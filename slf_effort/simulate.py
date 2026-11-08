"""Virtual-species experiment: ground truth is KNOWN, so we can measure how well
each pseudo-absence / bias-correction treatment recovers it.

Geometry and the effort surface come from the real study region (cells and
their report KDE); the species' true distribution, its environmental covariates
and the reporting process are simulated.

  truth      ~ Bernoulli(expit(a + 1.6*env1 - 1.0*env2^2 + 0.8*env3))
  reported   = truth AND Bernoulli(1 - exp(-kappa * effort_true))      -> presence-only data
  survey     = cell sampled with prob ~ effort_true^gamma (effort-biased), detection < 1
  models see = noisy env covariates (no coordinates) and a NOISY effort proxy
"""
from dataclasses import replace

import numpy as np
import pandas as pd
from scipy.special import expit

from .data import Dataset, propensity
from .experiment import baseline_scores, evaluate, run_treatments
from .geo import gaussian_kde_at
from .metrics import block_ids


def _field(rng, px, py, scale_km, n_waves=12):
    k = rng.normal(size=(n_waves, 2)) / scale_km
    ph = rng.uniform(0, 2 * np.pi, n_waves)
    f = np.cos(2 * np.pi * (np.outer(px, k[:, 0]) + np.outer(py, k[:, 1])) + ph).sum(axis=1)
    return (f - f.mean()) / f.std()


def _solve(fn, target, lo, hi, iters=60):
    """Bisection for increasing fn."""
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        if fn(mid) < target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


SCENARIOS = {
    # effort independent of the environment: bias adds noise but does not confound
    "independent": dict(effort_env_corr=0.0, bias_power=1.0, report_mean=0.4),
    # people live/report in particular environments: bias confounds the response curve
    "confounded": dict(effort_env_corr=1.0, bias_power=1.0, report_mean=0.4),
    # strong, concentrated effort and few reports
    "confounded_strong": dict(effort_env_corr=1.0, bias_power=2.0, report_mean=0.2),
    # effort concentrated where the species is LESS suitable along env3 (bias works against signal)
    "adverse": dict(effort_env_corr=0.0, effort_env3=-1.5, bias_power=1.0, report_mean=0.3),
}


def make_virtual_dataset(real_ds: Dataset, seed: int, prevalence=0.25, report_mean=0.4,
                         survey_frac=0.35, survey_gamma=0.7, detect=0.9,
                         proxy_sigma=0.5, env_noise=0.3, effort_env_corr=1.0, bias_power=1.0,
                         effort_env3=0.0):
    rng = np.random.default_rng(seed)
    base = real_ds.cells
    n = len(base)
    px, py = base["px"].to_numpy(), base["py"].to_numpy()
    e_base = np.clip(base["effort_kde"].to_numpy(float), 0.02, 1.0)

    env = np.column_stack([_field(rng, px, py, s) for s in (150.0, 80.0, 250.0)])
    eta = 1.6 * env[:, 0] - 1.0 * env[:, 1] ** 2 + 0.8 * env[:, 2]
    a = _solve(lambda a_: expit(a_ + eta).mean(), prevalence, -15, 15)
    truth = rng.random(n) < expit(a + eta)

    # true effort: real spatial effort pattern, optionally tilted toward high env1
    e_true = e_base * np.exp(effort_env_corr * env[:, 0] + effort_env3 * env[:, 2])
    e_true = np.clip(e_true / e_true.max(), 0.02, 1.0) ** bias_power

    kappa = _solve(lambda k_: (1 - np.exp(-k_ * e_true))[truth].mean(), report_mean, 1e-6, 1e4)
    q_true = 1 - np.exp(-kappa * e_true)
    reported = truth & (rng.random(n) < q_true)

    s_raw = q_true ** survey_gamma
    scale = _solve(lambda c_: np.clip(c_ * s_raw, 0, 1).mean(), survey_frac, 1e-6, 1e4)
    sampled = rng.random(n) < np.clip(scale * s_raw, 0, 1)
    observed = truth & (rng.random(n) < detect)

    cells = pd.DataFrame({
        "cell_key": [f"sim{i}" for i in range(n)],
        "lon": base["lon"].to_numpy(), "lat": base["lat"].to_numpy(),
        "x": base["x"].to_numpy(), "y": base["y"].to_numpy(), "z": base["z"].to_numpy(),
        "px": px, "py": py, "state": "SIM",
        "n_reports": reported.astype(int), "is_pos": reported, "in_M": True,
        "test_n": np.where(sampled, 5.0, np.nan),
        "test_label": np.where(sampled, observed.astype(float), np.nan),
        "truth": truth,
    })
    obs_env = env + rng.normal(0, env_noise, env.shape)
    for j in range(3):
        cells[f"env{j + 1}"] = obs_env[:, j]
    xyz = cells[["x", "y", "z"]].to_numpy()
    kde = gaussian_kde_at(xyz, xyz[reported], np.full(int(reported.sum()), np.log(2.0)),
                          real_ds.cfg.kde_bandwidth_km)
    cells["effort_kde"] = kde / kde.max() if kde.max() > 0 else kde
    cells["effort"] = np.log(e_true) + rng.normal(0, proxy_sigma, n)
    cells["q"] = propensity(cells["effort"])

    cfg = replace(real_ds.cfg, min_survey_rows=1)
    ds = Dataset(cells=cells, feat_cols=["env1", "env2", "env3"], cfg=cfg, core_states=["SIM"],
                 notes={"seed": seed, "n_truth": int(truth.sum()), "n_reported": int(reported.sum()),
                        "n_sampled": int(sampled.sum())})
    ok_s = sampled
    sets = {
        "truth_all": (np.ones(n, bool), truth.astype(float)),
        "truth_unreported": (~reported, truth.astype(float)),
        "survey_sample": (ok_s, cells["test_label"].to_numpy(float)),
        "survey_unreported": (ok_s & ~reported, cells["test_label"].to_numpy(float)),
    }
    return ds, sets


