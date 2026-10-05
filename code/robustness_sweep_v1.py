"""robustness_sweep_v1.py — do the published communities survive other settings?

Written 5 October 2026. A standalone check on the communities reported in the paper
(code/community_analysis_v21.ipynb, published run 20260417-152942).

The published run builds a similarity graph from all record pairs with
SequenceMatcher ratio >= 0.65 and finds communities with Leiden (modularity, which
equals RBConfiguration at resolution 1.0; seed 42). This script rebuilds that graph at
several thresholds, re-runs Leiden at several resolutions, and compares each run with
the published partition:

  * AMI: adjusted mutual information between the run and the published partition,
    over records present in both (1.0 = identical).
  * retention: for each tracked community, the share of its published members that
    end up together in one community of the run (the one holding most of them).
    Members that leave the graph at a higher threshold count as lost.
  * jaccard: overlap between the published community and that run community. High
    retention with low Jaccard means the community merged into a larger one.

Before the sweep, the script checks that the published settings reproduce the
published partition exactly, and stops if they do not.

Inputs (released in derived-data/):
  * pairwise_individual_records_20260313-120649.tsv.gz   (all pairs with ratio >= 0.20)
  * communities_individual_records_20260417-152942.tsv   (the published partition)

Output:
  * derived-data/robustness-sweep_individual_records_<stamp>.tsv — one row per run.
  * printed tables: AMI by threshold x resolution; retention at resolution 1.0;
    lowest retention per community near the published settings and over the grid.

Usage:
    python3 robustness_sweep_v1.py
    python3 robustness_sweep_v1.py --repo /path/to/repo --out-dir /somewhere/else

Requires pandas, networkx, igraph, leidenalg, scikit-learn (see requirements.txt).
"""
import argparse
import datetime
import pathlib
import sys
from collections import Counter

import igraph as ig
import leidenalg
import networkx as nx
import pandas as pd
from sklearn.metrics import adjusted_mutual_info_score

PAIRWISE = "pairwise_individual_records_20260313-120649.tsv.gz"
COMMUNITIES = "communities_individual_records_20260417-152942.tsv"

# Settings of the published run.
PUBLISHED_THRESHOLD = 0.65
PUBLISHED_RESOLUTION = 1.0
SEED = 42

# Grid of settings to try.
THRESHOLDS = [0.55, 0.60, 0.65, 0.70, 0.75]
RESOLUTIONS = [0.5, 1.0, 2.0]

# Communities tracked: those of the record examples in the paper's Table 1
# (0, 2, 4, 7, 11, 17) plus 21 from the close-reading set.
FOCUS = [0, 2, 4, 7, 11, 17, 21]

STAMP = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")


def leiden_at(pairs, threshold, resolution):
    """Build the graph as the notebook does (NetworkX, then igraph in the same node
    and edge order) and run Leiden at the given resolution."""
    sub = pairs[pairs["sm_ratio"] >= threshold]
    g_nx = nx.from_pandas_edgelist(sub, source="base_id", target="compare_id",
                                   edge_attr="sm_ratio")
    edges = list(g_nx.edges(data="sm_ratio"))
    nodes = list(g_nx.nodes())
    idx = {n: i for i, n in enumerate(nodes)}
    g = ig.Graph(n=len(nodes), edges=[(idx[u], idx[v]) for u, v, _ in edges],
                 edge_attrs={"weight": [w for _, _, w in edges]})
    part = leidenalg.find_partition(g, leidenalg.RBConfigurationVertexPartition,
                                    weights="weight", resolution_parameter=resolution,
                                    seed=SEED)
    labels = {nodes[n]: cid for cid, comm in enumerate(part) for n in comm}
    return labels, len(part)


