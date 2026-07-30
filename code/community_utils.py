"""
community_utils.py — shared community detection and comparison utilities.

Used by:
  structural_similarity_v3.ipynb — Batches D and F (masked and skeleton graphs)
  shotlist_structure_v2.ipynb    — Batch D (shotlist-masked graph)

Functions
---------
run_leiden(G, edge_attr, outpath, label='', resolution=1.0, seed=42)
    Run Leiden (or fall back to Louvain) on a NetworkX graph; save TSV.

compare_partitions(orig_partition, new_partition, label='', top_n=15)
    Compute NMI and per-community stability between two partitions.
"""

import os

import pandas as pd
from collections import Counter
from sklearn.metrics import normalized_mutual_info_score


def run_leiden(G, edge_attr, outpath, label='', resolution=1.0, seed=42):
    """
    Run Leiden community detection on a NetworkX graph.

    Falls back to python-louvain if leidenalg/igraph are not installed.
    Prints community count and modularity Q, then saves the partition to a TSV.

    Parameters
    ----------
    G          : networkx.Graph — must have edge attribute `edge_attr`
    edge_attr  : str — name of the edge weight attribute
    outpath    : str — path to write the communities TSV (film_ref, community_id)
    label      : str — short label for print messages, e.g. 'masked', 'skeleton'
    resolution : float — resolution parameter for Louvain fallback
    seed       : int — random seed for reproducibility

    Returns
    -------
    partition : dict  { film_ref: community_id (int) }
    """
    tag = f'({label})' if label else ''

    try:
        import leidenalg
        import igraph as ig

        _adj  = [(u, v, d[edge_attr]) for u, v, d in G.edges(data=True)]
        _ig   = ig.Graph.TupleList(_adj, weights=True)
        _part = leidenalg.find_partition(
            _ig, leidenalg.ModularityVertexPartition,
            weights='weight', n_iterations=-1, seed=seed
        )
        partition = {
            _ig.vs[i]['name']: _part.membership[i]
            for i in range(_ig.vcount())
        }
        print(f'Leiden {tag}: {len(set(partition.values()))} communities')
        print(f'Modularity Q: {_part.modularity:.4f}')

    except ImportError:
        try:
            import community as community_louvain
        except ImportError:
            import subprocess as _sp, sys as _sys
            print('leidenalg not found; installing python-louvain for Louvain fallback...')
            result = _sp.run(
                [_sys.executable, '-m', 'pip', 'install', 'python-louvain', '-q'],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                raise RuntimeError(
                    'Could not install python-louvain automatically.\n'
                    'Run this in your environment and restart the kernel:\n'
                    '  conda install -c conda-forge python-louvain\n'
                    f'pip stderr: {result.stderr.strip()}'
                ) from None
            import community as community_louvain
        partition = community_louvain.best_partition(
            G, weight=edge_attr, resolution=resolution, random_state=seed
        )
        print(f'Louvain {tag}: {len(set(partition.values()))} communities')

    comm_df = pd.DataFrame([
        {'film_ref': ref, 'community_id': comm}
        for ref, comm in partition.items()
    ])
    comm_df.to_csv(outpath, sep='\t', index=False)
    print(f'Saved communities to: {os.path.abspath(outpath)}')
    return partition


def compare_partitions(orig_partition, new_partition, label='', top_n=15):
    """
    Compute NMI between two community partitions and print per-community stability.

    Only records present in *both* partitions are compared.

    Parameters
    ----------
    orig_partition : dict  { film_ref: community_id }
    new_partition  : dict  { film_ref: community_id }
    label          : str   short description for the new partition,
                           e.g. 'masked', 'skeleton', 'shotlist'
    top_n          : int   number of largest original communities to report

    Returns
    -------
    nmi    : float — Normalized Mutual Information (arithmetic average)
    common : list  — film_ref strings present in both partitions
    """
    common = sorted(set(new_partition.keys()) & set(orig_partition.keys()))
    if not common:
        print(f'compare_partitions: no records in common — cannot compute NMI.')
        return float('nan'), []

    y_orig = [orig_partition[r] for r in common]
    y_new  = [new_partition[r]  for r in common]

    nmi = normalized_mutual_info_score(y_orig, y_new, average_method='arithmetic')

    desc = f'original vs {label}' if label else 'partition comparison'
    print('=' * 60)
    print(f'NMI COMPARISON: {desc}')
    print('=' * 60)
    print(f'  Records in common  : {len(common):,}')
    print(f'  NMI                : {nmi:.4f}')
    print()

    if nmi >= 0.80:
        verdict = 'ROBUST — communities driven by structural convention.'
    elif nmi >= 0.60:
        verdict = 'MIXED — some communities reflect convention, others content.'
    else:
        verdict = 'CONTENT-DRIVEN — communities substantially disrupted.'
    print(f'  Verdict: {verdict}')
    print()

    df = pd.DataFrame({'film_ref': common, 'orig': y_orig, 'new': y_new})
    print(f'  Per-community stability (top {top_n} original communities by size):')
    print(f'  {"Community":<12} {"n":>6}  {"stability":>10}  interpretation')
    print('  ' + '-' * 55)
    for c, _ in Counter(y_orig).most_common(top_n):
        members   = df[df['orig'] == c]
        n         = len(members)
        top_count = members['new'].value_counts().iloc[0]
        stability = top_count / n
        interp    = ('stable'   if stability >= 0.70 else
                     'partial'  if stability >= 0.40 else
                     'disrupted')
        print(f'  C{c:<10} {n:>6}  {stability:>9.1%}  {interp}')

    return nmi, common
