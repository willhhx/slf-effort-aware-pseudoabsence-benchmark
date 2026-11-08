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


def fig_forest(deltas: pd.DataFrame, path, metric="auc", sets=None, ref_label="random background"):
    d = deltas[deltas["metric"] == metric]
    if d.empty:
        return
    sets = sets or [s for s in SET_LABELS if s in set(d["set"])]
    models = [m for m in ("rf", "lr") if m in set(d["model"])]
    treats = [t for t in LABELS if t in set(d["treatment"])]
    fig, axes = plt.subplots(1, len(models), figsize=(5.2 * len(models), 0.55 * len(sets) * len(treats) / 2 + 2),
                             sharey=True, squeeze=False)
    for ax, m in zip(axes[0], models):
        y = 0
        yt, yl = [], []
        for s in sets:
            for j, t in enumerate(treats):
                r = d[(d["model"] == m) & (d["set"] == s) & (d["treatment"] == t)]
                if r.empty:
                    y += 1
                    continue
                r = r.iloc[0]
                ax.errorbar(r["delta"], y, xerr=[[r["delta"] - r["ci_lo"]], [r["ci_hi"] - r["delta"]]],
                            fmt="o", ms=3.5, color=_COL[j % len(_COL)], capsize=2, lw=1)
                y += 1
            yt.append(y - len(treats) / 2 - 0.5)
            yl.append(SET_LABELS.get(s, s))
            y += 1
        ax.axvline(0, color="k", lw=.8)
        ax.set_yticks(yt)
        ax.set_yticklabels(yl, fontsize=8)
        ax.invert_yaxis()
        ax.set_title(MODEL_LABELS.get(m, m), fontsize=10)
        ax.set_xlabel(f"Change in {metric.upper()} vs {ref_label} (95% block-bootstrap CI)")
    handles = [plt.Line2D([], [], marker="o", ls="", color=_COL[j % len(_COL)], label=LABELS[t])
               for j, t in enumerate(treats)]
    fig.legend(handles=handles, loc="lower center", ncol=3, fontsize=7, frameon=False)
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    fig.savefig(path, dpi=200)
    plt.close(fig)


def fig_sim(summary: pd.DataFrame, path, set_name="truth_unreported"):
    d = summary[summary["set"] == set_name]
    if d.empty:
        return
    scens = list(dict.fromkeys(d["scenario"]))
    models = [m for m in ("rf", "lr") if m in set(d["model"])]
    treats = [t for t in LABELS if t in set(d["treatment"])]
    fig, axes = plt.subplots(len(models), len(scens), figsize=(3.4 * len(scens), 2.8 * len(models)),
                             sharey=True, squeeze=False)
    for i, m in enumerate(models):
        for j, sc in enumerate(scens):
            ax = axes[i][j]
            r = d[(d["model"] == m) & (d["scenario"] == sc)].set_index("treatment")
            xs = np.arange(len(treats))
            vals = [r["mean_delta"].get(t, np.nan) for t in treats]
            err = [1.96 * r["se_delta"].get(t, np.nan) for t in treats]
            ax.bar(xs, vals, yerr=err, color=[_COL[k % len(_COL)] for k in range(len(treats))],
                   capsize=2, lw=0)
            ax.axhline(0, color="k", lw=.8)
            ax.set_xticks(xs)
            ax.set_xticklabels([t.replace("_", "\n") for t in treats], fontsize=6)
            if i == 0:
                ax.set_title(sc.replace("_", " "), fontsize=9)
            if j == 0:
                ax.set_ylabel(f"{MODEL_LABELS.get(m, m)}\nchange in AUC vs random bg", fontsize=7)
    fig.suptitle(f"Virtual species: {SET_LABELS.get(set_name, set_name)}", fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)
