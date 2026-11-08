"""Unit tests. Run:  python -m unittest discover -s tests -v   (from the project folder)"""
import os
import sys
import tempfile
import unittest
import warnings
from dataclasses import replace

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
warnings.filterwarnings("ignore")

from slf_effort.background import TREATMENTS, build_training, env_similar            # noqa: E402
from slf_effort.data import (Config, build_dataset, cell_key_from, load_lyde,         # noqa: E402
                             propensity, real_eval_sets)
from slf_effort.experiment import (baseline_scores, evaluate, paired_deltas,          # noqa: E402
                                   run_treatments)
from slf_effort.geo import gaussian_kde_at, nearest_distance, to_xyz                  # noqa: E402
from slf_effort.metrics import alert_flags, auc, ap, bootstrap_indices, boyce         # noqa: E402
from slf_effort.simulate import make_virtual_dataset, run_one, spatial_folds          # noqa: E402
from slf_effort.testing import synthetic_lyde, write_synthetic_lyde                   # noqa: E402

CFG = Config(replicates=2, n_trees=30, bootstrap=20, seed=7)


def make_ds(cfg=CFG, seed=0, n_cells=600):
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "lyde.csv")
        write_synthetic_lyde(p, seed=seed, n_cells=n_cells)
        return load_lyde(p), None


class TestGeo(unittest.TestCase):
    def test_distance_philadelphia_nyc(self):
        a = to_xyz([-75.1652], [39.9526])
        b = to_xyz([-74.0060], [40.7128])
        d = nearest_distance(a, b)[0]
        self.assertTrue(125 < d < 135, d)           # true great-circle ~130 km

    def test_kde(self):
        src = to_xyz([-75.0], [40.0])
        at_src = gaussian_kde_at(src, src, [2.0], 20.0)[0]
        self.assertAlmostEqual(at_src, 2.0, places=6)
        far = to_xyz([-75.0], [40.0 + 20.0 / 111.0])          # about 20 km north
        d = nearest_distance(far, src)[0]
        self.assertTrue(19.5 < d < 20.5, d)
        v = gaussian_kde_at(far, src, [2.0], 20.0)[0]
        self.assertAlmostEqual(v, 2.0 * np.exp(-0.5 * (d / 20.0) ** 2), places=8)
        very_far = to_xyz([-75.0], [43.0])
        self.assertEqual(gaussian_kde_at(very_far, src, [1.0], 20.0)[0], 0.0)


class TestMetrics(unittest.TestCase):
    def test_auc(self):
        y = np.array([0, 0, 0, 1, 1, 1])
        self.assertEqual(auc(y, np.array([.1, .2, .3, .7, .8, .9])), 1.0)
        self.assertEqual(auc(y, np.array([.9, .8, .7, .3, .2, .1])), 0.0)
        self.assertEqual(auc(y, np.ones(6)), 0.5)
        self.assertTrue(np.isnan(auc(np.ones(5), np.arange(5))))
        rng = np.random.default_rng(0)
        yy = rng.random(4000) < .3
        self.assertAlmostEqual(auc(yy, rng.random(4000)), 0.5, delta=0.03)

    def test_auc_matches_sklearn(self):
        from sklearn.metrics import roc_auc_score
        rng = np.random.default_rng(1)
        y = rng.random(500) < .4
        s = np.round(rng.random(500), 1)                       # many ties
        self.assertAlmostEqual(auc(y, s), roc_auc_score(y, s), places=10)
        self.assertTrue(0 <= ap(y, s) <= 1)

    def test_boyce(self):
        rng = np.random.default_rng(0)
        s_all = rng.random(3000)
        pres = s_all[rng.random(3000) < s_all ** 3]            # presences concentrated at high scores
        self.assertGreater(boyce(pres, s_all), 0.8)
        pres_rand = s_all[rng.random(3000) < 0.3]
        self.assertLess(abs(boyce(pres_rand, s_all)), 0.6)

    def test_alert_flags_fraction(self):
        s = np.random.default_rng(0).random(1000)
        self.assertAlmostEqual(alert_flags(s, 0.2).mean(), 0.2, delta=0.01)

    def test_bootstrap_blocks(self):
        blocks = np.repeat(np.arange(10), 5)
        idx = bootstrap_indices(blocks, 7, np.random.default_rng(0))
        self.assertEqual(len(idx), 7)
        for b in idx:
            counts = np.bincount(b, minlength=50).reshape(10, 5)
            self.assertTrue(((counts == counts[:, :1]).all()))   # blocks are resampled whole


