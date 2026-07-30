"""
tfidf_utils.py — shared TF-IDF utilities for NLS catalogue analysis notebooks.

Used by:
  isolate_analysis_v3.ipynb  — KMeans clustering of isolate record descriptions
  community_analysis_v21.ipynb — Batch F TF-IDF cross-validation

Functions
---------
load_descriptions(records_dir, filter_refs=None)
    Load and concatenate dcterms:description text from XML record files.

fit_tfidf(texts, min_df_range=(3, 2, 1), max_df=0.85,
          max_features=10_000, sublinear_tf=True)
    Fit a TfidfVectorizer, retrying with lower min_df if vocabulary is empty.

kmeans_elbow(X, k_range=None, vis_dir='visualisations', timestamp='', title='')
    Compute KMeans inertia for a range of k values and save an elbow plot.

fit_kmeans(X, k, seed=42, n_init=10)
    Fit KMeans at a fixed k; return the model and cluster labels.
"""

import os
import re

import pandas as pd

# ── Description text loading ───────────────────────────────────────────────────

# re.DOTALL so multi-line <dcterms:description> elements are captured correctly.
_RE_DESC    = re.compile(r'<dcterms:description>(.*?)</dcterms:description>', re.DOTALL)
_RE_FILMREF = re.compile(r'\(filmRef\)([^<\s]+)')


def load_descriptions(records_dir, filter_refs=None):
    """
    Load description text from XML record files in records_dir.

    Iterates every file in records_dir, extracts the film_ref identifier and all
    dcterms:description field values, concatenates the field values with a space,
    and returns one row per record.

    Parameters
    ----------
    records_dir : str
        Path to directory of individual record XML files.
    filter_refs : set or None
        If given, only records whose film_ref is in this set are returned.
        Pass a set for O(1) membership tests on large corpora.

    Returns
    -------
    pd.DataFrame with columns:
        film_ref         : str  e.g. '(filmRef)0001'
        description_text : str  all description fields concatenated with spaces
    """
    rows = []
    for fname in sorted(os.listdir(records_dir)):
        fpath = os.path.join(records_dir, fname)
        try:
            text = open(fpath, encoding='utf-8').read()
        except Exception:
            continue
        m = _RE_FILMREF.search(text)
        if not m:
            continue
        film_ref = '(filmRef)' + m.group(1)
        if filter_refs is not None and film_ref not in filter_refs:
            continue
        descs    = _RE_DESC.findall(text)
        combined = ' '.join(d.strip() for d in descs)
        rows.append({'film_ref': film_ref, 'description_text': combined})
    return pd.DataFrame(rows, columns=['film_ref', 'description_text'])


# ── TF-IDF vectorisation ───────────────────────────────────────────────────────

def fit_tfidf(texts, min_df_range=(3, 2, 1), max_df=0.85,
              max_features=10_000, sublinear_tf=True):
    """
    Fit a TfidfVectorizer on texts, retrying with progressively lower min_df
    if the vocabulary is empty at the initial threshold.

    Parameters
    ----------
    texts        : iterable of str
    min_df_range : tuple of int — tried in order until vocabulary is non-empty
    max_df       : float — upper document-frequency cutoff (0–1)
                   Pass 1.0 or None to disable the upper cutoff.
    max_features : int or None — cap on vocabulary size; None = unlimited
    sublinear_tf : bool — apply log(1 + tf) term-frequency scaling

    Returns
    -------
    vectorizer : fitted TfidfVectorizer
    X          : sparse TF-IDF matrix  (n_docs × n_terms)
    min_df     : int  — the min_df value that produced a non-empty vocabulary
    """
    from sklearn.feature_extraction.text import TfidfVectorizer

    kw = dict(stop_words='english', max_df=max_df,
              sublinear_tf=sublinear_tf)
    if max_features is not None:
        kw['max_features'] = max_features

    for _min_df in min_df_range:
        vectorizer = TfidfVectorizer(min_df=_min_df, **kw)
        X = vectorizer.fit_transform(texts)
        if X.shape[1] > 0:
            return vectorizer, X, _min_df

    tried = list(min_df_range)
    raise ValueError(
        f'TF-IDF vocabulary is empty after trying min_df={tried}. '
        'Check that texts are non-empty and not all stop words.'
    )


# ── KMeans clustering ──────────────────────────────────────────────────────────

def kmeans_elbow(X, k_range=None, vis_dir='visualisations', timestamp='',
                 title='KMeans elbow plot'):
    """
    Fit KMeans for each k in k_range, plot inertia vs k, and save the figure.

    Parameters
    ----------
    X         : sparse or dense matrix — TF-IDF feature matrix
    k_range   : list of int — k values to evaluate; defaults to range(5, 51, 5)
    vis_dir   : str — directory for the output PNG
    timestamp : str — appended to output filename for provenance
    title     : str — plot title

    Returns
    -------
    inertias : list of float — within-cluster sum of squares for each k
    k_range  : list of int  — the k values used
    """
    import time as _time

    import matplotlib.pyplot as plt
    from sklearn.cluster import KMeans

    if k_range is None:
        k_range = list(range(5, 51, 5))

    inertias = []
    print(f'Computing inertia for k = {k_range[0]} … {k_range[-1]} ...')
    t0 = _time.time()
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=5)
        km.fit(X)
        inertias.append(km.inertia_)
        print(f'  k={k:3d}  inertia={km.inertia_:,.0f}  ({_time.time()-t0:.0f}s)')

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(k_range, inertias, marker='o', color='#2166ac', linewidth=2)
    ax.set_xlabel('Number of clusters (k)')
    ax.set_ylabel('Inertia (within-cluster sum of squares)')
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    ax.set_xticks(k_range)
    plt.tight_layout()

    os.makedirs(vis_dir, exist_ok=True)
    fname = f'tfidf-elbow_{timestamp}.png' if timestamp else 'tfidf-elbow.png'
    fpath = os.path.join(vis_dir, fname)
    plt.savefig(fpath, dpi=150, bbox_inches='tight')
    plt.show()
    print(f'Elbow plot saved to: {os.path.abspath(fpath)}')
    return inertias, k_range


def fit_kmeans(X, k, seed=42, n_init=10):
    """
    Fit KMeans at a fixed k.

    Parameters
    ----------
    X     : sparse or dense matrix
    k     : int — number of clusters
    seed  : int — random state for reproducibility
    n_init: int — number of initialisations

    Returns
    -------
    km     : fitted KMeans model
    labels : ndarray of int — cluster assignment per record
    """
    from sklearn.cluster import KMeans

    km = KMeans(n_clusters=k, random_state=seed, n_init=n_init)
    labels = km.fit_predict(X)
    return km, labels
