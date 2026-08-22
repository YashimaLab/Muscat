# ディレクトリ EbiFryAllData のデータ概要

## 1. 説明
本mdファイルはEbiFry_v3.pyの計算の過程で出力されたアーカイブを解析に使用するため、その内容をまとめたものである。人やAIが読んで解析処理の手助けとなるように作成した。

## 2.1 データ構造
ディレクトリ EbiFryAllData 直下に各計算処理のアーカイブが存在する。

*   58個のアーカイブが存在する
*   各アーカイブはデータ処理スクリプト(`EbiFry_v3.py`)を用いた結晶構造データ等(.cif)のバッチ処理結果セットである。
*   アーカイブ形式はZIP64の`.zip`

各ZIPファイルを展開した際のディレクトリおよびファイル構造は以下の通りである。

```text
[ZIP_Name]/
 ├── target_X/                                 # [Input] (※ Xは任意の文字列)
 │    ├── [FileName_1].cif                     # 処理対象の初期データ
 │    ├── [FileName_2].cif
 │    └── ... (多数のcifファイル)
 │
 ├── cal_dir/                                  # [Output/Intermediate]
 │    ├── 00000000/                            # 8桁の連番ディレクトリ
 │    │    ├── BVPA_events.txt
 │    │    ├── BVPA_gui.csv                    # ※ Exception.A(2.2参照)の対象
 │    │    ├── BVPA_rp.csv                     # ※ Exception.A(2.2参照)の対象
 │    │    ├── YourCustomFileName_CollCode[ICSD_ID]_refined_CIF.cif
 │    │    ├── YourCustomFileName_CollCode[ICSD_ID]_refined_CIF.cif.cube   # ※ Exception.B(2.2参照)の対象
 │    │    └── YourCustomFileName_CollCode[ICSD_ID]_refined_JSON.json
 │    ├── 00000001/
 │    │    └── ... (00000000と同構造のファイル群)
 │    └── ... (以降、連番で続く)
 │
 ├── output_dir/                               # [Output/Final]
 │    ├── result.csv                           # 最終集計結果 (※ あるいはXを正の整数として、result_[X].csv となっている)
 │    └── result_initial.csv                   # 初期状態の集計結果　(※ あるいはXを正の整数として、result_initial_[X].csv となっている)
 │
 ├── EbiFry_v3.py                              # [Processor] 処理実行スクリプト
 └── time.txt                                  # [Log] 処理時間ログファイル

 ```

> **【解析時の注意点】**
> *   ZIP内部のパス構造は、ルートに**ZIPアーカイブ名と同名のフォルダ**が存在する（例: `1.zip` 内のファイルパスは `1/output_dir/result_1.csv` や `1/cal_dir/00000000/...` となる）。
> *   EbiFryAllData全体は圧縮状態で 約240 GiB 、 全展開時で推定 約1.1 TiB あるので、メモリやストレージへの全展開を行うプログラムを作成するのは非推奨。

## 2.2. `cal_dir/` の例外パターン
cal_dir 下の各連番ディレクトリ内のファイル構成は基本6ファイルだが、以下の例外が存在する。
*   Exception.A (Missing CSVs)
    *   状態: BVPA_gui.csv および BVPA_rp.csv が出力されていない。
    *   説明: 活性化障壁の計算中、タイムアウト等で障壁計算が行われない場合に発生する。
*   Exception.B (Assigned CIF vs Cube)
    *   状態: 通常出力される .cube ファイルが存在しない。
    *   説明: cubeファイルの生成中、タイムアウト等で処理が失敗した場合に発生する。
    *   ファイル名末尾が _assigned.cif となる以下のファイルが代わりに出力されている
        *   YourCustomFileName_CollCode[ICSD_ID]_refined_CIF_assigned.cif


## 3. 各ファイルの役割と内容
ここではファイルがどのようなデータを持っているかをまとめる。

### 3.1. Data Processing Script
*   **`EbiFry_v3.py`**
    *   **役割**: CIFファイルを入力とし、前処理、スクリーニング、および外部プログラム (`softBV.exe`, `softpath.exe`) を用いたエネルギー障壁 (Eb) 計算を自動で行うスクリプト。
    *   **データ内容**: 実際に実行されたプログラムが記述されている。

### 3.2. Logging and Processing Output
*   **`time.txt`**
    *   **役割**: スクリプト全体の処理開始と終了時間を記録するログファイル。
    *   **データ内容**: 実行時のシステム日時（`start time: ...`, `end time: ...`）。

### 3.3. Generated Configuration and Formatted Files (`cal_dir/`)
`cal_dir/` 以下の各連番ディレクトリに生成される、フォーマットされたファイルとデータパース用ファイル。softBVのexeファイルが出力した「BVPA_～」ファイルについては詳細が分からないため省略

