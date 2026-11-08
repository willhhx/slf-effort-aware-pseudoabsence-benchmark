#!/usr/bin/env python
"""Virtual-species experiment (ground truth known). Resumable: re-running skips finished seeds.

Example:
    python run_simulation.py --lyde /path/to/lyde.csv --out results/simulation
"""
import argparse
import os
import sys
import time
import warnings

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from slf_effort.data import Config, build_dataset, load_lyde          # noqa: E402
from slf_effort.plots import fig_sim                                    # noqa: E402
from slf_effort.simulate import SCENARIOS, run_one, summarise          # noqa: E402
from slf_effort.testing import write_synthetic_lyde                    # noqa: E402

warnings.filterwarnings("ignore")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lyde", help="path to full lyde.csv (provides the real study geometry/effort)")
    ap.add_argument("--synthetic", action="store_true", help="use built-in synthetic geometry instead of lyde.csv")
    ap.add_argument("--out", default="results/simulation")
    ap.add_argument("--n-seeds", type=int, default=12)
    ap.add_argument("--seed0", type=int, default=5000)
    ap.add_argument("--replicates", type=int, default=3)
    ap.add_argument("--folds", type=int, default=4)
    ap.add_argument("--trees", type=int, default=100)
    ap.add_argument("--scenarios", nargs="*", default=list(SCENARIOS))
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)

    if a.synthetic:
        tmp = os.path.join(a.out, "_synthetic_lyde.csv")
        write_synthetic_lyde(tmp, seed=1, n_cells=450)
        path = tmp
    elif a.lyde:
        path = a.lyde
    else:
        ap.error("give --lyde PATH or --synthetic")
    ds = build_dataset(load_lyde(path), Config())
    print(f"study region: {len(ds.cells)} cells, {int(ds.cells.is_pos.sum())} training-report cells")

    raw = os.path.join(a.out, "sim_results_raw.csv")
    done = pd.read_csv(raw) if os.path.exists(raw) else pd.DataFrame()
    finished = set(zip(done["scenario"], done["seed"])) if len(done) else set()
    t0 = time.time()
    for scen in a.scenarios:
        for k in range(a.n_seeds):
            seed = a.seed0 + k
            if (scen, seed) in finished:
                continue
            ev, diag, notes = run_one(ds, seed, replicates=a.replicates, k_folds=a.folds,
                                      n_trees=a.trees, scenario=scen)
            ev.to_csv(raw, mode="a", header=not os.path.exists(raw), index=False)
            print(f"[{time.time() - t0:6.0f}s] {scen} seed {seed} done", flush=True)

    res = pd.read_csv(raw)
    summ = pd.concat([summarise(res, metric=m) for m in ("auc", "ap")], ignore_index=True)
    summ.to_csv(os.path.join(a.out, "sim_summary.csv"), index=False)
    fig_sim(summ[summ["metric"] == "auc"], os.path.join(a.out, "fig_sim_truth_unreported.png"), "truth_unreported")
    fig_sim(summ[summ["metric"] == "auc"], os.path.join(a.out, "fig_sim_survey_sample.png"), "survey_sample")
    show = summ[(summ["metric"] == "auc") & (summ["set"] == "truth_unreported")]
    pd.set_option("display.width", 200)
    print(show[["scenario", "model", "treatment", "mean_delta", "se_delta", "win_rate", "n_seeds"]]
          .round(4).to_string(index=False))
    print("wrote", a.out)


if __name__ == "__main__":
    main()
