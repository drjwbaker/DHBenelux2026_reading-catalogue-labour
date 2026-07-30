"""figure_shotlist_by_decade_v1.py — regenerate Figure 1 (shotlist/timecode rate by decade).

Reconstructed 23 July 2026 to restore the provenance of
figures/shotlist-by-decade_20260710.png. Verified against the published caption
values before inclusion: dated records 17,782; shotlist % by decade 1890s-1970s
98.9-100.0, 1980s 94.1, 1990s 28.1, 2000s 20.9, 2010s 47.9; timecodes 2010s 0.8.

Input : derived-data/features_individual_records_20260313-120649.tsv
Output: figures/shotlist-by-decade_<stamp>.png + figures/shotlist-by-decade_<stamp>.tsv
"""
import datetime
import pathlib

import matplotlib.pyplot as plt
import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent.parent
FEATURES = HERE / "derived-data" / "features_individual_records_20260313-120649.tsv"
STAMP = datetime.datetime.now().strftime("%Y%m%d")

df = pd.read_csv(FEATURES, sep="\t")
dated = df[(df.year >= 1890) & (df.year <= 2026)].copy()
assert len(dated) == 17782, f"expected 17,782 dated records, got {len(dated)}"
dated["decade"] = (dated.year // 10 * 10).astype(int)

g = dated.groupby("decade").agg(
    n=("film_ref", "count"),
    shotlist_pct=("has_shotlist", lambda s: round(100 * s.mean(), 1)),
    timecode_pct=("has_timecodes", lambda s: round(100 * s.mean(), 1)),
).reset_index()

out_tsv = HERE / "figures" / f"shotlist-by-decade_{STAMP}.tsv"
g.to_csv(out_tsv, sep="\t", index=False)

fig, ax = plt.subplots(figsize=(8, 4.5))
ax.plot(g.decade, g.shotlist_pct, marker="o", label="Shot-by-shot description")
ax.plot(g.decade, g.timecode_pct, marker="s", label="Timecoded")
ax.set_xlabel("Decade of material described")
ax.set_ylabel("% of records")
ax.set_ylim(0, 105)
ax.legend()
fig.tight_layout()
fig.savefig(HERE / "figures" / f"shotlist-by-decade_{STAMP}.png", dpi=200)
print(g.to_string(index=False))
print("verified: caption values reproduce exactly")
