#!/usr/bin/env python
"""Real-data experiment on lydemapr (spotted lanternfly).

Presence-only public reports (train bio-years) -> predict structured-survey outcomes (test bio-years).

Examples
--------
Core analysis, lyde.csv only (no downloads needed):
    python run_real.py --lyde /path/to/lyde.csv --out results/real

With external covariates (made by `python -m slf_effort.covariates ...`):
    python run_real.py --lyde lyde.csv --covariates covariates.csv \
        --env-cols bio1 bio4 bio12 elev --effort-cols logpop --out results/real_cov
"""
import argparse
import json
import os
import platform
import sys
import time
import warnings
from dataclasses import replace

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from slf_effort import __version__                                           # noqa: E402
from slf_effort.background import TREATMENTS                                 # noqa: E402
from slf_effort.data import (Config, build_dataset, data_summary, load_lyde,  # noqa: E402
                             real_eval_sets)
from slf_effort.experiment import (baseline_scores, evaluate, paired_deltas,  # noqa: E402
                                   run_treatments)
from slf_effort.plots import fig_forest, fig_map                             # noqa: E402
from slf_effort.testing import write_synthetic_lyde                          # noqa: E402

warnings.filterwarnings("ignore")


def parse(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lyde", help="path to the FULL lyde.csv from Zenodo (not lyde_10k.csv)")
    ap.add_argument("--synthetic", action="store_true", help="run on built-in synthetic data (self-test)")
    ap.add_argument("--out", default="results/real")
    ap.add_argument("--covariates", help="CSV with lon, lat + covariate columns (see slf_effort.covariates)")
    ap.add_argument("--env-cols", nargs="*", default=None, help="environmental covariate columns to use as features")
    ap.add_argument("--effort-cols", nargs="*", default=None, help="effort-proxy columns (e.g. log population density)")
    ap.add_argument("--no-origin", action="store_true", help="do not add distance-to-origin as a feature (covariate mode)")
    ap.add_argument("--target", choices=["present", "established"], default="present")
    ap.add_argument("--train-years", nargs="+", type=int, default=[2019, 2020, 2021])
    ap.add_argument("--test-years", nargs="+", type=int, default=[2022, 2023])
    ap.add_argument("--min-rows", type=int, default=3, help="min survey records for a test cell (primary analysis)")
    ap.add_argument("--buffer-km", type=float, default=50.0)
    ap.add_argument("--replicates", type=int, default=10)
    ap.add_argument("--trees", type=int, default=200)
    ap.add_argument("--bootstrap", type=int, default=200)
    ap.add_argument("--jobs", type=int, default=-1)
    ap.add_argument("--seed", type=int, default=20261107)
    ap.add_argument("--quick", action="store_true", help="fast smoke settings (not for the paper)")
    return ap.parse_args(argv)


def main(argv=None):
    a = parse(argv)
    os.makedirs(a.out, exist_ok=True)
    if a.synthetic:
        path = os.path.join(a.out, "_synthetic_lyde.csv")
        write_synthetic_lyde(path, seed=0, n_cells=600)
    elif a.lyde:
        path = a.lyde
    else:
        sys.exit("give --lyde PATH (full lyde.csv) or --synthetic")
    cfg = Config(train_years=tuple(a.train_years), test_years=tuple(a.test_years), target=a.target,
                 min_survey_rows=a.min_rows, buffer_km=a.buffer_km, replicates=a.replicates,
                 n_trees=a.trees, bootstrap=a.bootstrap, n_jobs=a.jobs, seed=a.seed)
    if a.quick:
        cfg = replace(cfg, replicates=2, n_trees=60, bootstrap=40)

    t0 = time.time()
    df = load_lyde(path)
    cov = pd.read_csv(a.covariates) if a.covariates else None
    ds = build_dataset(df, cfg, cov, a.env_cols, a.effort_cols, add_origin=not a.no_origin)
    c = ds.cells
    print(f"rows {len(df):,} | study-region cells {len(c):,} | training-report cells {int(c.is_pos.sum()):,} "
          f"| accessible area {int(c.in_M.sum()):,} | core states {ds.core_states}")
    print("features:", ds.feat_cols, "| effort:", ds.notes.get("effort_source"))
    if ds.notes.get("cells_dropped_missing_covariates"):
        print("WARNING: dropped cells with missing covariates:", ds.notes["cells_dropped_missing_covariates"],
              "(positives:", ds.notes["positives_dropped_missing_covariates"], ")")

    data_summary(df, ds).to_csv(os.path.join(a.out, "table1_data_summary.csv"), index=False)
    fig_map(ds, os.path.join(a.out, "fig_map.png"))

    print("fitting treatments ...", flush=True)
    scores, diag = run_treatments(ds, verbose=True)
    diag.to_csv(os.path.join(a.out, "training_diagnostics.csv"), index=False)
    base = baseline_scores(ds)
    sets = real_eval_sets(ds)

    ev = evaluate(ds, scores, sets, extra=base)
    ev.to_csv(os.path.join(a.out, "metrics_by_stratum.csv"), index=False)
    sens = []
    for mr in (1, 3, 10):
        e = evaluate(ds, scores, real_eval_sets(ds, mr), extra=base)
        e["min_rows"] = mr
        sens.append(e)
    pd.concat(sens).to_csv(os.path.join(a.out, "sensitivity_min_survey_rows.csv"), index=False)

    print("block-bootstrap comparisons ...", flush=True)
    d_rand = paired_deltas(ds, scores, sets, ref="random_bg", seed=1)
    d_rand.to_csv(os.path.join(a.out, "paired_vs_random_background.csv"), index=False)
    sb = dict(scores)
    for m in sorted({m for (_, m) in scores}):
        sb[("BASE_kde", m)] = base[("BASE_kde", "-")]
    d_base = paired_deltas(ds, sb, sets, ref="BASE_kde", treatments=list(TREATMENTS), seed=2)
    d_base.to_csv(os.path.join(a.out, "paired_vs_report_density_baseline.csv"), index=False)
    fig_forest(d_rand, os.path.join(a.out, "fig_delta_auc_vs_random.png"), "auc")
    fig_forest(d_rand, os.path.join(a.out, "fig_delta_fpr_vs_random.png"), "fpr")
    fig_forest(d_base, os.path.join(a.out, "fig_delta_auc_vs_baseline.png"), "auc",
               ref_label="report-density baseline")

    pred = c[["cell_key", "lon", "lat", "state", "n_reports", "is_pos", "in_M", "test_n", "test_label"]].copy()
    for (t, m), s in scores.items():
        pred[f"{t}__{m}"] = s
    pred["BASE_kde"] = base[("BASE_kde", "-")]
    pred.to_csv(os.path.join(a.out, "predictions.csv"), index=False)

    meta = {"version": __version__, "python": platform.python_version(), "config": cfg.to_dict(),
            "features": ds.feat_cols, "origin_lonlat": ds.origin, "core_states": ds.core_states,
            "notes": {k: str(v) for k, v in ds.notes.items()}, "lyde_file": os.path.abspath(path),
            "seconds": round(time.time() - t0, 1)}
    with open(os.path.join(a.out, "run_config.json"), "w") as f:
        json.dump(meta, f, indent=2, default=str)

    pd.set_option("display.width", 220)
    show = ev[ev["set"].isin(["all", "zero_report_cells", "transfer_states"])]
    print("\nAUC by treatment and stratum (higher is better):")
    print(show.pivot_table(index=["model", "treatment"], columns="set", values="auc").round(3).to_string())
    print(f"\nFalse-positive rate at a {int(cfg.alert_primary * 100)}% alert budget (lower is better):")
    print(show.pivot_table(index=["model", "treatment"], columns="set",
                           values=f"fpr@{int(cfg.alert_primary * 100)}").round(3).to_string())
    print(f"\nDone in {time.time() - t0:.0f}s. Outputs in {a.out}")
    return ev


if __name__ == "__main__":
    main()
