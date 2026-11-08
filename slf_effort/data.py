"""Load lydemapr (lyde.csv) and build the analysis dataset.

Design (no label leakage):
  * Training data  = PUBLIC reports (collection_method == individual_reporting) that
    are positive, in the training bio-years. These are presence-only.
  * Accessible area M = 10-km cells with ANY record (public or survey, present or
    absent) up to the last training bio-year. Only cell LOCATIONS are used, never
    survey outcomes, and nothing after the training period.
  * Test data = PROFESSIONAL survey rows (field_survey/management) in the test
    bio-years, aggregated per 10-km cell (label = any detection).
"""
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Sequence

import numpy as np
import pandas as pd

from .geo import gaussian_kde_at, local_xy, nearest_distance, to_xyz

REQUIRED_COLS = [
    "bio_year", "state", "lyde_present", "lyde_established", "collection_method",
    "rounded_longitude_10k", "rounded_latitude_10k", "latitude", "longitude",
]
STATE_FIX = {"Indiana": "IN"}


@dataclass
class Config:
    train_years: tuple = (2019, 2020, 2021)   # bio_year
    test_years: tuple = (2022, 2023)          # bio_year
    target: str = "present"                   # "present" or "established"
    region_km: float = 250.0                  # keep cells within this distance of a training report
    min_survey_rows: int = 3                  # min survey records for a test cell to count
    kde_bandwidth_km: float = 20.0
    buffer_km: float = 50.0                   # geographic exclusion around training positives
    thin_km: float = 30.0                     # block size for spatial thinning of positives
    bg_ratio: float = 3.0                     # background points per positive (before caps)
    max_bg_frac: float = 0.6                  # never use more than this fraction of M as background
    env_k: int = 5                            # k for environmental-similarity exclusion
    env_quantile: float = 0.5                 # exclusion strictness (higher = stricter)
    effort_alpha: float = 1.0                 # exponent on propensity for pseudo-absence sampling
    replicates: int = 10                      # background redraws averaged per treatment
    n_trees: int = 200
    n_jobs: int = -1
    seed: int = 20261107
    block_km: float = 50.0                    # spatial block size for bootstrap
    bootstrap: int = 200
    core_state_share: float = 0.05            # states with >= this share of training reports are "core"
    alert_fracs: tuple = (0.1, 0.2, 0.3)
    alert_primary: float = 0.2

    def to_dict(self):
        return asdict(self)


@dataclass
class Dataset:
    cells: pd.DataFrame
    feat_cols: List[str]
    cfg: Config
    core_states: List[str] = field(default_factory=list)
    origin: Optional[tuple] = None
    notes: Dict[str, object] = field(default_factory=dict)