def spatial_folds(ds: Dataset, k: int, block_km: float, seed: int):
    c = ds.cells
    b = block_ids(c["px"].to_numpy(), c["py"].to_numpy(), block_km)
    ub = np.unique(b)
    rng = np.random.default_rng(seed)
    assign = rng.permutation(len(ub)) % k
    lookup = dict(zip(ub, assign))
    return np.array([lookup[v] for v in b])


def run_one(real_ds: Dataset, seed: int, replicates=3, k_folds=4, n_trees=100, treatments=None,
            fold_block_km=100.0, scenario="confounded", cfg_overrides=None):
    ds, sets = make_virtual_dataset(real_ds, seed, **SCENARIOS[scenario])
    ds.cfg = replace(ds.cfg, n_trees=n_trees, seed=seed, **(cfg_overrides or {}))
    folds = spatial_folds(ds, k_folds, fold_block_km, seed)
    kw = {} if treatments is None else {"treatments": treatments}
    scores, diag = run_treatments(ds, replicates=replicates, folds=folds, **kw)
    ev = evaluate(ds, scores, sets, extra={("BASE_kde", "-"): ds.cells["effort_kde"].to_numpy(float)})
    ev["seed"] = seed
    ev["scenario"] = scenario
    return ev, diag, ds.notes


def summarise(results: pd.DataFrame, ref="random_bg", metric="auc"):
    """Mean metric per (treatment, model, set) and paired difference vs `ref`."""
    r = results.copy()
    if "scenario" not in r.columns:
        r["scenario"] = "all"
    piv = r.pivot_table(index=["scenario", "seed", "model", "set"], columns="treatment", values=metric)
    out = []
    for (scen, model, sname), g in piv.groupby(level=["scenario", "model", "set"]):
        for t in g.columns:
            if t == ref or t not in g or ref not in g:
                continue
            d = (g[t] - g[ref]).dropna()
            if len(d) == 0:
                continue
            out.append({"scenario": scen, "model": model, "set": sname, "treatment": t, "metric": metric,
                        "mean": float(g[t].mean()), "ref_mean": float(g[ref].mean()),
                        "mean_delta": float(d.mean()),
                        "se_delta": float(d.std(ddof=1) / np.sqrt(len(d))) if len(d) > 1 else np.nan,
                        "win_rate": float((d > 0).mean()), "n_seeds": int(len(d))})
    return pd.DataFrame(out)
