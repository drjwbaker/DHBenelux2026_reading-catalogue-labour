"""
utils.py — miscellaneous shared utilities for NLS catalogue analysis notebooks.

Used by:
  isolate_analysis_v3.ipynb      — auto-detect latest communities TSV
  community_analysis_v21.ipynb   — auto-detect latest communities TSV

Functions
---------
latest_communities_tsv(pattern='derived-data/communities_*.tsv')
    Return the path to the most recently produced communities TSV, identified
    by the YYYYMMDD-HHMMSS timestamp embedded in the filename (not filesystem
    mtime, so file-copy operations cannot mislead it).
"""

import glob
import os
import re

_TS_PATTERN = re.compile(r'communities_.*_(\d{8}-\d{6})\.tsv$')


def _extract_ts(path):
    """Return the YYYYMMDD-HHMMSS timestamp string from a communities filename."""
    m = _TS_PATTERN.search(os.path.basename(path))
    return m.group(1) if m else ''


def latest_communities_tsv(pattern='derived-data/communities_*.tsv'):
    """
    Auto-detect the most recent communities TSV by the timestamp in its filename.

    Warns if more than one file exists and advises archiving old files to
    derived-data/attic/ to suppress the warning.

    Parameters
    ----------
    pattern : str — glob pattern to search; default finds all communities_*.tsv
              files in derived-data/ relative to the current working directory.

    Returns
    -------
    str : path to the most recent matching file

    Raises
    ------
    FileNotFoundError if no file matches pattern.
    """
    candidates = sorted(glob.glob(pattern), key=_extract_ts, reverse=True)

    if not candidates:
        raise FileNotFoundError(
            f'No file matching {pattern!r} found in {os.getcwd()}. '
            'Run community_analysis through Batch B first.'
        )

    if len(candidates) > 1:
        print(f'WARNING: {len(candidates)} communities files found — '
              f'using the most recent.')
        print('  Archive old files to derived-data/attic/ to suppress this warning:')
        for f in candidates[1:]:
            print(f'    {f}')
        print()

    return candidates[0]