def _as_bool(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip().str.upper().eq("TRUE")


def load_lyde(path: str) -> pd.DataFrame:
    head = pd.read_csv(path, nrows=0).columns
    missing = [c for c in REQUIRED_COLS if c not in head]
    if missing:
        raise ValueError(f"{path} is missing required columns: {missing}. "
                         "Use the full lyde.csv from Zenodo (not lyde_10k.csv).")
    df = pd.read_csv(path, usecols=REQUIRED_COLS, low_memory=False)
    n0 = len(df)
    df = df[df["lyde_present"].notna()].copy()
    df = df[df["rounded_longitude_10k"].notna() & df["rounded_latitude_10k"].notna()].copy()
    df["present"] = _as_bool(df["lyde_present"])
    df["established"] = _as_bool(df["lyde_established"])
    df["state"] = df["state"].astype(str).str.strip().replace(STATE_FIX)
    df["method"] = np.where(df["collection_method"].eq("individual_reporting"), "public", "survey")
    df["lon_c"] = df["rounded_longitude_10k"].round(5)
    df["lat_c"] = df["rounded_latitude_10k"].round(5)
    df["cell_key"] = df["lon_c"].map("{:.5f}".format) + "_" + df["lat_c"].map("{:.5f}".format)
    df.attrs["dropped_rows"] = int(n0 - len(df))
    return df


def propensity(effort) -> np.ndarray:
    """Reporting propensity in [0.05, 1] from an effort proxy (percentile rank)."""
    r = pd.Series(np.asarray(effort, dtype=float)).rank(pct=True, method="average").to_numpy()
    return 0.05 + 0.95 * r


def _zscore(a: np.ndarray) -> np.ndarray:
    sd = np.nanstd(a)
    return (a - np.nanmean(a)) / (sd if sd > 0 else 1.0)


def cell_key_from(lon, lat):
    lon = np.round(np.asarray(lon, dtype=float), 5)
    lat = np.round(np.asarray(lat, dtype=float), 5)
    return pd.Series(lon).map("{:.5f}".format) + "_" + pd.Series(lat).map("{:.5f}".format)


def build_dataset(df: pd.DataFrame, cfg: Config, covariates: Optional[pd.DataFrame] = None,
                  env_cols: Optional[Sequence[str]] = None,
                  effort_cols: Optional[Sequence[str]] = None,
                  add_origin: bool = True) -> Dataset:
    if cfg.target not in ("present", "established"):
        raise ValueError("cfg.target must be 'present' or 'established'")
    flag = cfg.target
    train_end = max(cfg.train_years)
    if min(cfg.test_years) <= train_end:
        raise ValueError("test_years must come strictly after train_years")

    g = df.groupby("cell_key", sort=True)
    cells = g.agg(lon=("lon_c", "first"), lat=("lat_c", "first")).reset_index()
    state_mode = g["state"].agg(lambda s: s.value_counts().index[0])
    cells["state"] = cells["cell_key"].map(state_mode)

    pub_tr = df[(df["method"] == "public") & df[flag] & df["bio_year"].isin(cfg.train_years)]
    nrep = pub_tr.groupby("cell_key").size()
    cells["n_reports"] = cells["cell_key"].map(nrep).fillna(0).astype(int)
    cells["is_pos"] = cells["n_reports"] > 0

    m_keys = df.loc[df["bio_year"] <= train_end, "cell_key"].unique()
    cells["in_M"] = cells["cell_key"].isin(m_keys)

    test = df[(df["method"] == "survey") & df["bio_year"].isin(cfg.test_years)]
    tg = test.groupby("cell_key").agg(test_n=(flag, "size"), test_label=(flag, "max"))
    cells = cells.merge(tg, left_on="cell_key", right_index=True, how="left")
    cells["test_label"] = cells["test_label"].astype(float)

    xyz = to_xyz(cells["lon"], cells["lat"])
    cells[["x", "y", "z"]] = xyz
    cells["px"], cells["py"] = local_xy(cells["lon"], cells["lat"])

    # data-derived origin of the invasion: median location of earliest detections
    early = df[df["present"] & (df["bio_year"] <= 2015)]
    if len(early) == 0:
        first_year = df.loc[df["present"], "bio_year"].min()
        early = df[df["present"] & (df["bio_year"] == first_year)]
    origin = (float(early["lon_c"].median()), float(early["lat_c"].median()))
    cells["dist_origin_km"] = nearest_distance(xyz, to_xyz([origin[0]], [origin[1]]))

    # study region: within region_km of any training positive cell
    pos_xyz = xyz[cells["is_pos"].to_numpy()]
    if len(pos_xyz) == 0:
        raise ValueError("No training-period positive public reports found.")
    cells["dist_pos_km"] = nearest_distance(xyz, pos_xyz)
    keep = (cells["in_M"] | cells["test_n"].notna()) & (cells["dist_pos_km"] <= cfg.region_km)
    dom = cells[keep].reset_index(drop=True)
    dxyz = dom[["x", "y", "z"]].to_numpy()

    # KDE of training reports (log-weighted so one busy cell cannot dominate)
    ppos = dom["is_pos"].to_numpy()
    kde = gaussian_kde_at(dxyz, dxyz[ppos], np.log1p(dom.loc[ppos, "n_reports"].to_numpy()),
                          cfg.kde_bandwidth_km)
    dom["effort_kde"] = kde / kde.max() if kde.max() > 0 else kde

    notes: Dict[str, object] = {"dropped_rows_missing_present": df.attrs.get("dropped_rows", 0)}

    # optional external covariates
    if covariates is not None:
        cov = covariates.copy()
        if not {"lon", "lat"}.issubset(cov.columns):
            raise ValueError("covariates file needs 'lon' and 'lat' columns (cell centroids).")
        cov["cell_key"] = cell_key_from(cov["lon"], cov["lat"]).to_numpy()
        use = list(dict.fromkeys(list(env_cols or []) + list(effort_cols or [])))
        miss = [c for c in use if c not in cov.columns]
        if miss:
            raise ValueError(f"covariate columns not found: {miss}")
        cov = cov[["cell_key"] + use].drop_duplicates("cell_key")
        dom = dom.merge(cov, on="cell_key", how="left")
        bad = dom[use].isna().any(axis=1) if use else pd.Series(False, index=dom.index)
        notes["cells_dropped_missing_covariates"] = int(bad.sum())
        notes["positives_dropped_missing_covariates"] = int((bad & dom["is_pos"]).sum())
        dom = dom[~bad].reset_index(drop=True)

    if env_cols:
        feat_cols = list(env_cols) + (["dist_origin_km"] if add_origin else [])
    else:
        feat_cols = ["dist_origin_km", "lon", "lat"]

    if effort_cols:
        dom["effort"] = np.nanmean(np.column_stack([_zscore(dom[c].to_numpy(float))
                                                    for c in effort_cols]), axis=1)
        notes["effort_source"] = "external:" + ",".join(effort_cols)
    else:
        dom["effort"] = dom["effort_kde"]
        notes["effort_source"] = "kde_of_training_reports (stand-in; add population/road covariates for real effort)"
    dom["q"] = propensity(dom["effort"])

    share = pub_tr["state"].value_counts(normalize=True)
    core = list(share[share >= cfg.core_state_share].index)
    return Dataset(cells=dom, feat_cols=feat_cols, cfg=cfg, core_states=core,
                   origin=origin, notes=notes)


def real_eval_sets(ds: Dataset, min_rows: Optional[int] = None):
    """name -> (boolean mask over ds.cells, label vector over ds.cells)."""
    c = ds.cells
    mr = ds.cfg.min_survey_rows if min_rows is None else min_rows
    ok = (c["test_n"].fillna(0).to_numpy() >= mr) & c["test_label"].notna().to_numpy()
    y = c["test_label"].to_numpy(float)
    rep = c["n_reports"].to_numpy() > 0
    core = c["state"].isin(ds.core_states).to_numpy()
    return {
        "all": (ok, y),
        "reported_cells": (ok & rep, y),
        "zero_report_cells": (ok & ~rep, y),
        "core_states": (ok & core, y),
        "transfer_states": (ok & ~core, y),
    }


def data_summary(df: pd.DataFrame, ds: Dataset) -> pd.DataFrame:
    """Table 1 material: rows, cells and positivity by method and period."""
    cfg = ds.cfg
    period = np.where(df["bio_year"].isin(cfg.train_years), "train",
                      np.where(df["bio_year"].isin(cfg.test_years), "test", "other"))
    t = df.assign(period=period).groupby(["method", "period"]).agg(
        rows=("present", "size"), cells=("cell_key", "nunique"),
        pct_present=("present", lambda s: round(100 * s.mean(), 1)))
    t = t.reset_index()
    c = ds.cells
    ok = real_eval_sets(ds)
    extra = []
    for name, (m, y) in ok.items():
        extra.append({"method": "analysis", "period": f"test cells: {name}",
                      "rows": int(m.sum()), "cells": int(m.sum()),
                      "pct_present": round(100 * float(np.nanmean(y[m])), 1) if m.any() else np.nan})
    extra.append({"method": "analysis", "period": "training positive cells",
                  "rows": int(c["n_reports"].sum()), "cells": int(c["is_pos"].sum()), "pct_present": 100.0})
    extra.append({"method": "analysis", "period": "accessible-area cells (M)",
                  "rows": np.nan, "cells": int(c["in_M"].sum()), "pct_present": np.nan})
    return pd.concat([t, pd.DataFrame(extra)], ignore_index=True)