*   **`YourCustomFileName_CollCode[ICSD_ID]_refined_JSON.json`**
    *   **役割**: 元のCIFファイルから解析・抽出された結晶構造情報を、JSON形式で保持する中間ファイル。
    *   **データ内容**: 空間群名、原子のフラクショナル座標、各格子定数、構成原子などの各種CIF情報が辞書型で整理されたもの。
*   **`YourCustomFileName_CollCode[ICSD_ID]_refined_CIF.cif`**
    *   **役割**: 元のCIFデータを元に、スクリプト（および外部プログラム）が処理しやすい形にフォーマット・整理されたクリーンなCIFファイル。
    *   **データ内容**: JSONから抽出された、基本のセル情報、空間群、対称操作、および原子サイトの座標リスト。
*   **`YourCustomFileName_CollCode[ICSD_ID]_refined_CIF.cif.cube`**
    *   **役割**: CIFデータから計算された酸化物イオンの各地点におけるポテンシャルを格納するcubeファイル。
    *   **データ内容**: 結合原子価法（Bond Valence Method）に基づく、空間の各グリッド地点における酸化物イオンのポテンシャル計算結果（3次元配列データ）。ファイルヘッダには、系の原子数、原点座標（Bohr単位）、および3軸方向のボクセルベクトル（グリッド間隔）とグリッド数が格納されている
*   **`BVPA_gui.csv`**
    *   **役割**: 外部プログラムによるエネルギー障壁 (Eb) 計算の結果が出力されるファイル。スクリプトが結果を収集するための読み取りソースとなる。
    *   **データ内容**: 次元 (1D, 2D, 3D) ごとのエネルギー障壁値（eV）のリスト。

### 3.4. Aggregated Output Files (`output_dir/`)
全データの処理結果を集約したCSVファイル。

*   **`result_initial.csv` (または `result_initial_X.csv`)**
    *   **役割**: 計算開始前（スクリーニング前）に、全対象CIFファイルの基本情報をまとめた一覧リスト。
    *   **データ内容**:
        *   `dir_name`: 割り当てられた連番ディレクトリ名（例: 00000000）
        *   `file_name`: 元のCIFファイル名
        *   `formula_sum`: 化学式（全体）
        *   `formula_structural`: 構造化学式
        *   `name_structure_type`: 構造タイプ名
        *   `ICSD_ID`: ICSDデータベースコード
        *   `space_group_name`: 空間群名
        *   `space_group_IT_number`: 空間群のIT番号
*   **`result.csv` (または `result_X.csv`)**
    *   **役割**: スクリーニング結果と、Eb計算に成功したファイルについてはそのエネルギー障壁値を記録した最終集計ファイル。
    *   **データ内容**:
        *   `dir_name`: 割り当てられた連番ディレクトリ名
        *   `file_name`: 処理したCIFファイル名
        *   `Eb_1D`: 1次元エネルギー障壁値 (eV)
        *   `Eb_2D`: 2次元エネルギー障壁値 (eV)
        *   `Eb_3D`: 3次元エネルギー障壁値 (eV)
        *   `note`: 特記事項。スクリーニングでの除外理由や計算エラーログが記録される。


## 4. `result.csv` における`note`の内容
計算処理の過程でエラーが起きた場合`note`の項にその理由が記述されているため、それぞれが指す内容を示す
*   strange CIF file (ex. too big occupancy)
    *   **内容** : CIFファイルのパース（読み込み）時にエラーが発生した
    *   **発生条件** :異常な占有率（許容値1.005をオーバーしている等）が設定されているなど、構造の解析自体に失敗した。

*   too big structure ([体積] A^3)
    *   **内容** : 単位格子が大きすぎる
    *   **発生条件** :結晶の単位格子体積がスクリーニングの上限値（MAX_STRUCTURE_VOLUME に設定された 2000 A^3）を超えていた。

*   containing banned atomic group (center:[中心原子のシンボル])
    *   **内容** : 指定のオキソ酸が結晶構造内に含まれていた
    *   **発生条件** :除外対象リスト（C, N, P, S, Cl, Br, I）に含まれる原子に酸素が最近接原子として存在し、その影響で活性化障壁がうまく計算できないと判断し計算対象から外した。

*   too long calculation time
    *   **内容** : EbiFry_v3.pyでの計算時間が長すぎた
    *   **発生条件** :外部プログラムの計算時間が制限時間（TIME_LIMIT に設定された 3600秒）を超過し、重すぎる計算と判断されてタイムアウトによる強制終了が行われた。

*   no BVPA_gui.csv (ex. too big occupancy)
    *   **内容** : 活性化障壁を求めるための`BVPA_gui.csv`が存在しなかった
    *   **発生条件** :外部プログラムの実行自体は終了したものの、結果を読み取るためのファイル（BVPA_gui.csv）が生成されなかった、あるいはファイル内に期待されるエネルギー障壁(Eb)の値が見つからなかった。
