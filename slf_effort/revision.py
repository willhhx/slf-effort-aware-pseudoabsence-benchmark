"""Analyses added in response to peer review (all use the same data, splits and seeds).

  * survey description          what the professional test data are, per stratum
  * component ablation           buffer (B), environmental exclusion (E), effort weighting (W)
  * training separability        does environmental exclusion only make training easier?
  * environmental similarity     are transfer cells environmentally analogous to training?
  * effort / design sensitivity  propensity floor, transform, exponent, proxy, buffer distance
  * extra metrics                AP, Boyce, alert-budget sensitivity / FPR, calibration slope
  * uncertainty                  refitting on block-subsampled training data; bootstrap block size
"""
from dataclasses import replace

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold

from .background import ABLATION, TREATMENTS, _standardise, build_training
from .data import real_eval_sets
from .experiment import evaluate
from .metrics import auc, block_ids
from .models import MODELS, fit_predict


# ----------------------------------------------------------------------------- helpers
def env_cols(ds):
    return [f for f in ds.feat_cols if f not in ("dist_origin_km", "lon", "lat")] or list(ds.feat_cols)


def _tid(t):
    return TREATMENTS.index(t) if t in TREATMENTS else 100 + ABLATION.index(t)


def calibration_slope(y, s):
    """Slope of a logistic regression of the survey outcome on logit(score).

    1 = well-spread relative scores, <1 = over-confident spread, >1 = too compressed.
    The intercept is not interpretable for presence/pseudo-absence models (it depends on the
    pseudo-absence ratio), so only the slope is reported.
    """
    y = np.asarray(y).astype(int)
    if y.min() == y.max():
        return np.nan
    s = np.clip(np.asarray(s, float), 1e-3, 1 - 1e-3)
    z = np.log(s / (1 - s)).reshape(-1, 1)
    m = LogisticRegression(C=1e6, max_iter=1000).fit(z, y)
    return float(m.coef_[0, 0])


def add_calibration(ev, ds, scores, sets):
    out = []
    for (t, m), s in scores.items():
        for name, (mask, y) in sets.items():
            idx = np.flatnonzero(mask)
            if len(idx) < 20:
                continue
            out.append({"treatment": t, "model": m, "set": name,
                        "calib_slope": calibration_slope(y[idx], s[idx])})
    return ev.merge(pd.DataFrame(out), on=["treatment", "model", "set"], how="left")


# ----------------------------------------------------------------------------- survey data
def survey_description(df, ds):
    """Per-stratum description of the professional test cells and the rows behind them."""
    sets = real_eval_sets(ds)
    c = ds.cells
    cfg = ds.cfg
    test_rows = df[(df["method"] == "survey") & df["bio_year"].isin(cfg.test_years)]
    years = test_rows.groupby("cell_key")["bio_year"].nunique()
    rows = []
    for name, (mask, y) in sets.items():
        cc = c[mask]
        n = cc["test_n"].to_numpy(float)
        rows.append({"set": name, "cells": int(mask.sum()), "pct_detected": 100 * float(np.nanmean(y[mask])),
                     "records_median": float(np.median(n)), "records_q25": float(np.percentile(n, 25)),
                     "records_q75": float(np.percentile(n, 75)), "pct_cells_ge10_records": 100 * float((n >= 10).mean()),
                     "pct_cells_both_test_years": 100 * float((cc["cell_key"].map(years) >= 2).mean()),
                     "median_km_to_training_report": float(cc["dist_pos_km"].median())})
    by_cell = pd.DataFrame(rows)
    keys = set(c.loc[sets["all"][0], "cell_key"])
    tr = test_rows[test_rows["cell_key"].isin(keys)]
    return by_cell, tr


# ----------------------------------------------------------------------------- separability
def separability(ds, treatments, replicates=3, folds=5):
    """Cross-validated AUC for telling training presences from pseudo-absences, and how far
    (standardised environmental distance) pseudo-absences sit from the nearest presence."""
    c, cfg = ds.cells, ds.cfg
    X = c[ds.feat_cols].to_numpy(float)
    E = _standardise(c[env_cols(ds)].to_numpy(float), c["in_M"].to_numpy())
    rows = []
    for t in treatments:
        for r in range(replicates):
            rng = np.random.default_rng(np.random.SeedSequence([cfg.seed, _tid(t), r, 0]))
            idx, y, w, add_eff, _ = build_training(t, ds, rng)
            pos_idx = idx[y == 1]
            bg_idx = idx[y == 0]
            dist = cKDTree(E[pos_idx]).query(E[bg_idx], k=1)[0]
            skf = StratifiedKFold(folds, shuffle=True, random_state=r)
            oof = np.zeros(len(idx))
            for tr, te in skf.split(idx, y):
                oof[te] = fit_predict("rf", X[idx][tr], y[tr], w[tr], X[idx][te], cfg, 7 + r)
            rows.append({"treatment": t, "rep": r, "n_pos": len(pos_idx), "n_pa": len(bg_idx),
                         "train_cv_auc": auc(y, oof), "pa_env_dist_median": float(np.median(dist))})
    return (pd.DataFrame(rows).groupby("treatment")
            .agg(n_pos=("n_pos", "first"), n_pa=("n_pa", "mean"), train_cv_auc=("train_cv_auc", "mean"),
                 pa_env_dist_median=("pa_env_dist_median", "mean")).reset_index())