class TestData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df, _ = make_ds()
        cls.ds = build_dataset(cls.df, CFG)

    def test_loader_flags(self):
        self.assertTrue({"present", "established", "method", "cell_key"}.issubset(self.df.columns))
        self.assertEqual(set(self.df["method"]), {"public", "survey"})

    def test_missing_columns_error(self):
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, "x.csv")
            pd.DataFrame({"longitude": [1], "latitude": [2]}).to_csv(p, index=False)
            with self.assertRaises(ValueError):
                load_lyde(p)

    def test_invariants(self):
        c = self.ds.cells
        self.assertTrue((c.loc[c.is_pos, "in_M"]).all())               # positives inside accessible area
        self.assertTrue((c.loc[c.is_pos, "n_reports"] > 0).all())
        self.assertTrue(c["q"].between(0.05, 1.0).all())
        self.assertTrue(c["effort_kde"].between(0, 1).all())
        self.assertGreater(int(c.is_pos.sum()), 20)
        self.assertGreater(int(c.test_label.notna().sum()), 20)

    def test_temporal_order_enforced(self):
        with self.assertRaises(ValueError):
            build_dataset(self.df, replace(CFG, test_years=(2021, 2022)))

    def test_positives_come_only_from_training_years_public(self):
        d = self.df
        keys = d[(d.method == "public") & d.present & d.bio_year.isin(CFG.train_years)].cell_key.unique()
        pos_keys = set(self.ds.cells.loc[self.ds.cells.is_pos, "cell_key"])
        self.assertEqual(set(keys), pos_keys)

    def test_test_labels_from_survey_test_years_only(self):
        d = self.df
        s = d[(d.method == "survey") & d.bio_year.isin(CFG.test_years)]
        expect = s.groupby("cell_key").present.max()
        c = self.ds.cells.set_index("cell_key")
        have = c["test_label"].dropna()
        common = have.index.intersection(expect.index)
        self.assertEqual(len(have), len(common))
        self.assertTrue((have.loc[common].astype(bool) == expect.loc[common]).all())

    def test_accessible_area_uses_only_pre_test_records(self):
        d = self.df
        only_test = set(d[d.bio_year > max(CFG.train_years)].cell_key) - set(d[d.bio_year <= max(CFG.train_years)].cell_key)
        c = self.ds.cells
        self.assertFalse(c.loc[c.cell_key.isin(only_test), "in_M"].any())

    def test_eval_sets_partition(self):
        s = real_eval_sets(self.ds)
        all_m = s["all"][0]
        self.assertTrue(((s["reported_cells"][0] | s["zero_report_cells"][0]) == all_m).all())
        self.assertFalse((s["reported_cells"][0] & s["zero_report_cells"][0]).any())
        self.assertTrue(((s["core_states"][0] | s["transfer_states"][0]) == all_m).all())

    def test_cell_key_roundtrip(self):
        k = cell_key_from([-75.647058823529412], [40.45045045045045])
        self.assertEqual(k.iloc[0], "-75.64706_40.45045")

    def test_covariate_merge_and_drop(self):
        c = self.ds.cells
        cov = c[["lon", "lat"]].copy()
        cov["bio1"] = np.random.default_rng(0).normal(10, 2, len(cov))
        cov["logpop"] = np.random.default_rng(1).normal(3, 1, len(cov))
        cov.loc[cov.index[:5], "bio1"] = np.nan
        ds2 = build_dataset(self.df, CFG, cov, ["bio1"], ["logpop"])
        self.assertEqual(ds2.notes["cells_dropped_missing_covariates"], 5)
        self.assertEqual(ds2.feat_cols, ["bio1", "dist_origin_km"])
        self.assertTrue(np.isfinite(ds2.cells[["bio1", "effort"]].to_numpy()).all())
        with self.assertRaises(ValueError):
            build_dataset(self.df, CFG, cov, ["nope"], None)

    def test_propensity(self):
        q = propensity(np.arange(100.0))
        self.assertAlmostEqual(q.min(), 0.05 + 0.95 / 100)
        self.assertAlmostEqual(q.max(), 1.0)


