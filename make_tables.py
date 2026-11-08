#!/usr/bin/env python
"""Turn the result CSVs into manuscript-ready Markdown tables.

    python make_tables.py --real results/real --sim results/simulation --out results/paper_tables.md
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from slf_effort.background import LABELS
from slf_effort.models import MODEL_LABELS
from slf_effort.plots import SET_LABELS


def _cell(v):
    if isinstance(v, float):
        if np.isnan(v):
            return ""
        if v == int(v) and abs(v) >= 10:
            return str(int(v))
    return str(v)


def md(df: pd.DataFrame) -> str:
    cols = [str(c) for c in df.columns]
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for _, r in df.iterrows():
        lines.append("| " + " | ".join(_cell(v) for v in r) + " |")
    return "\n".join(lines)


def fmt_ci(r, nd=3):
    return f"{r['delta']:+.{nd}f} [{r['ci_lo']:+.{nd}f}, {r['ci_hi']:+.{nd}f}]"


def name(t):
    return LABELS.get(t, t)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--real")
    ap.add_argument("--sim")
    ap.add_argument("--out", default="paper_tables.md")
    a = ap.parse_args(argv)
    out = []
    if a.real:
        t1 = pd.read_csv(os.path.join(a.real, "table1_data_summary.csv"))
        out += ["## Table 1. Data summary", md(t1), ""]
        ev = pd.read_csv(os.path.join(a.real, "metrics_by_stratum.csv"))
        sets = [s for s in SET_LABELS if s in set(ev["set"])]
        for metric, title in (("auc", "AUC"), ("ap", "Average precision"),
                              ("fpr@20", "False-positive rate at 20% alert budget (lower is better)"),
                              ("sens@20", "Sensitivity at 20% alert budget")):
            if metric not in ev.columns:
                continue
            p = ev.pivot_table(index=["model", "treatment"], columns="set", values=metric)[sets].round(3)
            p = p.reset_index()
            p["model"] = p["model"].map(lambda m: MODEL_LABELS.get(m, "-"))
            p["treatment"] = p["treatment"].map(name)
            p = p.rename(columns=SET_LABELS)
            out += [f"## {title} by stratum (test cells)", md(p), ""]
        for fn, title in (("paired_vs_random_background.csv", "vs random background"),
                          ("paired_vs_report_density_baseline.csv", "vs report-density (KDE) baseline")):
            f = os.path.join(a.real, fn)
            if not os.path.exists(f):
                continue
            d = pd.read_csv(f)
            for metric in ("auc", "fpr"):
                x = d[d["metric"] == metric].copy()
                if x.empty:
                    continue
                x["cell"] = x.apply(fmt_ci, axis=1)
                p = x.pivot_table(index=["model", "treatment"], columns="set", values="cell", aggfunc="first")
                p = p[[s for s in SET_LABELS if s in p.columns]].reset_index()
                p["model"] = p["model"].map(lambda m: MODEL_LABELS.get(m, m))
                p["treatment"] = p["treatment"].map(name)
                p = p.rename(columns=SET_LABELS)
                out += [f"## Change in {metric.upper()} {title} (95% spatial-block bootstrap CI)", md(p), ""]
    if a.sim:
        s = pd.read_csv(os.path.join(a.sim, "sim_summary.csv"))
        for metric in ("auc",):
            for sname in ("truth_unreported", "survey_sample"):
                x = s[(s["metric"] == metric) & (s["set"] == sname)].copy()
                if x.empty:
                    continue
                x["cell"] = x.apply(lambda r: f"{r['mean_delta']:+.3f} ± {1.96 * r['se_delta']:.3f} (wins {r['win_rate']:.0%})", axis=1)
                p = x.pivot_table(index=["scenario", "model"], columns="treatment", values="cell", aggfunc="first")
                p = p[[t for t in LABELS if t in p.columns]].reset_index()
                p["model"] = p["model"].map(lambda m: MODEL_LABELS.get(m, m))
                p = p.rename(columns=name)
                n = int(x["n_seeds"].max())
                out += [f"## Virtual species: change in {metric.upper()} vs random background, {SET_LABELS.get(sname, sname)} "
                        f"(mean ± 1.96 SE over {n} species; win rate)", md(p), ""]
    with open(a.out, "w") as f:
        f.write("\n".join(out))
    print("wrote", a.out)


if __name__ == "__main__":
    main()
