"""Evaluation metrics and spatial-block bootstrap."""
import numpy as np
from scipy.stats import rankdata, spearmanr
from sklearn.metrics import average_precision_score


def auc(y, s):
    y = np.asarray(y).astype(bool)
    n1 = int(y.sum())
    n0 = len(y) - n1
    if n1 == 0 or n0 == 0:
        return np.nan
    r = rankdata(s)
    return float((r[y].sum() - n1 * (n1 + 1) / 2.0) / (n1 * n0))


def ap(y, s):
    y = np.asarray(y).astype(int)
    if y.sum() == 0 or y.sum() == len(y):
        return np.nan
    return float(average_precision_score(y, s))


def boyce(s_pres, s_all, nbins=100, width=0.1):
    """Continuous Boyce index (Hirzel et al. 2006), moving window, as in ecospat."""
    s_pres = np.asarray(s_pres, float)
    s_all = np.asarray(s_all, float)
    if len(s_pres) < 10:
        return np.nan
    lo, hi = float(s_all.min()), float(s_all.max())
    if hi - lo <= 0:
        return np.nan
    w = width * (hi - lo)
    starts = np.linspace(lo, hi - w, nbins)
    f, mid = [], []
    for a in starts:
        b = a + w
        e = np.mean((s_all >= a) & (s_all <= b))
        if e <= 0:
            continue
        p = np.mean((s_pres >= a) & (s_pres <= b))
        f.append(p / e)
        mid.append((a + b) / 2.0)
    if len(f) < 3 or np.ptp(f) == 0:
        return np.nan
    return float(spearmanr(mid, f).correlation)


def alert_flags(s, frac):
    """Flag the top `frac` of the domain by score (rank-based; ties get average rank)."""
    pct = rankdata(s) / len(s)
    return pct > (1.0 - frac)


def _sens(y, s, f):
    y = np.asarray(y).astype(bool)
    return float(f[y].mean()) if y.any() else np.nan


def _fpr(y, s, f):
    y = np.asarray(y).astype(bool)
    return float(f[~y].mean()) if (~y).any() else np.nan


METRICS = {
    "auc": lambda y, s, f: auc(y, s),
    "ap": lambda y, s, f: ap(y, s),
    "sens": _sens,
    "fpr": _fpr,
}


def bootstrap_indices(blocks, B, rng):
    """B resamples (index arrays) of whole spatial blocks, drawn with replacement."""
    ub, inv = np.unique(blocks, return_inverse=True)
    groups = [np.flatnonzero(inv == i) for i in range(len(ub))]
    out = []
    for _ in range(B):
        pick = rng.integers(0, len(groups), len(groups))
        out.append(np.concatenate([groups[i] for i in pick]))
    return out


def block_ids(px, py, block_km):
    return (np.floor(np.asarray(px) / block_km).astype(np.int64) * 100003
            + np.floor(np.asarray(py) / block_km).astype(np.int64))
