# Datasheet — NLS Moving Image Archive catalogue data, as used

Following Alkemade, Candela, Claeyssens, et al., *Datasheets for Digital Cultural Heritage Datasets*, 7 July 2025, https://doi.org/10.5281/zenodo.15828222 this datasheet documents the dataset used in this analysis - the National Library of Scotland's published dataset - and preprocessing steps used. The authoritative documentation for the source dataset is the NLS's own readme, which can be found distributed with it.

## Motivation

Created to support the analysis in "What Catalogues Say About Their Own Making" (DH Benelux Journal, submitted 2026). This paper read part of an institutional catalogue as evidence of the labour and resourcing conditions under which its records were produced, via pairwise text similarity, community detection, and description-structure features (shotlisting, timecoding, description length).

## Composition

- Source: **Moving Image Archive dataset, version 4**, National Library of Scotland Data Foundry. 23,491 records describing the film and television holdings of Scotland's national collection of moving images, provided as 4 XML files in Dublin Core and 4 in MARCXML, with an NLS readme. Created 29–30 April 2025 per the NLS readme. DOI (current version): https://doi.org/10.34812/05y2-xv88.
- This analysis uses the **Dublin Core** files, split into per-record files by `data-prep/split_records.py`.
- Records fields include: identifier ("film reference"), title, date, genre tags, and one or more description fields. 17,782 records (75.7%) have a usable year of the material described (1890–2026): note that this year is a date of creation/publication for described material, not the date of cataloguing or accession. Decade-level figures produced for the paper are therefore proxies for the earliest possible cataloguing date.
- Descriptions range from twenty-word repeated stubs (the *Dè a-nis?* series: 584 near-identical records) to 150+ word shot-by-shot accounts with timecodes.

## Collection process

The source dataset is published by the NLS Data Foundry as a snapshot of the Moving Image Archive catalogue.

## Preprocessing / cleaning

Applied here, on top of the NLS release:

1. **Per-record splitting** (`data-prep/split_records.py`): the four Dublin Core XML files are split into one file per record.
2. **Boilerplate stripping at analysis time**: Data Foundry boilerplate statements (standard rights/provenance text repeated across records) are removed from descriptions before similarity measurement, to prevent spurious near-duplicate matches.
3. **Broadcaster-supplied text is retained**: a substantial number of television records carry broadcaster programme summaries ingested wholesale (many tagged e.g. "[Source - BBC Alba]"). These are part of the catalogue as published and are deliberately retained, and the paper reads them as evidence of cataloguing practice.
4. **Feature extraction** (`features_…tsv`): description word counts, shotlist and timecode detection (see `timecode_codebook_20260317.tsv`), genre tags, year.

## Personal and sensitive data

Catalogue records name film-makers, presenters, and credited contributors, and descriptions may name individuals appearing in footage. All content is as published by the NLS in an openly licensed dataset. No additional personal data are introduced, and no attempt is made to identify cataloguers, who are anonymous in the source data.

## Uses

Suited to: analysis of cataloguing practice and descriptive conventions; catalogue-data quality and provenance work; similarity and clustering method development on heterogeneous description text. Ill-suited to: treating description presence/absence as a measure of collection importance (the paper's own argument is that it measures resourcing); inferring cataloguing dates from material dates (see 'Composition' above); reading stub records such as those for *Dè a-nis?* as carelessness (the paper argues they trace constraint, not negligence).

## Distribution and licence

- Source data: **CC0 1.0** (per the NLS readme), from https://doi.org/10.34812/05y2-xv88 — not redistributed here (size), fetched at reproduction time.
- Derived data and figures in this repository: **CC0 1.0** (`LICENSE-DATA.md` carries the licence text). The underlying catalogue records are National Library of Scotland Data Foundry material, themselves CC0; this repository adds no further restriction. Attribution to the NLS as source of the underlying records, and citation of this repository and the accompanying paper (`CITATION.cff`), are appreciated though not legally required under CC0.
- Code (`code/` and `data-prep/`): **MIT** (`LICENSE`).

## Maintenance

Maintained by James Baker (ORCID 0000-0002-2682-6922) on a best-effort basis as part of the research this repository is based on. The NLS may issue new versions of the source dataset under the same DOI. This repository uses version 4 and the run stamps in `derived-data/`.

## Derived-data note (brief)

The published analysis: features and pairwise runs **20260313-120649**; similarity graph and Leiden communities run **20260417-152942** (5,585 in-graph records; 17,906 isolates; the *Dè a-nis?* community of 584). Figure 1 recomputes from the features file alone (`code/figure_shotlist_by_decade_v1.py`, verified against the published caption). The "roughly 1,300" broadcaster-supplied summaries figure recomputes from the features file plus the source tags in the NLS DC export (`code/broadcaster_summaries_v1.py`, which writes `derived-data/broadcaster-summaries_individual_records_20260922-131453.tsv` and asserts the reported count of 1,355 at the 50-word rule). Community detection is stochastic in tie-breaking; the community file is the published run.
