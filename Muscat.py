import glob
import numpy as np
import os
import pandas as pd
from concurrent.futures import ProcessPoolExecutor
from pymatgen.core import Structure
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from scipy.interpolate import RegularGridInterpolator
from scipy.ndimage import distance_transform_edt
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components
from skimage.feature import peak_local_max

import warnings
# 警告の非表示設定
warnings.filterwarnings('ignore', category=UserWarning, module='pymatgen')

# ================= ユーザー設定 =================
INPUT_DIR = "target"                        # 解析対象のCIF・cubeファイルの保存ディレクトリ
OUTPUT_CIF_DIR = "output"                   # 解析結果のCIFの保存用ディレクトリ
OUTPUT_CSV = "Muscat_screening_result.csv"  # 解析結果のCSVファイル

PERCENTILE_THRESHOLD = 10   # 下位何%を「低い」とみなすか(%)
MIN_OXYGEN_DIST = 1.2       # 酸素原子から離すべき距離 (Å)
RESAMPLE_RESOLUTION = 0.1   # リサンプリング解像度 (Å)
PADDING_ANGSTROM = 2.0      # 境界での切断を防ぐための「のりしろ」 (Å)
GROUP_RANGE = 0.5           # 同じサイトとみなす原子位置の距離 (Å)
# ================================================
BOHR_TO_ANGSTROM = 0.529177