# ----------------------------------------------------------------------------- environmental similarity
def environmental_novelty(ds, k=5, analog_q=0.95):
    """Distance (standardised environment, k-th nearest training presence) of every cell,
    expressed as its percentile among the presences' own leave-one-out distances.
    A cell is 'analog' when that percentile is <= analog_q."""
    c = ds.cells
    E = _standardise(c[env_cols(ds)].to_numpy(float), c["in_M"].to_numpy())
    pos = c["is_pos"].to_numpy()
    tree = cKDTree(E[pos])
    d_self = tree.query(E[pos], k=k + 1)[0][:, -1]
    d_all = tree.query(E, k=k)[0][:, -1]
    d_all[pos] = d_self                      # presences: leave-one-out
    pct = np.searchsorted(np.sort(d_self), d_all, side="right") / len(d_self)
    return d_all, pct, pct <= analog_q


def similarity_sets(ds, analog):
    base = real_eval_sets(ds)
    c = ds.cells
    near = c["dist_pos_km"].to_numpy() <= 50
    tm, y = base["transfer_states"]
    cm, _ = base["core_states"]
    return {"core_states": (cm, y), "transfer_states": (tm, y),
            "transfer_env_analog": (tm & analog, y), "transfer_env_novel": (tm & ~analog, y),
            "transfer_within_50km_of_report": (tm & near, y), "transfer_beyond_50km": (tm & ~near, y)}


# ----------------------------------------------------------------------------- refitting uncertainty
def _fit_all(ds, t, allowed, salt, replicates):
    c, cfg = ds.cells, ds.cfg
    X = c[ds.feat_cols].to_numpy(float)
    eff = c["effort"].to_numpy(float)
    eff_const = float(np.median(eff[c["in_M"].to_numpy()]))
    out = {m: np.zeros(len(c)) for m in MODELS}
    for r in range(replicates):
        rng = np.random.default_rng(np.random.SeedSequence([cfg.seed, _tid(t), r, salt]))
        idx, y, w, add_eff, _ = build_training(t, ds, rng, allowed)
        Xtr, Xp = X[idx], X
        if add_eff:
            Xtr = np.column_stack([Xtr, eff[idx]])
            Xp = np.column_stack([X, np.full(len(c), eff_const)])
        for m in MODELS:
            out[m] += fit_predict(m, Xtr, y, w, Xp, cfg, int(rng.integers(1, 2**31 - 1))) / replicates
    return out


def refit_uncertainty(ds, treatments=("random_bg", "ewc_pa", "kde_bg", "thin_bg"), n_refit=30,
                      drop_frac=0.2, replicates=3, verbose=False):
    """Refit every treatment on training data from which a random 20% of 50-km blocks were
    removed (positives and accessible area), predict all test cells, and record AUC.
    The spread of treatment-minus-random differences across refits reflects training-data
    and background-sampling variability, which the test-cell bootstrap does not."""
    c, cfg = ds.cells, ds.cfg
    blocks = block_ids(c["px"].to_numpy(), c["py"].to_numpy(), cfg.block_km)
    ub = np.unique(blocks)
    sets = real_eval_sets(ds)
    rows = []
    for k in range(n_refit):
        rng = np.random.default_rng(np.random.SeedSequence([cfg.seed, 999, k]))
        drop = rng.choice(ub, int(round(drop_frac * len(ub))), replace=False)
        allowed = ~np.isin(blocks, drop)
        for t in treatments:
            sc = _fit_all(ds, t, allowed, 1000 + k, replicates)
            for m, s in sc.items():
                for name, (mask, y) in sets.items():
                    rows.append({"refit": k, "treatment": t, "model": m, "set": name,
                                 "auc": auc(y[mask].astype(bool), s[mask])})
        if verbose:
            print(f"  refit {k + 1}/{n_refit}", flush=True)
    raw = pd.DataFrame(rows)
    piv = raw.pivot_table(index=["refit", "model", "set"], columns="treatment", values="auc")
    summ = []
    for (m, s), g in piv.groupby(level=["model", "set"]):
        for t in treatments:
            if t == "random_bg":
                continue
            d = g[t] - g["random_bg"]
            summ.append({"model": m, "set": s, "treatment": t, "mean_auc": g[t].mean(),
                         "delta_mean": d.mean(), "delta_p2.5": d.quantile(.025), "delta_p97.5": d.quantile(.975),
                         "share_refits_positive": float((d > 0).mean()), "n_refit": len(d)})
    return raw, pd.DataFrame(summ)


# ----------------------------------------------------------------------------- sensitivity variants
def propensity_variant(effort, floor=0.05, transform="rank"):
    e = np.asarray(effort, float)
    if transform == "rank":
        r = pd.Series(e).rank(pct=True, method="average").to_numpy()
    elif transform == "linear":
        r = (e - np.nanmin(e)) / (np.nanmax(e) - np.nanmin(e))
    else:
        raise ValueError(transform)
    return floor + (1 - floor) * r


def design_variants(ds):
    """name -> modified Dataset (only q or one ewc_pa setting changes)."""
    c = ds.cells
    out = {}
    for fl in (0.01, 0.2):
        d = replace(ds, cells=c.assign(q=propensity_variant(c["effort"], fl)))
        out[f"propensity floor {fl}"] = d
    out["linear (min-max) transform"] = replace(ds, cells=c.assign(q=propensity_variant(c["effort"], 0.05, "linear")))
    out["effort proxy = report density"] = replace(ds, cells=c.assign(q=propensity_variant(c["effort_kde"])))
    for a in (0.5, 2.0):
        out[f"weight exponent {a}"] = replace(ds, cfg=replace(ds.cfg, effort_alpha=a))
    for b in (25.0, 100.0):
        out[f"buffer {int(b)} km"] = replace(ds, cfg=replace(ds.cfg, buffer_km=b))
    return out
