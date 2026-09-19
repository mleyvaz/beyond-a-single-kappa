"""
Verification script: confirms, by direct computation, the manuscript's
Section 4.2 claim that the two illustrative items (30 for conflict, 21 for
ignorance) are the largest positive OLS residuals against each variable's
fitted linear trend on the CURRENT primary proxy D = SD(T-F).

CORRECTED 2026-09-19 (post-REVIEW_CODEX_v0.3 self-check): this script
originally computed D on RENORMALIZED T,F, the same bug as the first version
of circularity_fix_experiment.py -- silently reintroducing I through the
renormalization denominator. On the raw values, item 21 replaces item 8 as
the top ignorance residual, and the K/I roles in Section 4.2 reverse
entirely (see circularity_fix_experiment.py's module docstring for the full
before/after numbers). This script now computes D on raw, unrenormalized
T,F only, matching circularity_fix_experiment.py.

Run: python item_selection_D_based.py
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, r"C:\Users\HP\Documents\PCR6_RaterFusion_ADAS_2026\code")
from pcr6_fusion import renormalize_triplet, pairwise_mean_conflict

DATA_DIR = r"C:\Users\HP\Documents\Layered_Neutrosophic_HJMS\repo\experiments"
OUT_DIR = r"C:\Users\HP\Documents\PCR6_RaterFusion_ADAS_2026\results"


def load_filtered() -> pd.DataFrame:
    df = pd.read_csv(f"{DATA_DIR}\\exp_expert_filtered_long.csv")
    assert df["expert_id"].nunique() == 17
    assert df["hypothesis_id"].nunique() == 30
    assert len(df) == 510
    return df


def main() -> None:
    df = load_filtered()

    rows = []
    for hyp_id, group in df.groupby("hypothesis_id"):
        group = group.sort_values("expert_id")
        triplets = [renormalize_triplet(r.T, r.I, r.F) for r in group.itertuples()]
        assert len(triplets) == 17
        d_vals = (group["T"] - group["F"]).to_numpy()  # raw, unrenormalized -- see module docstring
        D = float(np.std(d_vals, ddof=1))
        mean_K = pairwise_mean_conflict(triplets)
        mean_I = float(np.mean([t.I for t in triplets]))
        rows.append(
            {
                "hypothesis_id": hyp_id,
                "hypothesis": group["hypothesis"].iloc[0],
                "D": D,
                "mean_K": mean_K,
                "mean_I": mean_I,
            }
        )

    out = pd.DataFrame(rows).sort_values("hypothesis_id").reset_index(drop=True)
    assert len(out) == 30

    slope_K, intercept_K, *_ = stats.linregress(out["D"], out["mean_K"])
    slope_I, intercept_I, *_ = stats.linregress(out["D"], out["mean_I"])
    out["ols_resid_K_on_D"] = out["mean_K"] - (intercept_K + slope_K * out["D"])
    out["ols_resid_I_on_D"] = out["mean_I"] - (intercept_I + slope_I * out["D"])

    top_conflict_item = out.loc[out["ols_resid_K_on_D"].idxmax()]
    top_ignorance_item = out.loc[out["ols_resid_I_on_D"].idxmax()]

    print("Item with the largest POSITIVE OLS residual for K on D (conflict higher than the D trend predicts):")
    print(top_conflict_item[["hypothesis_id", "hypothesis", "D", "mean_K", "mean_I", "ols_resid_K_on_D"]].to_string())

    print("\nItem with the largest POSITIVE OLS residual for I on D (ignorance higher than the D trend predicts):")
    print(top_ignorance_item[["hypothesis_id", "hypothesis", "D", "mean_K", "mean_I", "ols_resid_I_on_D"]].to_string())

    # --- checks anchoring this script to the manuscript's Section 4.2 claim ---
    assert int(top_conflict_item["hypothesis_id"]) == 30, (
        "Manuscript Section 4.2 claims item 30 is the top D-based conflict residual; "
        f"got item {int(top_conflict_item['hypothesis_id'])} instead."
    )
    assert int(top_ignorance_item["hypothesis_id"]) == 21, (
        "Manuscript Section 4.2 claims item 21 is the top D-based ignorance residual; "
        f"got item {int(top_ignorance_item['hypothesis_id'])} instead."
    )
    print("\n[OK] Confirms manuscript Section 4.2: items 30 (conflict) and 21 (ignorance) are indeed "
          "the top OLS residuals against the raw D trend.")

    out.to_csv(f"{OUT_DIR}\\item_selection_D_based.csv", index=False)
    with open(f"{OUT_DIR}\\item_selection_D_based.txt", "w", encoding="utf-8") as f:
        f.write(f"top_conflict_item_id={int(top_conflict_item['hypothesis_id'])}\n")
        f.write(f"top_conflict_item_D={top_conflict_item['D']:.4f}\n")
        f.write(f"top_conflict_item_K={top_conflict_item['mean_K']:.4f}\n")
        f.write(f"top_conflict_item_ols_resid_K_on_D={top_conflict_item['ols_resid_K_on_D']:.4f}\n")
        f.write(f"top_ignorance_item_id={int(top_ignorance_item['hypothesis_id'])}\n")
        f.write(f"top_ignorance_item_D={top_ignorance_item['D']:.4f}\n")
        f.write(f"top_ignorance_item_I={top_ignorance_item['mean_I']:.4f}\n")
        f.write(f"top_ignorance_item_ols_resid_I_on_D={top_ignorance_item['ols_resid_I_on_D']:.4f}\n")


if __name__ == "__main__":
    main()
