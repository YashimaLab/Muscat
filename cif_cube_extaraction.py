import os
import csv
import zipfile

# ================= ユーザー設定 =================
TARGET_ICSD_LIST = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20] 
BVE_CSV_PATH = "BVE_screening_Eb.csv"
MAP_CSV_PATH = "ICSD_File_Map.csv"
ARCHIVE_BASE_DIR = "EbiFryAllData"
# ================================================

def extract_cif_and_cube(icsd_list, bve_csv_path, map_csv_path, archive_base_dir, output_dir, log_file_path):
    """
    ICSD番号のリストに基づいてCIFとCubeファイルを抽出し、リネームして保存する。
    アーカイブの全解凍は行わず、必要なファイルのみを直接抽出する。
    """
    # 出力先ディレクトリの作成
    os.makedirs(output_dir, exist_ok=True)
    error_log = []

    # 1. BVE_screening_Eb.csv の読み込み (存在確認用)
    valid_icsd_ids = set()
    try:
        with open(bve_csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # ICSD_IDは整数/文字列型のため文字列として扱う
                valid_icsd_ids.add(str(row['ICSD_ID']).strip())
    except Exception as e:
        print(f"エラー: {bve_csv_path} の読み込みに失敗しました ({e})")
        return

    # 2. ICSD_File_Map.csv の読み込み (パス情報の取得)
    file_map = {}
    try:
        with open(map_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                file_map[str(row['ICSD_ID']).strip()] = {
                    'Zip_File': row['Zip_File'],
                    'CIF_Path': row['CIF_Path'],
                    'Cube_Path': row['Cube_Path'],
                    'Status': row['Status']
                }
    except Exception as e:
        print(f"エラー: {map_csv_path} の読み込みに失敗しました ({e})")
        return

    # 3. リストに基づきファイルの抽出・リネーム処理
    for icsd_id in icsd_list:
        icsd_id_str = str(icsd_id).strip()

        # スクリーニング結果(BVE_screening_Eb.csv)に存在しない場合
        if icsd_id_str not in valid_icsd_ids:
            error_log.append(f"ICSD_ID: {icsd_id_str} - エラー: BVE_screening_Eb.csvに存在しません。")
            continue

        # マップ情報(ICSD_File_Map.csv)に存在しない場合
        if icsd_id_str not in file_map:
            error_log.append(f"ICSD_ID: {icsd_id_str} - エラー: ICSD_File_Map.csvにパスのマッピング情報が存在しません。")
            continue

        map_info = file_map[icsd_id_str]
        
        # Missing CIF/Cube などのステータスチェック
        if "Missing CIF/Cube" in map_info['Status']:
            error_log.append(f"ICSD_ID: {icsd_id_str} - エラー: Statusが '{map_info['Status']}' のため処理をスキップしました。")
            continue

        zip_filepath = os.path.join(archive_base_dir, map_info['Zip_File'])

        # ZIPアーカイブ自体の存在確認
        if not os.path.exists(zip_filepath):
            error_log.append(f"ICSD_ID: {icsd_id_str} - エラー: 指定されたZIPアーカイブ ({zip_filepath}) が見つかりません。")
            continue

        # アーカイブ内のファイル抽出 (全解凍せず個別ファイルを取り出す)
        try:
            with zipfile.ZipFile(zip_filepath, 'r') as zf:
                # アーカイブ内のファイルリストを取得
                archive_files = zf.namelist()
                
                # --- CIFファイルの処理 ---
                cif_path = map_info['CIF_Path']
                if cif_path and cif_path in archive_files:
                    extracted_cif_data = zf.read(cif_path) # メモリ上に読み込み
                    output_cif_path = os.path.join(output_dir, f"{icsd_id_str}.cif")
                    with open(output_cif_path, 'wb') as out_f:
                        out_f.write(extracted_cif_data)
                else:
                    error_log.append(f"ICSD_ID: {icsd_id_str} - エラー: 目的のCIFファイルがアーカイブ内に存在しません。")

                # --- Cubeファイルの処理 ---
                cube_path = map_info['Cube_Path']
                if "Missing Cube" in map_info['Status']:
                     error_log.append(f"ICSD_ID: {icsd_id_str} - エラー: StatusがException.B等のため、Cubeファイルは存在しません。")
                elif cube_path and cube_path in archive_files:
                    extracted_cube_data = zf.read(cube_path) # メモリ上に読み込み
                    output_cube_path = os.path.join(output_dir, f"{icsd_id_str}.cube")
                    with open(output_cube_path, 'wb') as out_f:
                        out_f.write(extracted_cube_data)
                else:
                    error_log.append(f"ICSD_ID: {icsd_id_str} - エラー: 目的のCubeファイルがアーカイブ内に存在しません。")
                    
        except Exception as e:
             error_log.append(f"ICSD_ID: {icsd_id_str} - エラー: ZIP展開エラー ({e})")

    # 4. エラーログの出力
    with open(log_file_path, 'w', encoding='utf-8') as f:
        if error_log:
            f.write("\n".join(error_log))
            print(f"処理が完了しましたが、いくつかのエラーが発生しました。詳細は {log_file_path} を確認してください。")
        else:
            f.write("全てのエラーなしに正常に処理されました。")
            print("処理が正常に完了しました。")

# 実行例
if __name__ == "__main__":
    # 検索したいICSD番号のリスト
    TARGET_ICSD_LIST = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20] 

    extract_cif_and_cube(
        icsd_list = TARGET_ICSD_LIST,
        bve_csv_path = BVE_CSV_PATH,
        map_csv_path = MAP_CSV_PATH,
        archive_base_dir = ARCHIVE_BASE_DIR,
        output_dir = "output",
        log_file_path = "extraction_error_log.txt"
    )
