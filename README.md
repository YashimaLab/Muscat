# Muscat
cubeファイルを利用したスクリーニングプログラム

## 1. 説明
Muscat.pyは、`EbiFry_v3.py` の解析データを基に結晶構造内における「格子間酸素」を調べるプログラムである。

スクリーニングとしての完成度は不十分なので、各自が改造土台として使用することを前提に、`Muscat.py`及び説明文書を作成した。  
同梱されているファイル名と簡単な説明は以下の通り。詳細は他mdファイルを参照
*   `README.md` (この文書。最初に読むこと)
*   `Muscat.py` (プログラム本体)
*   `cif_cube_extaraction.py`　(スクリーニング補助プログラム)
*   `Muscat_screening.md`　(Muscatを使用したスクリーニングについての説明)
*   `EbiFryAllData_Description.md` (スクリーニングに使用するデータセットの説明)
*   `CSV_Data_Structure_Description.md` (スクリーニングにcsvデータの説明)
*   `BVE_screening_Eb.csv` (csvでのEbiFry計算結果まとめ)
*   `ICSD_File_Map.csv` (各スクリーニング結果とデータ位置の対応表)

AIに聞いて運用することを想定しているので、このうち以下のものはAIに渡して解析させて良い。
*   `Muscat.py`
*   `cif_cube_extaraction.py`
*   `Muscat_screening.md`
*   `EbiFryAllData_Description.md`
*   `CSV_Data_Structure_Description.md`

## 2. 注意事項
CSV や計算データ、mdファイルなどを使用する際は、**share から自分のPCにコピーすること!** そのまま開いたり、読み込んだりしてはならない!

`Muscat_screening.md` の 「3. これまでの試験運用で得られた知見と今後の課題」に私の知見はまとめてあるので、ここは読むと改良の手掛かりになるはずである。

## 3. このスクリプトや計算結果を利用したものを論文にするとき
`Muscat.py`のスクリーニングで使用するデータは`EbiFry_v3.py`で出力されており、このプログラムは以下の外部プログラム要素を含んでいるため，それらの論文を引用するとともに，それらのソフトのライセンスも一読すること。  
学会発表でもどこかに記載しておくほうがよいと思われる。

softBV-command line version: [http\://www\.dmse.nus.edu.sg/asn/softBVCL.html](http://www.dmse.nus.edu.sg/asn/softBVCL.html)    
H. Chen, L.L. Wong, S.Adams; SoftBV \- a software tool for screening the materials genome of inorganic fast ion conductors. *Acta Crystallogr.* B 75 (2019), 18-33. [https\://doi.org/10.1107/S2052520618015718](https://doi.org/10.1107/S2052520618015718) (as the source of the code)  
H. Chen, S. Adams; Bond softness sensitive bond-valence parameters for crystal structure plausibility tests. *IUCrJ* 4 (2017) 614-625. [https\://doi.org/10.1107/S2052520618015718](https://doi.org/10.1107/S2052520618015718)  (as the source of the BV parameters)

Pymatgen [https\://pymatgen.org/index.html\#](https://pymatgen.org/index.html#)   
P. Ong, W. D. Richards, A. Jain, G. Hautier, M. Kocher, S. Cholia, D. Gunter, V. L. Chevrier, K. A. Persson and G. Ceder, Python Materials Genomics (pymatgen): A robust, open-source python library for materials analysis, *Comput. Mater. Sci.*, 2013, 68, 314–319.  
10.1016/j.commatsci.2012.10.028