def compare(labels, published, members):
    shared = sorted(set(labels) & set(published))
    ami = adjusted_mutual_info_score([published[n] for n in shared],
                                     [labels[n] for n in shared])
    per = {}
    for c, mem in members.items():
        present = [n for n in mem if n in labels]
        if not present:
            per[c] = (0.0, 0.0)
            continue
        best, n_best = Counter(labels[n] for n in present).most_common(1)[0]
        best_set = {n for n, lab in labels.items() if lab == best}
        per[c] = (n_best / len(mem), len(mem & best_set) / len(mem | best_set))
    return ami, len(shared) / len(published), per


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=str(pathlib.Path(__file__).resolve().parent.parent),
                    help="repository root (default: the folder above code/)")
    ap.add_argument("--out-dir", default=None,
                    help="where to write the TSV (default: <repo>/derived-data)")
    args = ap.parse_args()

    data = pathlib.Path(args.repo) / "derived-data"
    out_dir = pathlib.Path(args.out_dir) if args.out_dir else data

    pairs = pd.read_csv(data / PAIRWISE, sep="\t",
                        usecols=["base_id", "compare_id", "sm_ratio"])
    pairs = pairs[pairs["sm_ratio"] >= min(THRESHOLDS)].reset_index(drop=True)
    pub = pd.read_csv(data / COMMUNITIES, sep="\t")
    published = dict(zip(pub["film_ref"], pub["community_id"]))
    members = {c: set(pub.loc[pub["community_id"] == c, "film_ref"]) for c in FOCUS}
    print(f"{len(pairs):,} pairs with ratio >= {min(THRESHOLDS)}; published partition: "
          f"{len(published):,} records in {pub['community_id'].nunique()} communities")

    # Reproduction check.
    labels, _ = leiden_at(pairs, PUBLISHED_THRESHOLD, PUBLISHED_RESOLUTION)
    ami, _, per = compare(labels, published, members)
    if ami < 0.999 or any(r < 0.999 for r, _ in per.values()):
        sys.exit(f"Published partition NOT reproduced (AMI {ami:.4f}). Check the input "
                 "files and package versions against requirements.txt; sweep not run.")
    print(f"Reproduction check passed: threshold {PUBLISHED_THRESHOLD}, resolution "
          f"{PUBLISHED_RESOLUTION} gives AMI {ami:.4f} with the published partition.\n")

    rows = []
    for t in THRESHOLDS:
        for r in RESOLUTIONS:
            labels, n_comm = leiden_at(pairs, t, r)
            ami, cov, per = compare(labels, published, members)
            row = {"threshold": t, "resolution": r, "n_records": len(labels),
                   "n_communities": n_comm, "share_of_published_in_graph": round(cov, 4),
                   "ami_vs_published": round(ami, 4)}
            for c, (ret, jac) in per.items():
                row[f"retention_c{c}"] = round(ret, 4)
                row[f"jaccard_c{c}"] = round(jac, 4)
            rows.append(row)
            print(f"threshold {t:.2f}  resolution {r:.1f}: {len(labels):>5,} records  "
                  f"{n_comm:>4} communities  AMI {ami:.3f}")
    df = pd.DataFrame(rows)

    out = out_dir / f"robustness-sweep_individual_records_{STAMP}.tsv"
    df.to_csv(out, sep="\t", index=False)

    pd.set_option("display.width", 160)
    print("\nAMI with the published partition (threshold x resolution):\n")
    print(df.pivot(index="threshold", columns="resolution", values="ami_vs_published").to_string())
    print("\nRetention at resolution 1.0:\n")
    r1 = df[df["resolution"] == 1.0].set_index("threshold")
    print(r1[[f"retention_c{c}" for c in FOCUS]]
          .rename(columns=lambda s: s.replace("retention_c", "community ")).to_string())
    near = df[((df["resolution"] == PUBLISHED_RESOLUTION) &
               ((df["threshold"] - PUBLISHED_THRESHOLD).abs() <= 0.051)) |
              (df["threshold"] == PUBLISHED_THRESHOLD)]
    print("\nLowest retention per community (nearby = thresholds 0.60-0.70 at resolution "
          "1.0, and resolutions 0.5-2.0 at 0.65):")
    print(f"{'community':>10} {'n':>5} {'nearby':>8} {'whole grid':>11}")
    for c in FOCUS:
        print(f"{c:>10} {len(members[c]):>5} {near[f'retention_c{c}'].min():>8.2f} "
              f"{df[f'retention_c{c}'].min():>11.2f}")
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