class TestBackground(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df, _ = make_ds()
        cls.ds = build_dataset(cls.df, CFG)

    def test_all_treatments_valid(self):
        c = self.ds.cells
        for t in TREATMENTS:
            rng = np.random.default_rng(0)
            idx, y, w, add, note = build_training(t, self.ds, rng)
            self.assertEqual(len(idx), len(y))
            self.assertTrue(c.loc[idx[y == 1], "is_pos"].all(), t)
            self.assertTrue(c.loc[idx[y == 0], "in_M"].all(), t)
            self.assertAlmostEqual(w[y == 1].sum(), w[y == 0].sum(), places=6)
            self.assertEqual(add, t == "effort_cov")
            self.assertEqual(len(set(idx[y == 0])), int((y == 0).sum()), t)     # no duplicate background

    def test_ewc_excludes_buffer(self):
        c = self.ds.cells
        xyz = c[["x", "y", "z"]].to_numpy()
        rng = np.random.default_rng(1)
        idx, y, w, _, _ = build_training("ewc_pa", self.ds, rng)
        pos = np.flatnonzero(c.is_pos.to_numpy())
        d = nearest_distance(xyz[idx[y == 0]], xyz[pos])
        self.assertTrue((d > CFG.buffer_km).all() or "geo_relaxed" in build_training("ewc_pa", self.ds, np.random.default_rng(1))[4])

    def test_thinning_reduces_positives(self):
        n_full = int(self.ds.cells.is_pos.sum())
        idx, y, *_ = build_training("thin_bg", self.ds, np.random.default_rng(2))
        self.assertLess(int((y == 1).sum()), n_full)

    def test_ipw_weights(self):
        idx, y, w, *_ = build_training("ewc_pa_ipw", self.ds, np.random.default_rng(3))
        q = self.ds.cells.loc[idx[y == 1], "q"].to_numpy()
        wp = w[y == 1]
        self.assertAlmostEqual(wp.mean(), 1.0, places=6)
        self.assertTrue(np.corrcoef(wp, 1 / q)[0, 1] > 0.999)

    def test_env_similar(self):
        rng = np.random.default_rng(0)
        pos_pts = rng.normal(0, 1, (200, 2))
        far_pts = rng.normal(8, 1, (50, 2))
        Xs = np.vstack([pos_pts, far_pts])
        pos = np.arange(200)
        cand = np.arange(200, 250)
        self.assertFalse(env_similar(Xs, pos, cand, 5, 0.9).any())
        near = np.vstack([pos_pts, rng.normal(0, 0.5, (50, 2))])
        self.assertTrue(env_similar(near, pos, cand, 5, 0.9).mean() > 0.9)

    def test_too_few_positives_errors(self):
        ds = build_dataset(self.df, CFG)
        ds.cells["is_pos"] = False
        with self.assertRaises(ValueError):
            build_training("random_bg", ds, np.random.default_rng(0))


class TestNoLeakage(unittest.TestCase):
    def test_scores_do_not_depend_on_test_outcomes(self):
        df, _ = make_ds()
        ds1 = build_dataset(df, CFG)
        ds2 = build_dataset(df, CFG)
        rng = np.random.default_rng(99)
        ds2.cells["test_label"] = rng.random(len(ds2.cells)) < 0.5
        ds2.cells["test_n"] = rng.integers(1, 50, len(ds2.cells)).astype(float)
        s1, _ = run_treatments(ds1, models=("rf", "lr"), replicates=1)
        s2, _ = run_treatments(ds2, models=("rf", "lr"), replicates=1)
        for k in s1:
            self.assertTrue(np.allclose(s1[k], s2[k]), k)

    def test_deterministic(self):
        df, _ = make_ds()
        ds = build_dataset(df, CFG)
        a, _ = run_treatments(ds, treatments=("random_bg", "ewc_pa"), models=("rf",), replicates=1)
        b, _ = run_treatments(ds, treatments=("random_bg", "ewc_pa"), models=("rf",), replicates=1)
        for k in a:
            self.assertTrue(np.allclose(a[k], b[k]), k)


class TestExperiment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        df, _ = make_ds()
        cls.ds = build_dataset(df, CFG)
        cls.scores, cls.diag = run_treatments(cls.ds, replicates=2)
        cls.sets = real_eval_sets(cls.ds)

    def test_scores_valid(self):
        n = len(self.ds.cells)
        for k, s in self.scores.items():
            self.assertEqual(len(s), n)
            self.assertTrue(np.isfinite(s).all(), k)
            self.assertTrue(((s >= 0) & (s <= 1)).all(), k)

    def test_evaluate_and_deltas(self):
        ev = evaluate(self.ds, self.scores, self.sets, extra=baseline_scores(self.ds))
        self.assertTrue({"auc", "ap", "cbi", "sens@20", "fpr@20"}.issubset(ev.columns))
        self.assertTrue(ev["auc"].dropna().between(0, 1).all())
        d = paired_deltas(self.ds, self.scores, self.sets, B=20)
        self.assertGreater(len(d), 0)
        row = d.iloc[0]
        self.assertAlmostEqual(row["delta"], row["value"] - row["ref_value"], places=9)
        self.assertTrue((d["ci_lo"].dropna() <= d["ci_hi"].dropna()).all())

    def test_model_beats_chance_on_synthetic(self):
        ev = evaluate(self.ds, self.scores, self.sets)
        rf = ev[(ev.model == "rf") & (ev.treatment == "random_bg") & (ev.set == "all")]["auc"].iloc[0]
        self.assertGreater(rf, 0.6)

    def test_folds_predict_each_cell_once(self):
        ds, sets = make_virtual_dataset(self.ds, seed=3)
        ds.cfg = replace(ds.cfg, n_trees=20)
        folds = spatial_folds(ds, 4, 100.0, 3)
        sc, _ = run_treatments(ds, treatments=("random_bg",), models=("lr",), replicates=1, folds=folds)
        s = sc[("random_bg", "lr")]
        self.assertTrue((s > 0).all())


class TestSimulation(unittest.TestCase):
    def test_virtual_dataset_invariants(self):
        df, _ = make_ds()
        real = build_dataset(df, CFG)
        ds, sets = make_virtual_dataset(real, seed=11)
        c = ds.cells
        self.assertTrue((c.loc[c.is_pos, "truth"]).all())                 # reports only of true presences
        self.assertAlmostEqual(c["truth"].mean(), 0.25, delta=0.06)
        self.assertGreater(int(c.is_pos.sum()), 10)
        self.assertTrue(set(sets) == {"truth_all", "truth_unreported", "survey_sample", "survey_unreported"})
        m, y = sets["truth_unreported"]
        self.assertFalse((m & c.is_pos.to_numpy()).any())
        ds2, _ = make_virtual_dataset(real, seed=11)
        self.assertTrue(np.array_equal(ds.cells["truth"].to_numpy(), ds2.cells["truth"].to_numpy()))

    def test_run_one_smoke(self):
        df, _ = make_ds()
        real = build_dataset(df, CFG)
        ev, diag, notes = run_one(real, 21, replicates=1, k_folds=3, n_trees=20,
                                  treatments=("random_bg", "ewc_pa"), scenario="adverse")
        self.assertTrue(ev["auc"].notna().any())
        self.assertEqual(set(ev["scenario"]), {"adverse"})


class TestCovariates(unittest.TestCase):
    def test_reader(self):
        from slf_effort.covariates import selftest
        selftest()


if __name__ == "__main__":
    unittest.main(verbosity=2)
