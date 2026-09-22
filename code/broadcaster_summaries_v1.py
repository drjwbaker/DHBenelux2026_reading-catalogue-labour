"""broadcaster_summaries_v1.py — reproduce the "roughly 1,300" broadcaster-supplied summaries count.

Written 22 September 2026. Reproduces the figure reported in the paper: among the
lengthier catalogue entries, those that are in fact broadcaster-supplied programme
summaries ingested wholesale from television listings, rather than cataloguer-written
description.

Definition (a record is a broadcaster-supplied summary if ALL of):
  * its description carries an explicit listings source tag, "[Source - ...]"
    (dominant sources: BBC Alba, Radio Times);
  * desc_word_count >= 50 (long enough to read as substantial description); and
  * has_shotlist is False (a shot-by-shot account is the signature of cataloguer
    labour, so its absence separates ingested copy from skilled description).
Because only records the Library itself marked as sourced are caught, the count is a
lower bound on ingested listings copy.

Inputs:
  * derived-data/features_individual_records_20260313-120649.tsv  (desc_word_count,
    has_shotlist) — reused from the released feature extraction.
  * the NLS Moving Image Archive DC XML export (National Library of Scotland, 2024,
    https://doi.org/10.34812/05y2-xv88), the same source split_records.py consumes;
    the "[Source - ...]" tag lives in the raw dcterms:description fields, which are
    not carried into the features file. Place the export's 2025_mia_dc_*.xml files
    in the repository root, or pass --xml-dir.

Output:
  * derived-data/broadcaster-summaries_individual_records_<stamp>.tsv — one row per
    record with has_source_tag, source_name, desc_word_count, has_shotlist and the
    is_broadcaster_summary flag.
  * prints the count at the 50-word rule (reported in the paper) and, for context,
    at 40 and 100 words.

Verified 22 Sep 2026 against the released features file: 1,355 records at the 50-word
rule (the paper's "roughly 1,300"); 4,084 records carry a source tag in total.

Usage:
    python3 broadcaster_summaries_v1.py
    python3 broadcaster_summaries_v1.py --xml-dir /path/to/nls-export
"""
import argparse
import csv
import datetime
import glob
import pathlib
import xml.etree.ElementTree as ET

RDF_NS = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
DESC = f"{{{RDF_NS}}}Description"

HERE = pathlib.Path(__file__).resolve().parent.parent
FEATURES = HERE / "derived-data" / "features_individual_records_20260313-120649.tsv"
STAMP = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

# candidate locations for the NLS DC XML export (per split_records.py / Data Foundry DOI)
XML_GLOBS = [
    "2025_mia_dc_*.xml",
    "data/2025_mia_dc_*.xml",
    "../data/nls-moving-image-archive-2025/2025_mia_dc_*.xml",
]


def find_xml(xml_dir=None):
    if xml_dir:
        files = sorted(glob.glob(str(pathlib.Path(xml_dir) / "2025_mia_dc_*.xml")))
        if files:
            return files
    for g in XML_GLOBS:
        files = sorted(glob.glob(str(HERE / g))) or sorted(glob.glob(g))
        if files:
            return files
    raise FileNotFoundError(
        "NLS DC XML export not found. Download the Moving Image Archive export "
        "(https://doi.org/10.34812/05y2-xv88), place 2025_mia_dc_*.xml in the repo "
        "root (as split_records.py expects), or pass --xml-dir."
    )


def source_tags(xml_files):
    """Map (filmRef) -> (has_source_tag, source_name) from the raw descriptions."""
    out = {}
    for fn in xml_files:
        root = ET.parse(fn).getroot()
        for d in root.iter(DESC):
            ident, descs = None, []
            for ch in d:
                tag = ch.tag.split("}")[1]
                text = ch.text or ""
                if tag == "identifier" and text.strip().startswith("(filmRef)"):
                    ident = text.strip()
                elif tag == "description":
                    descs.append(text)
            if ident:
                joined = " ".join(descs)
                name = ""
                i = joined.find("[Source")
                if i != -1:
                    j = joined.find("]", i)
                    frag = joined[i:j + 1] if j != -1 else joined[i:i + 40]
                    name = frag.split("-", 1)[-1].strip(" ]") if "-" in frag else ""
                out[ident] = ("[Source" in joined, name)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--xml-dir", default=None)
    args = ap.parse_args()

    feats = {}
    with open(FEATURES) as f:
        for r in csv.DictReader(f, delimiter="\t"):
            feats[r["film_ref"]] = r

    tags = source_tags(find_xml(args.xml_dir))

    rows, counts = [], {40: 0, 50: 0, 100: 0}
    for fr, r in feats.items():
        has_src, name = tags.get(fr, (False, ""))
        try:
            wc = int(r["desc_word_count"])
        except (KeyError, ValueError):
            wc = 0
        shot = r.get("has_shotlist", "") == "True"
        is_bs = has_src and wc >= 50 and not shot
        for thr in counts:
            if has_src and wc >= thr and not shot:
                counts[thr] += 1
        rows.append({
            "film_ref": fr,
            "has_source_tag": has_src,
            "source_name": name,
            "desc_word_count": wc,
            "has_shotlist": shot,
            "is_broadcaster_summary": is_bs,
        })

    out_tsv = HERE / "derived-data" / f"broadcaster-summaries_individual_records_{STAMP}.tsv"
    with open(out_tsv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter="\t")
        w.writeheader()
        w.writerows(rows)

    total_src = sum(1 for r in rows if r["has_source_tag"])
    print(f"records with a source tag (any length): {total_src}")
    print(f"broadcaster-supplied summaries, >=40 words, no shotlist: {counts[40]}")
    print(f"broadcaster-supplied summaries, >=50 words, no shotlist: {counts[50]}  <- reported as 'roughly 1,300'")
    print(f"broadcaster-supplied summaries, >=100 words, no shotlist: {counts[100]}")
    print(f"written: {out_tsv.relative_to(HERE)}")
    assert counts[50] == 1355, f"expected 1,355 at the 50-word rule, got {counts[50]}"
    print("verified: reported count reproduces exactly")


if __name__ == "__main__":
    main()
