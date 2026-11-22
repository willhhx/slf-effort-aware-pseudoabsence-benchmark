#!/usr/bin/env python
"""Additional analyses requested in peer review. Same data, splits and seeds as run_real.py.

    python run_revision.py --lyde lyde.csv --covariates data/covariates_ext.csv --out results/revision

The covariates file must contain bio1 bio4 bio6 bio12 logpop (primary analysis) and bio5 bio15
(alternative covariate set). Make it with:
    python -m slf_effort.covariates --lyde lyde.csv --out data/covariates_ext.csv \\
        --raster bio1=wc2.1_10m_bio_1.tif ... --raster logpop=usa_pd_2020_1km.tif:log1p
"""
import argparse
import json
import os
import sys
import time
import warnings
from dataclasses import replace

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from slf_effort.background import ABLATION, LABELS, TREATMENTS                      # noqa: E402
from slf_effort.data import Config, build_dataset, load_lyde, real_eval_sets        # noqa: E402
from slf_effort.experiment import baseline_scores, evaluate, paired_deltas, run_treatments  # noqa: E402
from slf_effort import plots, revision as rv                                        # noqa: E402

warnings.filterwarnings("ignore")
PRIMARY_ENV = ["bio1", "bio4", "bio6", "bio12"]
ALT_ENV = ["bio1", "bio4", "bio5", "bio6", "bio12", "bio15"]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lyde", required=True)
    ap.add_argument("--covariates", required=True)
    ap.add_argument("--out", default="results/revision")
    ap.add_argument("--refits", type=int, default=30)
    ap.add_argument("--quick", action="store_true", help="smoke-test settings (not for the paper)")
    ap.add_argument("--jobs", type=int, default=-1)
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    t0 = time.time()
    cfg = Config(n_jobs=a.jobs)
    if a.quick:
        cfg = replace(cfg, replicates=2, n_trees=40, bootstrap=30)
        a.refits = 2
    df = load_lyde(a.lyde)
    cov = pd.read_csv(a.covariates)
    ds = build_dataset(df, cfg, cov, PRIMARY_ENV, ["logpop"])
    sets = real_eval_sets(ds)
    out = lambda f: os.path.join(a.out, f)                                           # noqa: E731

    # 1. main treatments (reproduces the published run) + ablation
    print("[1] main treatments + ablation", flush=True)
    scores, _ = run_treatments(ds, treatments=TREATMENTS + ABLATION)
    base = baseline_scores(ds)
    ev = evaluate(ds, scores, sets, extra=base)
    ev = rv.add_calibration(ev, ds, {**scores, **base}, sets)
    ev.to_csv(out("metrics_all_treatments.csv"), index=False)
    d_rand = paired_deltas(ds, scores, sets, ref="random_bg", seed=1,
                           treatments=[t for t in TREATMENTS + ABLATION if t != "random_bg"])
    d_rand.to_csv(out("paired_vs_random_all.csv"), index=False)
    sb = dict(scores)
    for m in ("rf", "lr"):
        sb[("BASE_kde", m)] = base[("BASE_kde", "-")]
    paired_deltas(ds, sb, sets, ref="BASE_kde", treatments=list(TREATMENTS), seed=2,
                  metric_names=("auc", "ap")).to_csv(out("paired_vs_baseline_auc_ap.csv"), index=False)

    # 2. separability of training data
    print("[2] training separability", flush=True)
    rv.separability(ds, ["random_bg"] + list(ABLATION) + ["ewc_pa"],
                    replicates=1 if a.quick else 3).to_csv(out("training_separability.csv"), index=False)

    # 3. survey description
    print("[3] survey description", flush=True)
    extra = pd.read_csv(a.lyde, usecols=["survey", "source_agency", "rounded_longitude_10k",
                                         "rounded_latitude_10k", "lyde_present", "bio_year",
                                         "collection_method"], low_memory=False)
    by_cell, _ = rv.survey_description(df, ds)
    by_cell.to_csv(out("survey_description_by_stratum.csv"), index=False)
    ex = extra[(extra["collection_method"] != "individual_reporting") & extra["bio_year"].isin(cfg.test_years)
               & extra["lyde_present"].notna()].copy()
    ex["cell_key"] = (ex["rounded_longitude_10k"].round(5).map("{:.5f}".format) + "_"
                      + ex["rounded_latitude_10k"].round(5).map("{:.5f}".format))
    ex = ex[ex["cell_key"].isin(set(ds.cells.loc[sets["all"][0], "cell_key"]))]
    agency = ex.groupby("source_agency").agg(records=("survey", "size"),
                                             pct_detected=("lyde_present", lambda s: 100 * s.astype(str).str.upper().eq("TRUE").mean()))
    agency["pct_records"] = 100 * agency["records"] / agency["records"].sum()
    agency.sort_values("records", ascending=False).to_csv(out("survey_records_by_agency.csv"))
    prog = ex["survey"].value_counts()
    prog.head(15).rename("records").to_csv(out("survey_records_by_programme_top15.csv"))

    # 4. environmental similarity of transfer cells
    print("[4] environmental similarity", flush=True)
    d_env, pct, analog = rv.environmental_novelty(ds)
    ds.cells["env_novelty_pct"] = pct
    ssets = rv.similarity_sets(ds, analog)
    ev_s = evaluate(ds, {k: v for k, v in scores.items() if k[0] in TREATMENTS}, ssets, extra=base)
    ev_s.to_csv(out("metrics_env_similarity_strata.csv"), index=False)
    paired_deltas(ds, scores, ssets, ref="random_bg", seed=3, treatments=["ewc_pa", "kde_bg", "thin_bg"],
                  metric_names=("auc",)).to_csv(out("paired_env_similarity_strata.csv"), index=False)
    sb2 = {("ewc_pa", m): scores[("ewc_pa", m)] for m in ("rf", "lr")}
    sb2.update({("BASE_kde", m): base[("BASE_kde", "-")] for m in ("rf", "lr")})
    paired_deltas(ds, sb2, ssets, ref="BASE_kde", seed=4, treatments=["ewc_pa"],
                  metric_names=("auc",)).to_csv(out("paired_env_similarity_vs_baseline.csv"), index=False)
    comp = []
    for name, (mask, y) in {**sets, **ssets}.items():
        comp.append({"set": name, "cells": int(mask.sum()), "pct_env_analog": 100 * float(analog[mask].mean()),
                     "median_env_novelty_pct": float(np.median(pct[mask])), "pct_detected": 100 * float(np.nanmean(y[mask]))})
    pd.DataFrame(comp).drop_duplicates("set").to_csv(out("env_similarity_composition.csv"), index=False)
    for col in rv.env_cols(ds):
        pass
    envsum = ds.cells[sets["all"][0]].assign(group=np.where(sets["core_states"][0][sets["all"][0]], "core", "transfer"))
    envsum.groupby("group")[rv.env_cols(ds) + ["logpop"]].median().to_csv(out("env_medians_core_vs_transfer.csv"))

    # 5. design / effort sensitivity (ewc_pa only; random_bg is unaffected by these settings)
    print("[5] design sensitivity", flush=True)
    rows = []
    for name, dv in rv.design_variants(ds).items():
        sc, diag = run_treatments(dv, treatments=("ewc_pa",))
        sc = {**sc, **{k: v for k, v in scores.items() if k[0] == "random_bg"}}
        d = paired_deltas(dv, sc, sets, ref="random_bg", seed=1, treatments=["ewc_pa"], metric_names=("auc",))
        d["variant"] = name
        d["n_pa_mean"] = diag["n_bg"].mean()
        rows.append(d)
    d = paired_deltas(ds, scores, sets, ref="random_bg", seed=1, treatments=["ewc_pa"], metric_names=("auc",))
    d["variant"] = "primary (rank, floor 0.05, exponent 1, buffer 50 km, population)"
    rows.insert(0, d)
    pd.concat(rows).to_csv(out("design_sensitivity.csv"), index=False)

    # 6. alternative covariate set (six WorldClim variables)
    print("[6] alternative covariate set", flush=True)
    ds6 = build_dataset(df, cfg, cov, ALT_ENV, ["logpop"])
    sets6 = real_eval_sets(ds6)
    sc6, _ = run_treatments(ds6)
    base6 = baseline_scores(ds6)
    evaluate(ds6, sc6, sets6, extra=base6).to_csv(out("altcov_metrics.csv"), index=False)
    paired_deltas(ds6, sc6, sets6, ref="random_bg", seed=1, metric_names=("auc",)).to_csv(out("altcov_paired_vs_random.csv"), index=False)
    sb6 = dict(sc6)
    sb6.update({("BASE_kde", m): base6[("BASE_kde", "-")] for m in ("rf", "lr")})
    paired_deltas(ds6, sb6, sets6, ref="BASE_kde", treatments=list(TREATMENTS), seed=2,
                  metric_names=("auc",)).to_csv(out("altcov_paired_vs_baseline.csv"), index=False)

    # 7. uncertainty: bootstrap block size and refitting
    print("[7] uncertainty", flush=True)
    bs = []
    for bk in (25.0, 50.0, 100.0):
        dsb = replace(ds, cfg=replace(ds.cfg, block_km=bk))
        d = paired_deltas(dsb, scores, sets, ref="random_bg", seed=1, treatments=["ewc_pa", "kde_bg", "thin_bg"],
                          metric_names=("auc",))
        d["block_km"] = bk
        bs.append(d)
    pd.concat(bs).to_csv(out("bootstrap_block_size.csv"), index=False)
    raw, summ = rv.refit_uncertainty(ds, n_refit=a.refits, replicates=1 if a.quick else 3, verbose=True)
    raw.to_csv(out("refit_raw.csv"), index=False)
    summ.to_csv(out("refit_summary.csv"), index=False)

    # 8. supplementary figures
    plots.fig_forest(d_rand[d_rand["treatment"].isin(["ewc_pa"] + list(ABLATION))],
                     out("figS_ablation_delta_auc.png"), "auc", treatments=["abl_B", "abl_E", "abl_W", "abl_BE",
                                                                             "abl_BW", "abl_EW", "abl_BEW", "ewc_pa"],
                     sets=["all", "zero_report_cells", "transfer_states", "core_states"])
    plots.fig_novelty(ds, pct, sets, out("figS_env_novelty.png"))

    with open(out("run_info.json"), "w") as f:
        json.dump({"config": cfg.to_dict(), "features": ds.feat_cols, "alt_features": ds6.feat_cols,
                   "refits": a.refits, "seconds": round(time.time() - t0)}, f, indent=2, default=str)
    print(f"done in {time.time() - t0:.0f}s -> {a.out}")


if __name__ == "__main__":
    main()
