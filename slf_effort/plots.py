"""Figures (matplotlib, Agg backend; no display needed)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .background import LABELS
from .models import MODEL_LABELS

SET_LABELS = {
    "all": "All test cells", "reported_cells": "Cells with reports",
    "zero_report_cells": "Cells with no reports", "core_states": "Core states (PA/NJ)",
    "transfer_states": "Other states (transfer)",
    "truth_all": "All cells vs truth", "truth_unreported": "Unreported cells vs truth",
    "survey_sample": "Biased survey sample", "survey_unreported": "Survey, unreported cells",
}
_COL = ["#4c78a8", "#f58518", "#54a24b", "#e45756", "#b279a2", "#9d755d", "#7f7f7f"]


def fig_map(ds, path):
    c = ds.cells
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.scatter(c["px"], c["py"], s=4, c="#d0d0d0", label="Accessible area / test cells", lw=0)
    ok = c["test_label"].notna() & (c["test_n"].fillna(0) >= ds.cfg.min_survey_rows)
    a = ok & (c["test_label"] == 0)
    p = ok & (c["test_label"] == 1)
    ax.scatter(c.loc[a, "px"], c.loc[a, "py"], s=7, c="#4c78a8", alpha=.6, lw=0,
               label=f"Survey: not detected 2022-23 (n={int(a.sum())})")
    ax.scatter(c.loc[p, "px"], c.loc[p, "py"], s=7, c="#f58518", alpha=.8, lw=0,
               label=f"Survey: detected 2022-23 (n={int(p.sum())})")
    pos = c["is_pos"]
    ax.scatter(c.loc[pos, "px"], c.loc[pos, "py"], s=14, facecolors="none", edgecolors="#e45756",
               lw=.7, label=f"Training public-report cells (n={int(pos.sum())})")
    # clip the view to the bulk of the study region (a few far-away stray reports would otherwise stretch it)
    xs = pd.concat([c.loc[ok, "px"], c.loc[pos, "px"]])
    ys = pd.concat([c.loc[ok, "py"], c.loc[pos, "py"]])
    xlo, xhi = xs.quantile([0.005, 0.995])
    ylo, yhi = ys.quantile([0.005, 0.995])
    padx, pady = 0.05 * (xhi - xlo), 0.05 * (yhi - ylo)
    ax.set_xlim(xlo - padx, xhi + padx)
    ax.set_ylim(ylo - pady, yhi + pady)
    n_out = int((~((c["px"].between(xlo - padx, xhi + padx)) & (c["py"].between(ylo - pady, yhi + pady))) & (pos | ok)).sum())
    ax.set_xlabel("km east (approx.)" + (f"   [{n_out} far-away cells outside view]" if n_out else ""))
    ax.set_ylabel("km north (approx.)")
    ax.set_aspect("equal")
    ax.legend(fontsize=7, loc="lower right", frameon=False)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


SHORT = {
    "random_bg": "Random", "thin_bg": "Thinning", "kde_bg": "KDE-matched",
    "ewc_pa": "EWC-PA", "ewc_pa_ipw": "EWC-PA + IPW", "effort_cov": "Effort covariate",
    "abl_B": "Buffer only", "abl_E": "Env. exclusion only", "abl_W": "Effort weighting only",
    "abl_BE": "Buffer + env.", "abl_BW": "Buffer + effort", "abl_EW": "Env. + effort", "abl_BEW": "Buffer + env. + effort",
}
SCEN_LABELS = {"independent": "Effort independent\nof environment",
               "confounded": "Effort confounded\nwith environment",
               "confounded_strong": "Strongly concentrated\neffort",
               "adverse": "Effort highest where\nsuitability lowest"}


def fig_forest(deltas: pd.DataFrame, path, metric="auc", sets=None, ref_label="random background",
               treatments=None):
    d = deltas[deltas["metric"] == metric]
    if d.empty:
        return
    sets = sets or [s for s in SET_LABELS if s in set(d["set"])]
    models = [m for m in ("rf", "lr") if m in set(d["model"])]
    treats = treatments or [t for t in LABELS if t in set(d["treatment"])]
    col = (_COL + ["#17becf", "#bcbd22", "#8c564b"])
    h = 0.32 * len(sets) * (len(treats) + 1) + 2.2
    fig, axes = plt.subplots(1, len(models), figsize=(6.2 * len(models), h), sharey=True, squeeze=False)
    for ax, m in zip(axes[0], models):
        y = 0
        yt, yl = [], []
        for s in sets:
            for j, t in enumerate(treats):
                r = d[(d["model"] == m) & (d["set"] == s) & (d["treatment"] == t)]
                if not r.empty:
                    r = r.iloc[0]
                    ax.errorbar(r["delta"], y, xerr=[[r["delta"] - r["ci_lo"]], [r["ci_hi"] - r["delta"]]],
                                fmt="o", ms=5, color=col[j % len(col)], capsize=2.5, lw=1.4)
                y += 1
            yt.append(y - len(treats) / 2 - 0.5)
            yl.append(SET_LABELS.get(s, s).replace(" (", "\n("))
            y += 1
        ax.axvline(0, color="k", lw=1)
        ax.set_yticks(yt)
        ax.set_yticklabels(yl, fontsize=12)
        if ax is axes[0][0]:          # shared y-axis: invert once only
            ax.invert_yaxis()
        ax.set_title(MODEL_LABELS.get(m, m), fontsize=14, fontweight="bold")
        ax.set_xlabel(f"Change in {metric.upper()} vs {ref_label}\n(95% spatial-block bootstrap CI)", fontsize=12)
        ax.tick_params(axis="x", labelsize=11)
        ax.grid(axis="x", color="#e5e5e5", lw=.8)
        ax.set_axisbelow(True)
    handles = [plt.Line2D([], [], marker="o", ms=7, ls="", color=col[j % len(col)], label=SHORT.get(t, LABELS.get(t, t)))
               for j, t in enumerate(treats)]
    fig.legend(handles=handles, loc="lower center", ncol=min(len(treats), 4), fontsize=12, frameon=False)
    nrow = int(np.ceil(len(treats) / 4))
    fig.tight_layout(rect=(0, 0.035 + 0.035 * nrow * 6.5 / h, 1, 1))
    fig.savefig(path, dpi=300)
    plt.close(fig)


def fig_sim(summary: pd.DataFrame, path, set_name="truth_unreported"):
    d = summary[summary["set"] == set_name]
    if "metric" in d.columns:
        d = d[d["metric"] == "auc"]
    if d.empty:
        return
    order = [s for s in SCEN_LABELS if s in set(d["scenario"])]
    scens = order + [s for s in dict.fromkeys(d["scenario"]) if s not in order]
    models = [m for m in ("rf", "lr") if m in set(d["model"])]
    treats = [t for t in LABELS if t in set(d["treatment"])]
    fig, axes = plt.subplots(len(models), len(scens), figsize=(3.9 * len(scens), 3.9 * len(models)),
                             sharey=True, squeeze=False)
    for i, m in enumerate(models):
        for j, sc in enumerate(scens):
            ax = axes[i][j]
            r = d[(d["model"] == m) & (d["scenario"] == sc)].set_index("treatment")
            xs = np.arange(len(treats))
            vals = [r["mean_delta"].get(t, np.nan) for t in treats]
            err = [1.96 * r["se_delta"].get(t, np.nan) for t in treats]
            ax.bar(xs, vals, yerr=err, color=[_COL[k % len(_COL)] for k in range(len(treats))],
                   capsize=3, lw=0)
            ax.axhline(0, color="k", lw=1)
            ax.set_xticks(xs)
            ax.set_xticklabels([SHORT.get(t, t) for t in treats], fontsize=11, rotation=55, ha="right")
            ax.tick_params(axis="y", labelsize=11)
            ax.grid(axis="y", color="#e5e5e5", lw=.8)
            ax.set_axisbelow(True)
            if i == 0:
                ax.set_title(SCEN_LABELS.get(sc, sc), fontsize=12, fontweight="bold")
            if j == 0:
                ax.set_ylabel(f"{MODEL_LABELS.get(m, m)}\nchange in AUC vs random", fontsize=12)
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)


def fig_novelty(ds, pct, sets, path):
    """Environmental novelty of test cells relative to training presences, core vs transfer."""
    fig, ax = plt.subplots(figsize=(7, 4.2))
    bins = np.linspace(0, 1, 21)
    for name, colr in (("core_states", "#4c78a8"), ("transfer_states", "#f58518")):
        m = sets[name][0]
        ax.hist(np.clip(pct[m], 0, 1), bins=bins, alpha=.6, color=colr,
                label=f"{SET_LABELS[name]} (n={int(m.sum())})", density=True)
    ax.axvline(0.95, color="k", ls="--", lw=1)
    ax.text(0.945, ax.get_ylim()[1] * .92, "analog threshold", ha="right", fontsize=11)
    ax.set_xlabel("Environmental distance to training presences\n(percentile of presences' own distances)", fontsize=12)
    ax.set_ylabel("Density of test cells", fontsize=12)
    ax.tick_params(labelsize=11)
    ax.legend(fontsize=11, frameon=False, loc="upper left")
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)
