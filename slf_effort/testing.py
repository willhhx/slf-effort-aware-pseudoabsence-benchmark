"""Synthetic data in the lydemapr schema (for self-tests and unit tests only)."""
import numpy as np
import pandas as pd

STEP_LON = 0.1176470588
STEP_LAT = 0.0900900901


def synthetic_lyde(seed=0, n_cells=500):
    rng = np.random.default_rng(seed)
    gi, gj = np.meshgrid(np.arange(30), np.arange(30))
    cand = np.column_stack([gi.ravel(), gj.ravel()])
    sel = cand[rng.choice(len(cand), n_cells, replace=False)]
    clon = -77.0 + sel[:, 0] * STEP_LON
    clat = 39.4 + sel[:, 1] * STEP_LAT
    olon, olat = -75.65, 40.45
    dist = 111.0 * np.hypot((clon - olon) * np.cos(np.radians(40.4)), clat - olat)
    effort = rng.gamma(2.0, 1.0, n_cells)
    state = np.where(clat > 41.0, "NY", np.where(clon < -75.2, "PA", "NJ"))

    parts = []
    for by in range(2015, 2024):
        inv = dist < 25.0 * (by - 2014) * rng.uniform(0.8, 1.2, n_cells)
        if by >= 2018:                       # public reports: presences only
            cnt = np.where(inv, rng.poisson(1.0 + 1.5 * effort * (by - 2017)), 0)
            ci = np.repeat(np.arange(n_cells), cnt)
            est = rng.choice([True, False, None], size=len(ci), p=[0.6, 0.2, 0.2])
            parts.append(pd.DataFrame({"ci": ci, "bio_year": by, "pres": True, "est": est,
                                       "method": "individual_reporting"}))
        surveyed = rng.random(n_cells) < 0.5      # professional surveys: outcomes recorded
        cnt = np.where(surveyed, 1 + rng.poisson(4, n_cells), 0)
        ci = np.repeat(np.arange(n_cells), cnt)
        pres = inv[ci] & (rng.random(len(ci)) < 0.55)
        est = np.where(pres, rng.random(len(ci)) < 0.5, False)
        parts.append(pd.DataFrame({"ci": ci, "bio_year": by, "pres": pres, "est": est,
                                   "method": "field_survey/management"}))
    d = pd.concat(parts, ignore_index=True)
    out = pd.DataFrame({
        "year": d["bio_year"],
        "bio_year": d["bio_year"],
        "latitude": clat[d["ci"]] + rng.uniform(-0.04, 0.04, len(d)),
        "longitude": clon[d["ci"]] + rng.uniform(-0.05, 0.05, len(d)),
        "state": state[d["ci"]],
        "lyde_present": d["pres"].map({True: "TRUE", False: "FALSE"}),
        "lyde_established": d["est"].map({True: "TRUE", False: "FALSE"}),   # None -> NaN
        "collection_method": d["method"],
        "rounded_longitude_10k": clon[d["ci"]],
        "rounded_latitude_10k": clat[d["ci"]],
    })
    return out


def write_synthetic_lyde(path, seed=0, n_cells=500):
    synthetic_lyde(seed, n_cells).to_csv(path, index=False)
    return path
