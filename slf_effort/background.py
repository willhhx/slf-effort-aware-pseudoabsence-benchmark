"""Background / pseudo-absence generators (the experimental treatments).

All treatments train on PRESENCE-ONLY public reports (cells with is_pos) and draw
background / pseudo-absence cells from the accessible area M (in_M). None of them
sees any survey outcome.

  random_bg    uniform random background from M                         (baseline)
  thin_bg      positives thinned to 1 per thin_km block + random bg     (spatial thinning)
  kde_bg       background drawn proportional to the KDE of training
               reports (target-group-style bias matching)               (standard bias fix)
  ewc_pa       PROPOSED: geographic buffer + environmental exclusion +
               pseudo-absences sampled proportional to reporting
               propensity q ("looked-at" cells are better absences")
  ewc_pa_ipw   ewc_pa + positives weighted by 1/q (inverse propensity)
  effort_cov   random bg, effort proxy included as a covariate and
               held constant at prediction time                         (bias-covariate adjustment)
"""
from typing import Optional, Tuple

import numpy as np
from scipy.spatial import cKDTree

from .geo import nearest_distance

TREATMENTS = ("random_bg", "thin_bg", "kde_bg", "ewc_pa", "ewc_pa_ipw", "effort_cov")

LABELS = {
    "random_bg": "Random background",
    "thin_bg": "Spatial thinning",
    "kde_bg": "KDE-matched background",
    "ewc_pa": "Effort-weighted constrained PA (proposed)",
    "ewc_pa_ipw": "Proposed + inverse-propensity weights",
    "effort_cov": "Effort covariate held constant",
    "BASE_reports": "Baseline: report count",
    "BASE_kde": "Baseline: report KDE",
}


def _standardise(X: np.ndarray, ref_mask: np.ndarray) -> np.ndarray:
    mu = X[ref_mask].mean(axis=0)
    sd = X[ref_mask].std(axis=0)
    sd[sd == 0] = 1.0
    return (X - mu) / sd


def env_similar(Xs: np.ndarray, pos: np.ndarray, cand: np.ndarray, k: int, q: float) -> np.ndarray:
    """True for candidates that sit inside the presences' environmental envelope.

    Envelope: a candidate is 'similar' if the distance to its k-th nearest
    presence (standardised covariate space) is <= the q-quantile of the same
    statistic among the presences themselves (self excluded).
    """
    kk = int(max(1, min(k, len(pos) - 1)))
    tree = cKDTree(Xs[pos])
    d_self, _ = tree.query(Xs[pos], k=kk + 1)
    thr = np.quantile(d_self[:, -1], q)
    d_c, _ = tree.query(Xs[cand], k=kk)
    d_c = d_c if d_c.ndim == 1 else d_c[:, -1]
    return d_c <= thr


def _ewc_candidates(c, X, pos, Midx, n_bg, cfg):
    xyz = c[["x", "y", "z"]].to_numpy()
    d_pos = nearest_distance(xyz[Midx], xyz[pos])
    geo_ok = Midx[d_pos > cfg.buffer_km]
    if len(geo_ok) == 0:                       # degenerate: take the farthest cells
        order = np.argsort(-d_pos)[:n_bg]
        return Midx[order], "geo_relaxed"
    Xs = _standardise(X, np.isin(np.arange(len(c)), Midx))
    for qq in (cfg.env_quantile, 0.25, 0.1, 0.0):
        if qq > 0:
            sim = env_similar(Xs, pos, geo_ok, cfg.env_k, qq)
        else:
            sim = np.zeros(len(geo_ok), dtype=bool)
        cand = geo_ok[~sim]
        if len(cand) >= n_bg:
            return cand, ("" if qq == cfg.env_quantile else f"env_q={qq}")
    return cand, f"short:{len(cand)}"


def build_training(treatment: str, ds, rng: np.random.Generator,
                   allowed: Optional[np.ndarray] = None):
    """Return (idx, y, w, add_effort_covariate, note).

    idx: row indices into ds.cells; y: 1 = reported presence, 0 = background /
    pseudo-absence; w: sample weights with total presence weight == total
    background weight.
    """
    if treatment not in TREATMENTS:
        raise ValueError(f"unknown treatment {treatment}")
    c, cfg = ds.cells, ds.cfg
    n = len(c)
    allowed = np.ones(n, dtype=bool) if allowed is None else allowed
    pos = np.flatnonzero(c["is_pos"].to_numpy() & allowed)
    Midx = np.flatnonzero(c["in_M"].to_numpy() & allowed)
    if len(pos) < 5 or len(Midx) < 10:
        raise ValueError(f"too few training cells (pos={len(pos)}, M={len(Midx)})")
    X = c[ds.feat_cols].to_numpy(float)
    q = c["q"].to_numpy(float)
    n_bg = int(min(round(cfg.bg_ratio * len(pos)), cfg.max_bg_frac * len(Midx)))
    n_bg = max(n_bg, 5)
    wpos = np.ones(len(pos))
    note = ""
    add_effort = False

    if treatment in ("random_bg", "effort_cov"):
        bg = rng.choice(Midx, n_bg, replace=False)
        add_effort = treatment == "effort_cov"
    elif treatment == "thin_bg":
        keyv = (np.floor(c["px"].to_numpy()[pos] / cfg.thin_km).astype(np.int64) * 100003
                + np.floor(c["py"].to_numpy()[pos] / cfg.thin_km).astype(np.int64))
        order = rng.permutation(len(pos))
        _, first = np.unique(keyv[order], return_index=True)
        pos = pos[np.sort(order[first])]
        wpos = np.ones(len(pos))
        bg = rng.choice(Midx, n_bg, replace=False)
    elif treatment == "kde_bg":
        p = c["effort_kde"].to_numpy(float)[Midx] + 1e-6
        bg = rng.choice(Midx, n_bg, replace=False, p=p / p.sum())
    else:  # ewc_pa, ewc_pa_ipw
        cand, note = _ewc_candidates(c, X, pos, Midx, n_bg, cfg)
        # Subsample so that effort weighting matters and replicates differ even
        # when candidates are scarce: never use more than max_bg_frac of them.
        k = int(min(n_bg, max(5, cfg.max_bg_frac * len(cand))))
        k = min(k, len(cand))
        p = q[cand] ** cfg.effort_alpha
        bg = rng.choice(cand, k, replace=False, p=p / p.sum())
        if treatment == "ewc_pa_ipw":
            wpos = 1.0 / q[pos]
            wpos = wpos * (len(pos) / wpos.sum())

    idx = np.concatenate([pos, bg])
    y = np.concatenate([np.ones(len(pos)), np.zeros(len(bg))])
    w = np.concatenate([wpos, np.full(len(bg), wpos.sum() / len(bg))])
    return idx, y, w, add_effort, note
