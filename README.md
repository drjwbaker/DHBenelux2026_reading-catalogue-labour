# What Catalogues Say About Their Own Making: data and code

Data and code for the analysis reported in "What Catalogues Say About Their Own Making: reading catalogue data as evidence of its production" (DH Benelux Journal, submitted 2026). The paper reads the catalogue of the National Library of Scotland's Moving Image Archive as evidence of the labour, resourcing, and institutional conditions that produced it.

## What is here

```
DHBenelux2026_reading-catalogue-labour/
├── README.md                  this file
├── DATASHEET.md               datasheet for the dataset as used (Alkemade et al. 2025 model)
├── LICENSE                    MIT (code)
├── LICENSE-DATA.md            CC0 1.0 (derived data and figures)
├── CITATION.cff               how to cite
├── code/                      analysis code
│   ├── pairwise_comparison_v5.ipynb     pairwise text similarity (MinHash–LSH + SequenceMatcher)
│   ├── community_analysis_v21.ipynb     similarity graph + Leiden communities; in-graph/isolate split
│   ├── isolate_analysis_v3.ipynb        the isolate population: length, shotlisting, timecoding, TF-IDF
│   ├── shotlist_structure_v2.ipynb      shotlist and timecode detection over descriptions
│   ├── figure_shotlist_by_decade_v1.py  regenerates Figure 1 (reproduces caption values exactly)
│   ├── community_utils.py / tfidf_utils.py / utils.py   shared functions
│   └── requirements.txt                 pinned dependencies
├── data-prep/                 split_records.py + notes: NLS source → per-record files
├── derived-data/              outputs the paper's numbers rest on (run-stamp note below), incl.
│   ├── features_…20260313-120649.tsv        per-record features, all 23,491 records
│   ├── pairwise_…20260313-120649.tsv.gz     scored candidate pairs (~112 MB uncompressed)
│   ├── communities_…20260417-152942.tsv     the 5,585 in-graph records + community assignments
│   ├── timecode_codebook_20260317.tsv       the timecode-detection codebook
│   └── centrality / TF-IDF comparison / gateway-node / bridge-scan outputs for the same run
└── figures/                   shotlist-by-decade_20260710.png (the paper's Figure 1)
```

## Source data (not included here)

The source dataset is the National Library of Scotland's **Moving Image Archive dataset, version 4** (23,491 records; Dublin Core and MARCXML), released by the NLS Data Foundry under **CC0 1.0** and citable at https://doi.org/10.34812/05y2-xv88. It is ~3.6 GB unpacked and is therefore not included in this repository: download it from the DOI, then run `data-prep/split_records.py` to produce the per-record files the notebooks here expect. See `DATASHEET.md` for composition and preprocessing details.

## Reproducing the analysis

```
pip install -r code/requirements.txt
# 1. download the NLS MIA v4 dataset (DOI above) and split it:
python data-prep/split_records.py
# 2. run, in order:
#    code/pairwise_comparison_v5.ipynb
#    code/community_analysis_v21.ipynb
#    code/isolate_analysis_v3.ipynb
#    code/shotlist_structure_v2.ipynb
# 3. regenerate Figure 1:
python code/figure_shotlist_by_decade_v1.py
```

The derived data are provided, so the paper's numbers can be checked without rerunning anything: the Table 2 split is `communities_…20260417-152942.tsv` against the 23,491 rows of `features_…20260313-120649.tsv`; Figure 1's values recompute from the features file alone.

## A note on file names and runs

Derived files carry the run timestamp of the analysis that produced them (`YYYYMMDD-HHMMSS`). The published analysis is the **20260417-152942** run for the similarity graph and communities, over features computed in the **20260313-120649** run. Boilerplate rights statements were stripped from descriptions before similarity measurement (see `DATASHEET.md`).

## Licence

Code is released under the MIT Licence (`LICENSE`). Derived data and figures are released under CC0 1.0 (`LICENSE-DATA.md`), matching the licence of the NLS source data; source-rights and attribution notes are in `DATASHEET.md` (Distribution and licence).

## Citation

See `CITATION.cff`. Please cite the paper and, where you use them, the specific dataset or code files.
