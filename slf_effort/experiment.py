"""Run treatments x models, evaluate against labelled cells, paired block bootstrap."""
import numpy as np
import pandas as pd

from .background import TREATMENTS, build_training
from .metrics import (METRICS, alert_flags, auc, ap, block_ids, bootstrap_indices, boyce)
from .models import MODELS, fit_predict


def run_treatments(ds, treatments=TREATMENTS, models=MODELS, replicates=None, folds=None,
                   verbose=False):
    """Fit every treatment/model and score ALL cells in ds.cells.

    folds=None : train on all training cells, predict all cells (real-data,
                 temporal-holdout design).
    folds=array: spatial cross-fitting. Cells in fold f are predicted by models
                 trained only on cells outside fold f (used in simulation, where
                 there is no temporal split and in-sample scores would be unfair).
    Scores are averaged over `replicates` independent background redraws.
    """
    cfg = ds.cfg
    R = int(replicates or cfg.replicates)
    c = ds.cells
    n = len(c)
    X = c[ds.feat_cols].to_numpy(float)
    eff = c["effort"].to_numpy(float)
    eff_const = float(np.median(eff[c["in_M"].to_numpy()]))
    fold_ids = [None] if folds is None else list(np.unique(folds))
    scores = {(t, m): np.zeros(n) for t in treatments for m in models}
    diag = []
    for ti, t in enumerate(treatments):
        if verbose:
            print(f"  treatment {t}", flush=True)
        for r in range(R):
            for fi, f in enumerate(fold_ids):
                if f is None:
                    allowed = np.ones(n, dtype=bool)
                    pred_idx = np.arange(n)
                else:
                    allowed = folds != f
                    pred_idx = np.flatnonzero(folds == f)
                rng = np.random.default_rng(np.random.SeedSequence([cfg.seed, ti, r, fi]))
                idx, y, w, add_eff, note = build_training(t, ds, rng, allowed)
                Xtr, Xp = X[idx], X[pred_idx]
                if add_eff:
                    Xtr = np.column_stack([Xtr, eff[idx]])
                    Xp = np.column_stack([Xp, np.full(len(pred_idx), eff_const)])
                for m in models:
                    seed = int(rng.integers(1, 2**31 - 1))
                    scores[(t, m)][pred_idx] += fit_predict(m, Xtr, y, w, Xp, cfg, seed) / R
                diag.append({"treatment": t, "rep": r, "fold": fi, "n_pos": int((y == 1).sum()),
                             "n_bg": int((y == 0).sum()), "note": note})
    return scores, pd.DataFrame(diag)


def baseline_scores(ds):
    c = ds.cells
    return {("BASE_reports", "-"): np.log1p(c["n_reports"].to_numpy(float)),
            ("BASE_kde", "-"): c["effort_kde"].to_numpy(float)}


def evaluate(ds, scores, eval_sets, extra=None, alert_fracs=None):
    """Long table of point metrics for every (treatment, model, evaluation set)."""
    cfg = ds.cfg
    fracs = alert_fracs or cfg.alert_fracs
    all_scores = dict(scores)
    if extra:
        all_scores.update(extra)
    rows = []
    for (t, m), s in all_scores.items():
        flags = {f: alert_flags(s, f) for f in fracs}
        for name, (mask, yfull) in eval_sets.items():
            idx = np.flatnonzero(mask)
            if len(idx) == 0:
                continue
            y = yfull[idx].astype(bool)
            ss = s[idx]
            row = {"treatment": t, "model": m, "set": name, "n_cells": len(idx),
                   "n_present": int(y.sum()), "prevalence": float(y.mean()),
                   "auc": auc(y, ss), "ap": ap(y, ss),
                   "cbi": boyce(ss[y], ss) if y.any() else np.nan}
            for f in fracs:
                row[f"sens@{int(round(f*100))}"] = float(flags[f][idx][y].mean()) if y.any() else np.nan
                row[f"fpr@{int(round(f*100))}"] = float(flags[f][idx][~y].mean()) if (~y).any() else np.nan
            rows.append(row)
    return pd.DataFrame(rows)


def paired_deltas(ds, scores, eval_sets, ref="random_bg", metric_names=("auc", "ap", "sens", "fpr"),
                  B=None, seed=0, treatments=None):
    """Treatment-minus-reference metric differences with spatial-block bootstrap CIs."""
    cfg = ds.cfg
    B = int(B or cfg.bootstrap)
    c = ds.cells
    blocks = block_ids(c["px"].to_numpy(), c["py"].to_numpy(), cfg.block_km)
    rng = np.random.default_rng(seed)
    flags = {k: alert_flags(s, cfg.alert_primary) for k, s in scores.items()}
    models = sorted({m for (_, m) in scores})
    treats = treatments or sorted({t for (t, _) in scores if t != ref})
    out = []
    for name, (mask, yfull) in eval_sets.items():
        idx = np.flatnonzero(mask)
        if len(idx) < 20:
            continue
        y = yfull[idx].astype(bool)
        if y.all() or (not y.any()):
            continue
        boots = bootstrap_indices(blocks[idx], B, rng)
        for m in models:
            if (ref, m) not in scores:
                continue
            sr, fr = scores[(ref, m)][idx], flags[(ref, m)][idx]
            for t in treats:
                if (t, m) not in scores:
                    continue
                st, ft = scores[(t, m)][idx], flags[(t, m)][idx]
                for mn in metric_names:
                    fn = METRICS[mn]
                    obs = fn(y, st, ft) - fn(y, sr, fr)
                    ds_ = []
                    for b in boots:
                        yb = y[b]
                        if yb.all() or (not yb.any()):
                            continue
                        ds_.append(fn(yb, st[b], ft[b]) - fn(yb, sr[b], fr[b]))
                    ds_ = np.asarray(ds_, float)
                    ds_ = ds_[np.isfinite(ds_)]
                    if len(ds_) < 10:
                        lo = hi = p = np.nan
                    else:
                        lo, hi = np.percentile(ds_, [2.5, 97.5])
                        p = float(min(1.0, 2 * min((ds_ <= 0).mean(), (ds_ >= 0).mean())))
                    out.append({"set": name, "model": m, "treatment": t, "reference": ref,
                                "metric": mn, "value": fn(y, st, ft), "ref_value": fn(y, sr, fr),
                                "delta": obs, "ci_lo": lo, "ci_hi": hi, "p_boot": p,
                                "n_boot": len(ds_)})
    return pd.DataFrame(out)