def parse_cube_file(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()
    tokens2 = lines[2].split()
    natoms = int(tokens2[0])
    origin = np.array([float(x) for x in tokens2[1:4]]) * BOHR_TO_ANGSTROM
    axis_params = np.array([[float(x) for x in lines[i].split()] for i in range(3, 6)])
    grid_shape = axis_params[:, 0].astype(int)
    voxel_vectors = axis_params[:, 1:4] * BOHR_TO_ANGSTROM 
    data_1d = np.fromstring(" ".join(lines[6+natoms:]), sep=' ')
    data_3d = data_1d.reshape(grid_shape)
    return origin, voxel_vectors, data_3d, grid_shape

def group_interstitial_sites(sites, cif_path):
    """
    格子間サイトを距離および対称操作（空間群）に基づいてグルーピングし、平均化する。
    """
    if not sites:
        return []

    # 1. CIFから構造と対称操作を取得
    structure = Structure.from_file(cif_path)
    lattice = structure.lattice
    # 空間群の解析（精度は0.1A程度に設定）
    finder = SpacegroupAnalyzer(structure, symprec=0.1)
    symm_ops = finder.get_space_group_operations()
    
    num_sites = len(sites)
    fcoords = np.array([[s['a_frac'], s['b_frac'], s['c_frac']] for s in sites])
    
    # 2. 対称性を考慮した隣接行列の作成
    # adj[i, j] = True ならば、サイトiとjは対称操作によって重なる（等価である）
    adj_matrix = np.zeros((num_sites, num_sites), dtype=bool)

    for i in range(num_sites):
        adj_matrix[i, i] = True # 自己結合
        for j in range(i + 1, num_sites):
            is_equivalent = False
            
            # サイトiに対して全対称操作を適用し、サイトjと重なるかチェック
            for op in symm_ops:
                # 対称操作を適用
                transformed_fcoord = op.operate(fcoords[i])
                # PBCを考慮した距離を計算
                dist, _ = lattice.get_distance_and_image(transformed_fcoord, fcoords[j])
                
                if dist <= GROUP_RANGE:
                    is_equivalent = True
                    break
            
            if is_equivalent:
                adj_matrix[i, j] = adj_matrix[j, i] = True

    # 3. 連結成分の抽出（グルーピング）
    n_components, labels = connected_components(csgraph=csr_matrix(adj_matrix), directed=False)

    grouped_results = []
    filename = sites[0]['Filename']

    # 4. 各グループごとに代表値を算出
    for cluster_id in range(n_components):
        indices = np.where(labels == cluster_id)[0]
        cluster_members = [sites[i] for i in indices]
        
        # --- PBCを考慮した座標の平均化 ---
        # 最初のメンバーを基準点にする
        ref_fcoord = fcoords[indices[0]]
        all_aligned_fcoords = []
        
        for idx in indices:
            # 対称操作を考慮して「最も基準点に近い像」を探す
            best_dist = float('inf')
            best_pos = None
            
            for op in symm_ops:
                transformed = op.operate(fcoords[idx])
                # 基準点に最も近い格子像(image)を取得
                dist, image = lattice.get_distance_and_image(ref_fcoord, transformed)
                actual_pos = transformed + image
                
                if dist < best_dist:
                    best_dist = dist
                    best_pos = actual_pos
            
            all_aligned_fcoords.append(best_pos)
        
        # 重心を計算
        mean_fcoord = np.mean(all_aligned_fcoords, axis=0) % 1.0
        
        # 物理量の平均（または最適値）
        # 半径やポテンシャルはグループ内の最大/最小をとるのも一つの手ですが、ここでは平均とします
        mean_radius = np.mean([s['Max_Inscribed_Radius_A'] for s in cluster_members])
        mean_pot = np.mean([s['Min_Potential'] for s in cluster_members])
        mean_dist_o = np.mean([s['Dist_to_O'] for s in cluster_members])

        grouped_results.append({
            'Filename': filename,
            'a_frac': mean_fcoord[0],
            'b_frac': mean_fcoord[1],
            'c_frac': mean_fcoord[2],
            'Max_Inscribed_Radius_A': mean_radius,
            'Min_Potential': mean_pot,
            'Dist_to_O': mean_dist_o,
            'Multiplicity': len(indices) # 何個のサイトが統合されたか（参考用）
        })

    return grouped_results

def save_raw_sites_to_cif(sites, cif_path, suffix="_raw_candidates.cif"):
    """
    集約前の全候補サイトをHe原子として元の構造に追加し、デバッグ用のCIFとして保存する。
    """
    if not sites:
        return

    try:
        # 元の構造を読み込む
        structure = Structure.from_file(cif_path)
        
        # 候補サイトをHe(ヘリウム)として追加
        for site in sites:
            # pymatgenのappendはデフォルトがデカルト座標(True)のため、
            # 分数座標を渡す場合は coords_are_cartesian=False を指定します。
            structure.append(
                "He", 
                [site['a_frac'], site['b_frac'], site['c_frac']], 
                coords_are_cartesian=False
            )

        # 出力パスの作成 (例: original.cif -> original_raw_candidates.cif)
        base_name = os.path.basename(cif_path)
        name_without_ext = os.path.splitext(base_name)[0]
        output_path = os.path.join(OUTPUT_CIF_DIR, name_without_ext + suffix)
        structure.to(filename=output_path, fmt="cif")
        print(f"  Debug: Raw candidate sites (He) saved to {output_path}")
        
    except Exception as e:
        import traceback
        traceback.print_exc() # 詳細なエラー内容を確認するために追加
        print(f"  Warning: Could not save debug CIF: {e}")

def process_single_cube(filepath):
    filename = os.path.basename(filepath)
    cif_path = os.path.splitext(filepath)[0] + ".cif"
    results = []
    try:
        structure = Structure.from_file(cif_path)
        oxygen_frac_list = [
            site.frac_coords for site in structure 
            if any(el.symbol == "O" for el in site.species.elements)
        ]

        if not oxygen_frac_list:
            raise ValueError("構造内に酸素原子が見つかりませんでした。")
        lattice = structure.lattice

        origin, voxel_vectors, data_3d, grid_shape = parse_cube_file(filepath)

        # 1. ユニットセル行列 M (行ベクトル形式)
        M = voxel_vectors * grid_shape[:, np.newaxis]
        A, B, C = M[0], M[1], M[2]

        # A,B,Cから直交基底ベクトルex,ey,ezを作成(Gram-Schmidt)し、その長さをLx,Ly,Lzとして計算
        Lx = np.linalg.norm(A)
        ex = A / Lx
        ez = np.cross(A, B) / np.linalg.norm(np.cross(A, B))
        ey = np.cross(ez, ex)
        Ly = np.dot(B, ey)
        Lz = np.dot(C, ez)
        
        # 直交基底行列 (行が基底ベクトル)
        E = np.vstack([ex, ey, ez])

        # 3. リサンプリング範囲の設定 (のりしろ追加)
        d = PADDING_ANGSTROM
        xi = np.arange(-d, Lx + d, RESAMPLE_RESOLUTION)
        yi = np.arange(-d, Ly + d, RESAMPLE_RESOLUTION)
        zi = np.arange(-d, Lz + d, RESAMPLE_RESOLUTION)
        gx, gy, gz = np.meshgrid(xi, yi, zi, indexing='ij')
        
        # 4. 座標変換行列 T (Local Cart -> Global Index)
        # index = (P_local @ E) @ inv(M) @ diag(grid_shape)
        inv_M = np.linalg.inv(M)
        T = E @ inv_M @ np.diag(grid_shape)
        
        cart_coords_local = np.stack([gx.ravel(), gy.ravel(), gz.ravel()], axis=1)
        grid_indices = np.dot(cart_coords_local, T) % grid_shape

        # 直方体のグリッドの各地点におけるポテンシャルを再計算
        nodes = [np.arange(n + 1) for n in grid_shape]
        data_padded = np.pad(data_3d, ((0, 1), (0, 1), (0, 1)), mode='wrap')
        interpolator = RegularGridInterpolator(nodes, data_padded, method='linear')
        resampled_data = interpolator(grid_indices).reshape(gx.shape)

        # 内接球の半径の計算
        threshold = np.percentile(resampled_data, PERCENTILE_THRESHOLD)
        print(threshold)
        low_pot_mask = resampled_data <= threshold
        dt = distance_transform_edt(low_pot_mask, sampling=RESAMPLE_RESOLUTION)

        # 近すぎるピーク同士の重複除去
        peak_indices = peak_local_max(dt, min_distance=int(0.5/RESAMPLE_RESOLUTION))

        for idx in peak_indices:
            s, t, u = xi[idx[0]], yi[idx[1]], zi[idx[2]]
            
            # 元の 1 ユニットセル範囲 [0, L) に収まっているものだけを採用 (重複排除)
            if not (0 <= s < Lx and 0 <= t < Ly and 0 <= u < Lz):
                continue
            
            radius = dt[tuple(idx)]
            if radius < RESAMPLE_RESOLUTION: continue

            # 分数座標 (a, b, c) の計算
            frac_coords = np.dot(np.array([s, t, u]), E @ inv_M) % 1.0

            dist_to_O = float('inf')
            for o_fcoords in oxygen_frac_list:
                # 座標(数値配列)同士を渡す
                dist, _ = lattice.get_distance_and_image(frac_coords, o_fcoords)
                
                if dist < dist_to_O:
                    dist_to_O = dist
        
            if dist_to_O >= MIN_OXYGEN_DIST:
                results.append({
                    'Filename': filename,
                    'a_frac': frac_coords[0], 'b_frac': frac_coords[1], 'c_frac': frac_coords[2],
                    'Max_Inscribed_Radius_A': radius,
                    'Min_Potential': resampled_data[tuple(idx)],
                    'Dist_to_O': dist_to_O
                })

        final_grouped_results = group_interstitial_sites(results, cif_path)

        for res in final_grouped_results:
            # data_3d 全体のうち、このサイトのMin_Potential以下の値を持つ割合を計算する
            percentile = np.mean(data_3d <= res['Min_Potential'])
            res['Potential_Percentile'] = percentile

        save_raw_sites_to_cif(results, cif_path)
        save_raw_sites_to_cif(final_grouped_results, cif_path, "_cleaned_candidates.cif")
    except Exception as e:
        print(f"Error in {filename}: {e}")
    return final_grouped_results

def main():
    os.makedirs(OUTPUT_CIF_DIR, exist_ok=True)
    file_list = glob.glob(os.path.join(INPUT_DIR, "*.cube"))
    print(f"合計 {len(file_list)} 個のファイルを処理します...")

    all_results = []
    with ProcessPoolExecutor() as executor:
        for batch in executor.map(process_single_cube, file_list):
            all_results.extend(batch)
    if all_results:
        df = pd.DataFrame(all_results)
        cols = ['Filename', 'a_frac', 'b_frac', 'c_frac', 'Max_Inscribed_Radius_A', 'Min_Potential', 'Potential_Percentile', 'Dist_to_O','Multiplicity']
        df[cols].sort_values(['Filename', 'Min_Potential']).to_csv(OUTPUT_CSV, index=False)
        print(f"完了！ {len(all_results)} 個の格子間サイト候補を特定しました。")
    else:
        print("サイトが見つかりませんでした。")

if __name__ == "__main__":
    main()
