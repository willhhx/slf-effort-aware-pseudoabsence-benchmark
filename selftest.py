#!/usr/bin/env python
"""Run this FIRST on your machine. ~1-2 minutes, needs no data download.

Checks: unit tests, the full real-data script on synthetic lydemapr-format data,
and the simulation script on synthetic geometry. Prints PASS or the failing step.
"""
import os
import sys
import tempfile
import traceback
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def step(n, total, msg):
    print(f"\n[{n}/{total}] {msg}", flush=True)


def main():
    import warnings
    warnings.filterwarnings("ignore")
    import pandas
    import scipy
    import sklearn
    print(f"python {sys.version.split()[0]} | numpy {np.__version__} | pandas {pandas.__version__} | "
          f"scipy {scipy.__version__} | scikit-learn {sklearn.__version__}")
    ok = True
    step(1, 3, "unit tests")
    suite = unittest.defaultTestLoader.discover(os.path.join(HERE, "tests"))
    res = unittest.TextTestRunner(verbosity=0).run(suite)
    ok &= res.wasSuccessful()

    with tempfile.TemporaryDirectory() as td:
        step(2, 3, "run_real.py on synthetic data (--quick)")
        try:
            import run_real
            ev = run_real.main(["--synthetic", "--quick", "--out", os.path.join(td, "real"), "--jobs", "1"])
            for f in ("table1_data_summary.csv", "metrics_by_stratum.csv", "paired_vs_random_background.csv",
                      "paired_vs_report_density_baseline.csv", "predictions.csv", "fig_map.png",
                      "fig_delta_auc_vs_random.png", "run_config.json"):
                assert os.path.exists(os.path.join(td, "real", f)), f"missing output {f}"
            assert np.isfinite(ev["auc"].dropna()).all() and len(ev) > 10
        except Exception:
            traceback.print_exc()
            ok = False

        step(3, 3, "run_simulation.py on synthetic geometry (tiny)")
        try:
            import run_simulation
            run_simulation.main(["--synthetic", "--out", os.path.join(td, "sim"), "--n-seeds", "1",
                                 "--scenarios", "adverse", "--replicates", "1", "--folds", "3", "--trees", "30"])
            for f in ("sim_results_raw.csv", "sim_summary.csv", "fig_sim_truth_unreported.png"):
                assert os.path.exists(os.path.join(td, "sim", f)), f"missing output {f}"
        except Exception:
            traceback.print_exc()
            ok = False

    print("\n" + ("SELFTEST PASS" if ok else "SELFTEST FAILED - see messages above"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
