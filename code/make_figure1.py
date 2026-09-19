"""
Figure 1: the paper's headline result. Two panels, same x-axis (raw D),
showing the dissociation reported in Section 4.2: D correlates robustly
with K but not with I. Built directly from the same computation as
circularity_fix_experiment.py -- no numbers here are independent of what
is already verified and reported in the manuscript.

Run: python make_figure1.py
"""
import sys
import os

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats

sys.path.insert(0, r"C:\Users\HP\Documents\PCR6_RaterFusion_ADAS_2026\code")
from pcr6_fusion import renormalize_triplet, pairwise_mean_conflict

DATA_DIR = r"C:\Users\HP\Documents\Layered_Neutrosophic_HJMS\repo\experiments"
OUT_DIR = r"C:\Users\HP\Documents\PCR6_RaterFusion_ADAS_2026\paper\adas_template"

df = pd.read_csv(f"{DATA_DIR}\\exp_expert_filtered_long.csv")

rows = []
for hyp_id, group in df.groupby("hypothesis_id"):
    group = group.sort_values("expert_id")
    triplets = [renormalize_triplet(r.T, r.I, r.F) for r in group.itertuples()]
    D = float(np.std((group["T"] - group["F"]).to_numpy(), ddof=1))
    K = pairwise_mean_conflict(triplets)
    I = float(np.mean([t.I for t in triplets]))
    rows.append({"hypothesis_id": hyp_id, "D": D, "K": K, "I": I})

out = pd.DataFrame(rows).sort_values("hypothesis_id").reset_index(drop=True)

r_K, p_K = stats.pearsonr(out["D"], out["K"])
r_I, p_I = stats.pearsonr(out["D"], out["I"])

# verify against the manuscript's reported headline numbers before plotting
assert abs(r_K - 0.6882) < 0.001, r_K
assert abs(r_I - (-0.2134)) < 0.001, r_I

fig, axes = plt.subplots(1, 2, figsize=(9, 4), sharex=True)

for ax, col, r, p, label, color in [
    (axes[0], "K", r_K, p_K, r"Mean conjunctive conflict $\bar{K}$", "#c0392b"),
    (axes[1], "I", r_I, p_I, r"Mean ignorance $\bar{I}$", "#2471a3"),
]:
    ax.scatter(out["D"], out[col], s=28, color=color, alpha=0.8, edgecolors="black", linewidths=0.4)
    slope, intercept, *_ = stats.linregress(out["D"], out[col])
    xs = np.linspace(out["D"].min(), out["D"].max(), 50)
    ax.plot(xs, intercept + slope * xs, color=color, linewidth=1.2, linestyle="--")
    ax.set_xlabel(r"Classical proxy $D = \mathrm{SD}(T-F)$ (raw)")
    ax.set_ylabel(label)
    sig = "p < 0.001" if p < 0.001 else f"p = {p:.2f}"
    ax.set_title(f"r = {r:.2f}, {sig}", fontsize=10)
    ax.grid(alpha=0.25)

fig.tight_layout()
out_path = os.path.join(OUT_DIR, "figure1_D_vs_K_I.pdf")
fig.savefig(out_path)
print("saved:", out_path)
print(f"r_K={r_K:.4f} p_K={p_K:.4g}")
print(f"r_I={r_I:.4f} p_I={p_I:.4g}")
