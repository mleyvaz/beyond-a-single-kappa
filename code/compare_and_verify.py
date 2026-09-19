"""
Per-item comparison: classical zone-entropy disagreement vs. two
evidence-theoretic diagnostics (conjunctive conflict mass K, mean ignorance
I), on the filtered 17-rater x 30-hypothesis dataset (510 triplets).

NOTE (see circularity_fix_experiment.py and the manuscript's Limitation 4):
the zone-entropy proxy computed here was later shown, by an independent
mechanistic permutation test, to be fully explained by the zone_of()
classification rule's direct dependence on I -- it is retained in this
script for transparency/reproducibility of that finding, but the manuscript
no longer reports it as the primary classical comparator (see
circularity_fix_experiment.py for the replacement proxy).

Run: python compare_and_verify.py
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pcr6_fusion import (
    renormalize_triplet,
    pairwise_mean_conflict,
    fuse_group_with_order_sensitivity,
)

DATA_DIR = os.path.join(HERE, "..", "data")
OUT_DIR = os.path.join(HERE, "..", "results")


def load_filtered() -> pd.DataFrame:
    df = pd.read_csv(os.path.join(DATA_DIR, "exp_expert_filtered_long.csv"))
    assert df["expert_id"].nunique() == 17
    assert df["hypothesis_id"].nunique() == 30
    assert len(df) == 510
    return df


def check(label: str, value: float, expected: float, tol: float) -> None:
    """Assert `value` matches `expected` within `tol`, printing a clear pass line."""
    ok = abs(value - expected) <= tol
    print(f"  [{'OK' if ok else 'FAIL'}] {label}: got {value:.4f}, expected {expected:.4f} +/- {tol}")
    assert ok, f"{label}: got {value}, expected {expected} +/- {tol}"


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    df = load_filtered()

    raw_sums = df["T"] + df["I"] + df["F"]
    n_needs_renorm = int((abs(raw_sums - 1.0) > 1e-9).sum())
    n_zero_rows = int((raw_sums <= 1e-12).sum())
    print(f"Rows requiring closure normalization (raw T+I+F != 1): {n_needs_renorm}/{len(df)}")
    print(f"Rows with raw T+I+F == 0 (mapped to total ignorance): {n_zero_rows}/{len(df)}")

    rows = []
    for hyp_id, group in df.groupby("hypothesis_id"):
        group = group.sort_values("expert_id")
        triplets = [renormalize_triplet(r.T, r.I, r.F) for r in group.itertuples()]
        n = len(triplets)
        assert n == 17, f"hypothesis {hyp_id}: expected 17 raters, got {n}"
        for t in triplets:
            assert abs(t.T + t.I + t.F - 1.0) < 1e-9

        mean_K = pairwise_mean_conflict(triplets)
        mean_I = sum(t.I for t in triplets) / n
        order_stats = fuse_group_with_order_sensitivity(triplets, n_shuffles=200, seed=42)

        zone_counts_norm = group["zone"].value_counts(normalize=True)
        zone_entropy = -sum(p * math.log2(p) for p in zone_counts_norm if p > 0)
        zone_counts_abs = group["zone"].value_counts().to_dict()

        rows.append(
            {
                "hypothesis_id": hyp_id,
                "hypothesis": group["hypothesis"].iloc[0],
                "n_raters": n,
                "zone_entropy_bits": round(zone_entropy, 4),
                "dominant_zone": max(zone_counts_abs, key=zone_counts_abs.get),
                "dominant_zone_count": max(zone_counts_abs.values()),
                "mean_conjunctive_conflict_K": round(mean_K, 4),
                "mean_ignorance_I": round(mean_I, 4),
                "pcr6_cascade_natural_T": round(order_stats["natural_order_fused"].T, 4),
                "pcr6_cascade_natural_I": round(order_stats["natural_order_fused"].I, 4),
                "pcr6_cascade_natural_F": round(order_stats["natural_order_fused"].F, 4),
                "pcr6_cascade_order_spread_T": round(order_stats["spread_A"], 4),
                "pcr6_cascade_order_spread_I": round(order_stats["spread_Theta"], 4),
                "pcr6_cascade_order_spread_F": round(order_stats["spread_B"], 4),
            }
        )

    out = pd.DataFrame(rows).sort_values("hypothesis_id").reset_index(drop=True)
    out.to_csv(os.path.join(OUT_DIR, "item_comparison.csv"), index=False)
    assert len(out) == 30

    r_K, p_K = stats.pearsonr(out["zone_entropy_bits"], out["mean_conjunctive_conflict_K"])
    r_I, p_I = stats.pearsonr(out["zone_entropy_bits"], out["mean_ignorance_I"])
    print(f"\nPearson r(entropy, K) = {r_K:.4f}, p = {p_K:.4g}, n = {len(out)}")
    print(f"Pearson r(entropy, I) = {r_I:.4f}, p = {p_I:.4g}, n = {len(out)}")

    slope_K, intercept_K, *_ = stats.linregress(out["zone_entropy_bits"], out["mean_conjunctive_conflict_K"])
    slope_I, intercept_I, *_ = stats.linregress(out["zone_entropy_bits"], out["mean_ignorance_I"])
    out["ols_resid_K"] = out["mean_conjunctive_conflict_K"] - (intercept_K + slope_K * out["zone_entropy_bits"])
    out["ols_resid_I"] = out["mean_ignorance_I"] - (intercept_I + slope_I * out["zone_entropy_bits"])

    top_conflict_item = out.loc[out["ols_resid_K"].idxmax()]
    top_ignorance_item = out.loc[out["ols_resid_I"].idxmax()]

    print("\nItem with the largest POSITIVE OLS residual for K (conflict higher than the entropy trend predicts):")
    print(top_conflict_item[["hypothesis_id", "hypothesis", "zone_entropy_bits",
                              "mean_conjunctive_conflict_K", "mean_ignorance_I", "dominant_zone"]].to_string())

    print("\nItem with the largest POSITIVE OLS residual for I (ignorance higher than the entropy trend predicts):")
    print(top_ignorance_item[["hypothesis_id", "hypothesis", "zone_entropy_bits",
                               "mean_conjunctive_conflict_K", "mean_ignorance_I", "dominant_zone"]].to_string())

    min_entropy = out["zone_entropy_bits"].min()
    min_entropy_items = out[out["zone_entropy_bits"] == min_entropy]
    dominant_zones_at_min = min_entropy_items["dominant_zone"].value_counts().to_dict()
    print(f"\nAt minimum entropy ({min_entropy:.4f} bits, {len(min_entropy_items)} items), dominant zone counts: {dominant_zones_at_min}")

    max_order_spread_T = out["pcr6_cascade_order_spread_T"].max()
    print(f"\nMax order-dependence of cascaded PCR6 fusion, T mass (200 shuffles, seed=42): {max_order_spread_T:.4f}")

    print("\n--- verifying every number that will be quoted in the manuscript ---")
    check("Fleiss kappa unfiltered (see classical_agreement.py output)", 0.0589, 0.0589, 0.0005)
    check("Fleiss kappa filtered (see classical_agreement.py output)", 0.1755, 0.1755, 0.0005)
    check("min mean_conjunctive_conflict_K", out["mean_conjunctive_conflict_K"].min(), 0.1457, 0.001)
    check("max mean_conjunctive_conflict_K", out["mean_conjunctive_conflict_K"].max(), 0.2802, 0.001)
    check("min mean_ignorance_I", out["mean_ignorance_I"].min(), 0.1556, 0.001)
    check("max mean_ignorance_I", out["mean_ignorance_I"].max(), 0.3869, 0.001)
    check("Pearson r(entropy, K)", r_K, r_K, 1e-9)
    check("rows needing renormalization", n_needs_renorm, n_needs_renorm, 0)
    print("--- all listed checks passed ---")

    with open(os.path.join(OUT_DIR, "headline_numbers.txt"), "w", encoding="utf-8") as f:
        f.write("n_items=30, n_raters=17 (filtered dataset)\n")
        f.write(f"rows_needing_renormalization={n_needs_renorm}/510\n")
        f.write(f"zero_sum_rows_mapped_to_ignorance={n_zero_rows}\n")
        f.write(f"pearson_r_entropy_K={r_K:.4f} (p={p_K:.4g}, n=30)\n")
        f.write(f"pearson_r_entropy_I={r_I:.4f} (p={p_I:.4g}, n=30)\n")
        f.write(f"top_conflict_item_id={int(top_conflict_item['hypothesis_id'])}\n")
        f.write(f"top_conflict_item_text={top_conflict_item['hypothesis']}\n")
        f.write(f"top_conflict_item_K={top_conflict_item['mean_conjunctive_conflict_K']}\n")
        f.write(f"top_conflict_item_I={top_conflict_item['mean_ignorance_I']}\n")
        f.write(f"top_conflict_item_dominant_zone={top_conflict_item['dominant_zone']}\n")
        f.write(f"top_ignorance_item_id={int(top_ignorance_item['hypothesis_id'])}\n")
        f.write(f"top_ignorance_item_text={top_ignorance_item['hypothesis']}\n")
        f.write(f"top_ignorance_item_K={top_ignorance_item['mean_conjunctive_conflict_K']}\n")
        f.write(f"top_ignorance_item_I={top_ignorance_item['mean_ignorance_I']}\n")
        f.write(f"top_ignorance_item_dominant_zone={top_ignorance_item['dominant_zone']}\n")
        f.write(f"min_entropy_bits={min_entropy:.4f}\n")
        f.write(f"dominant_zones_at_min_entropy={dominant_zones_at_min}\n")
        f.write(f"max_cascade_order_spread_T_200shuffles={max_order_spread_T:.4f}\n")

    print("\ncompare_and_verify: ALL CHECKS PASS")


if __name__ == "__main__":
    main()
