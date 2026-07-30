#!/usr/bin/env python3
"""
split_records.py
----------------
Splits the NLS Moving Image Archive DC XML files into individual
record files, one per rdf:Description block, named by the dcterms:identifier
(filmRef) value.

Improved replacement for the csplit + tr + shuf pipeline in prep-code.md.

Output: individual .txt files in ./individual_records/
Each file contains the full rdf:Description block serialised as a single line
(no internal newlines), ready for pairwise comparison or sampling.

Usage:
    python3 split_records.py
    python3 split_records.py --output-dir /path/to/output
    python3 split_records.py --sample 500  # write a random 500-record sample too
"""

import argparse
import os
import random
import re
import shutil
import xml.etree.ElementTree as ET

# ── namespace map ──────────────────────────────────────────────────────────────
RDF_NS   = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
DCTERMS_NS = "http://purl.org/dc/terms/"
NS = {
    "rdf":     RDF_NS,
    "dcterms": DCTERMS_NS,
}

# Register so ET.tostring() uses the short prefixes
ET.register_namespace("rdf",     RDF_NS)
ET.register_namespace("dcterms", DCTERMS_NS)

# ── helpers ────────────────────────────────────────────────────────────────────

def get_film_id(desc: ET.Element) -> str | None:
    """Return the sanitised filmRef identifier, e.g. '0001' or 'UCS0214'."""
    for id_el in desc.findall("dcterms:identifier", NS):
        text = (id_el.text or "").strip()
        if text.startswith("(filmRef)"):
            return text[len("(filmRef)"):].strip()
    return None


def serialise_one_line(desc: ET.Element) -> str:
    """Serialise an rdf:Description element as a single whitespace-collapsed line."""
    raw = ET.tostring(desc, encoding="unicode")
    # collapse internal whitespace to single spaces
    return " ".join(raw.split())


# ── main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Split NLS MIA DC XML into individual record files.")
    parser.add_argument(
        "--data-dir",
        default=os.path.dirname(os.path.abspath(__file__)),
        help="Directory containing the 2025_mia_dc_*.xml files (default: script directory)"
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory for individual record files (default: <data-dir>/individual_records)"
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=None,
        help="If set, also write a random sample of this many records to <output-dir>/../sample_<N>/"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite output directory if it already exists"
    )
    args = parser.parse_args()

    data_dir   = args.data_dir
    output_dir = args.output_dir or os.path.join(data_dir, "individual_records")

    # ── prepare output directory ───────────────────────────────────────────────
    if os.path.exists(output_dir):
        if args.overwrite:
            shutil.rmtree(output_dir)
        else:
            print(f"Output directory already exists: {output_dir}")
            print("Use --overwrite to replace it.")
            return
    os.makedirs(output_dir)

    # ── process each XML file ──────────────────────────────────────────────────
    written  = 0
    skipped  = 0
    all_ids  = []   # keep track of written IDs for optional sampling

    for i in range(1, 5):
        xml_path = os.path.join(data_dir, f"2025_mia_dc_{i}.xml")
        if not os.path.exists(xml_path):
            print(f"  WARNING: {xml_path} not found, skipping.")
            continue

        print(f"Processing {os.path.basename(xml_path)} ...", end=" ", flush=True)
        tree = ET.parse(xml_path)
        root = tree.getroot()
        file_count = 0

        for desc in root.findall("rdf:Description", NS):
            film_id = get_film_id(desc)
            if film_id is None:
                skipped += 1
                continue

            content   = serialise_one_line(desc)
            out_path  = os.path.join(output_dir, f"{film_id}.txt")
            with open(out_path, "w", encoding="utf-8") as fh:
                fh.write(content)

            all_ids.append(film_id)
            written    += 1
            file_count += 1

        print(f"{file_count} records written.")

    print(f"\nTotal written : {written}")
    print(f"Total skipped : {skipped}")
    print(f"Output        : {output_dir}")

    # ── optional random sample ─────────────────────────────────────────────────
    if args.sample and args.sample < written:
        sample_dir = os.path.join(os.path.dirname(output_dir), f"sample_{args.sample}")
        os.makedirs(sample_dir, exist_ok=True)
        sampled_ids = random.sample(all_ids, args.sample)
        for film_id in sampled_ids:
            src = os.path.join(output_dir, f"{film_id}.txt")
            dst = os.path.join(sample_dir, f"{film_id}.txt")
            shutil.copy2(src, dst)
        # also write a combined base_data.txt for the notebook
        combined_path = os.path.join(sample_dir, "base_data.txt")
        with open(combined_path, "w", encoding="utf-8") as fh:
            for film_id in sampled_ids:
                src = os.path.join(output_dir, f"{film_id}.txt")
                with open(src, "r", encoding="utf-8") as src_fh:
                    fh.write(src_fh.read() + "\n")
        print(f"\nSample of {args.sample} records written to : {sample_dir}")
        print(f"Combined base_data.txt written to         : {combined_path}")


if __name__ == "__main__":
    main()
