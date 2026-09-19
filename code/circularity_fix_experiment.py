"""
Circularity-fix experiment, precommitted design (per unanimous 5-model
OpenRouter panel consulted 2026-09-19 on reviews/REVIEW_GEMINI_v0.2.md's
Limitation 4 finding). This design is fixed BEFORE looking at any of its own
results, to avoid choosing whichever variant happens to "work."

Two independent things are computed, both reported honestly regardless of
outcome:

(A) A classical disagreement proxy that never touches I or zone_of:
    D_j = sample SD (ddof=1) of (T_i - F_i) over item j's 17 RAW,
    pre-normalization rater values (0-1 rescaled elicitation, not divided
    by T+I+F). Correlated (Pearson + Spearman) against mean_K and mean_I
    (both computed on renormalized triplets, since K and I require a
    valid BBA -- see compare_and_verify.py), n=30.

    CORRECTED 2026-09-19 (third adversarial pass, REVIEW_CODEX_v0.3.md):
    an earlier version of this script computed D on RENORMALIZED T,F
    (i.e. D = SD((T-F)/(T+I+F))), which silently reintroduces I into the
    denominator -- the exact same class of circularity this experiment
    exists to rule out, just relocated rather than removed. Verified by
    direct comparison: D on renormalized triplets correlates with I
    (Pearson r=-0.60, p=0.0005) and only weakly with K (r=0.38, p=0.039,
    not Spearman-robust); D on genuinely raw T,F flips this completely --
    it correlates robustly with K (Pearson r=0.69, p<0.0001; Spearman
    rho=0.63, p=0.0002) and NOT with I (Pearson r=-0.21, p=0.26; Spearman
    rho=-0.32, p=0.08). The raw version is the one that actually matches
    the precommitted design (the 5-model panel's proposals -- SD of T-F,
    Gini mean difference, discretized entropy of T/(T+F) -- were all
    stated directly on raw T,F, with no renormalization step mentioned).
    This script now computes ONLY the raw version; the renormalized
    version is kept nowhere and should not be revived without flagging
    why.

(B) A mechanistic null test (proposed independently by one of the five
    panel models, Claude Opus 5): if the reported entropy-vs-I correlation
    (r=-0.82) is fully explained by zone_of's I>=0.35 gate rather than any
    real link between raters' (T,F) pattern and their I, then randomly
    reassigning which rater's (T,F) pair goes with which rater's I value,
    *within each item*, should reproduce a similarly extreme correlation
    just from the mechanics -- because the marginal distribution of I
    (which drives how many raters land in Ambiguity) is untouched by this
    shuffle, only the *pairing* with (T,F) is destroyed. This is done on
    the RAW (pre-normalization) T,I,F values, because that is what the
    original study's 'zone' column was actually computed from (verified:
    exp_expert_filter.py's zone_of() has no normalization step before it).
    Item-level mean I is invariant under this within-item shuffle (it's
    just the mean of the same 17 I-values), so the comparison target does
    not need to be recomputed per draw.

Run: python circularity_fix_experiment.py
"""
from __future__ import annotations

import math
import sys

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, r"C:\Users\HP\Documents\PCR6_RaterFusion_ADAS_2026\code")
from pcr6_fusion import renormalize_triplet, pairwise_mean_conflict

DATA_DIR = r"C:\Users\HP\Documents\Layered_Neutrosophic_HJMS\repo\experiments"
OUT_DIR = r"C:\Users\HP\Documents\PCR6_RaterFusion_ADAS_2026\results"
N_PERM = 5000
SEED = 42


def zone_of(T: float, I: float, F: float) -> str:
    """Exact copy of exp_expert_filter.py's zone_of -- do not edit independently."""
    if T > 0.50 and I < 0.35 and F < 0.30:
        return "Consensus"
    if I >= 0.35:
        return "Ambiguity"
    if T > 0.30 and F > 0.30:
        return "Contradiction"
    return "Ignorance"


def shannon_entropy(labels: list[str]) -> float:
    n = len(labels)
    counts: dict[str, int] = {}
    for lab in labels:
        counts[lab] = counts.get(lab, 0) + 1
    return -sum((c / n) * math.log2(c / n) for c in counts.values() if c > 0)


def load_filtered() -> pd.DataFrame:
    df = pd.read_csv(f"{DATA_DIR}\\exp_expert_filtered_long.csv")
    assert df["expert_id"].nunique() == 17
    assert df["hypothesis_id"].nunique() == 30
    assert len(df) == 510
    return df


def main() -> None:
    df = load_filtered()
    rng = np.random.default_rng(SEED)

    per_item_renorm = {}
    per_item_raw = {}
    for hyp_id, group in df.groupby("hypothesis_id"):
        group = group.sort_values("expert_id")
        triplets = [renormalize_triplet(r.T, r.I, r.F) for r in group.itertuples()]
        assert len(triplets) == 17
        per_item_renorm[hyp_id] = triplets
        per_item_raw[hyp_id] = list(zip(group["T"].to_numpy(), group["I"].to_numpy(), group["F"].to_numpy()))

    # ================= (A) I-free classical proxy (genuinely raw) =================
    rows = []
    for hyp_id in sorted(per_item_renorm):
        triplets = per_item_renorm[hyp_id]  # K, I still need valid BBAs
        raw_triples = per_item_raw[hyp_id]  # D uses these instead
        d_vals = np.array([t - f for (t, _, f) in raw_triples])
        D = float(np.std(d_vals, ddof=1))
        mean_K = pairwise_mean_conflict(triplets)
        mean_I = float(np.mean([t.I for t in triplets]))
        rows.append({"hypothesis_id": hyp_id, "hypothesis": None, "D_sd_TminusF": D, "mean_K": mean_K, "mean_I": mean_I})

    out = pd.DataFrame(rows).sort_values("hypothesis_id").reset_index(drop=True)
    assert len(out) == 30

    r_DK, p_DK = stats.pearsonr(out["D_sd_TminusF"], out["mean_K"])
    r_DI, p_DI = stats.pearsonr(out["D_sd_TminusF"], out["mean_I"])
    rho_DK, ps_DK = stats.spearmanr(out["D_sd_TminusF"], out["mean_K"])
    rho_DI, ps_DI = stats.spearmanr(out["D_sd_TminusF"], out["mean_I"])

    print("=" * 70)
    print("(A) I-free classical proxy: D_j = SD(T-F) over 17 RAW (unrenormalized) raters")
    print("=" * 70)
    print(f"D range: [{out['D_sd_TminusF'].min():.4f}, {out['D_sd_TminusF'].max():.4f}]")
    print(f"Pearson  r(D, K) = {r_DK:.4f}, p = {p_DK:.4g}, n=30")
    print(f"Pearson  r(D, I) = {r_DI:.4f}, p = {p_DI:.4g}, n=30")
    print(f"Spearman rho(D, K) = {rho_DK:.4f}, p = {ps_DK:.4g}, n=30")
    print(f"Spearman rho(D, I) = {rho_DI:.4f}, p = {ps_DI:.4g}, n=30")

    # --- illustrative items: largest positive OLS residual against D's fitted trend ---
    slope_K, intercept_K, *_ = stats.linregress(out["D_sd_TminusF"], out["mean_K"])
    slope_I, intercept_I, *_ = stats.linregress(out["D_sd_TminusF"], out["mean_I"])
    out["ols_resid_K"] = out["mean_K"] - (intercept_K + slope_K * out["D_sd_TminusF"])
    out["ols_resid_I"] = out["mean_I"] - (intercept_I + slope_I * out["D_sd_TminusF"])
    top_K_item = int(out.loc[out["ols_resid_K"].idxmax(), "hypothesis_id"])
    top_I_item = int(out.loc[out["ols_resid_I"].idxmax(), "hypothesis_id"])
    print(f"\nIllustrative item, largest positive residual for K against D's trend: item {top_K_item}")
    print(f"Illustrative item, largest positive residual for I against D's trend: item {top_I_item}")

    # ================= (B) Mechanistic null test (raw, pre-normalization) =================
    # Reproduce the manuscript's ORIGINAL raw-zone entropy and raw mean-I,
    # so the "observed" statistic below is computed the same way throughout
    # (fully raw), not mixed with the renormalized mean_I used elsewhere in
    # the manuscript -- disclosed explicitly, see report.
    obs_entropy = {}
    obs_meanI_raw = {}
    for hyp_id, triples in per_item_raw.items():
        zones = [zone_of(t, i, f) for (t, i, f) in triples]
        obs_entropy[hyp_id] = shannon_entropy(zones)
        obs_meanI_raw[hyp_id] = float(np.mean([i for (_, i, _) in triples]))

    ids_sorted = sorted(per_item_raw)
    entropy_arr = np.array([obs_entropy[h] for h in ids_sorted])
    meanI_raw_arr = np.array([obs_meanI_raw[h] for h in ids_sorted])
    r_obs, p_obs = stats.pearsonr(entropy_arr, meanI_raw_arr)

    # sanity: how close is raw mean-I to the renormalized mean-I already used
    # for the manuscript's headline r=-0.82 (which paired raw-zone entropy
    # with RENORMALIZED mean-I -- a pre-existing minor inconsistency,
    # disclosed here, not previously flagged by either adversarial pass)
    meanI_renorm_arr = out.sort_values("hypothesis_id")["mean_I"].to_numpy()
    r_manuscript_mixed, p_manuscript_mixed = stats.pearsonr(entropy_arr, meanI_renorm_arr)
    r_raw_vs_renorm_I, _ = stats.pearsonr(meanI_raw_arr, meanI_renorm_arr)
    max_abs_diff_I = float(np.max(np.abs(meanI_raw_arr - meanI_renorm_arr)))

    null_rs = np.empty(N_PERM)
    for p in range(N_PERM):
        entropy_perm = np.empty(len(ids_sorted))
        for k, hyp_id in enumerate(ids_sorted):
            triples = per_item_raw[hyp_id]
            tf_pairs = [(t, f) for (t, _, f) in triples]
            i_vals = [i for (_, i, _) in triples]
            perm_idx = rng.permutation(len(i_vals))
            synth = [(tf_pairs[j][0], i_vals[perm_idx[j]], tf_pairs[j][1]) for j in range(len(tf_pairs))]
            zones_perm = [zone_of(t, i, f) for (t, i, f) in synth]
            entropy_perm[k] = shannon_entropy(zones_perm)
        r_perm, _ = stats.pearsonr(entropy_perm, meanI_raw_arr)
        null_rs[p] = r_perm

    two_sided_p = float(np.mean(np.abs(null_rs) >= abs(r_obs)))
    percentile_obs = float(np.mean(null_rs <= r_obs) * 100)

    print()
    print("=" * 70)
    print("(B) Mechanistic null test: shuffle (T,F)<->I pairing within each item,")
    print("    keep zone_of's mechanics and I's marginal distribution intact")
    print("=" * 70)
    print(f"Observed (all-raw) r(entropy, mean_I_raw) = {r_obs:.4f}, p = {p_obs:.4g}, n=30")
    print(f"[disclosure] manuscript's reported r=-0.82 actually paired raw-zone entropy")
    print(f"  with RENORMALIZED mean_I, not raw mean_I: r(entropy, mean_I_renorm) = {r_manuscript_mixed:.4f}")
    print(f"  raw_I vs renorm_I across items: r={r_raw_vs_renorm_I:.4f}, max abs diff={max_abs_diff_I:.4f}")
    print(f"Null distribution over {N_PERM} within-item (T,F)<->I reshuffles (seed={SEED}):")
    print(f"  null r: mean={null_rs.mean():.4f}, sd={null_rs.std():.4f}, "
          f"5th/95th pct=[{np.percentile(null_rs,5):.4f}, {np.percentile(null_rs,95):.4f}]")
    print(f"  observed r={r_obs:.4f} sits at percentile {percentile_obs:.2f} of the null distribution")
    print(f"  two-sided permutation p-value for |r_obs| under the mechanistic null: {two_sided_p:.4f}")

    out.to_csv(f"{OUT_DIR}\\circularity_fix_proxy.csv", index=False)
    with open(f"{OUT_DIR}\\circularity_fix_results.txt", "w", encoding="utf-8") as f:
        f.write(f"(A) D=SD(T-F) proxy, n=30\n")
        f.write(f"D range=[{out['D_sd_TminusF'].min():.4f}, {out['D_sd_TminusF'].max():.4f}]\n")
        f.write(f"pearson_r_D_K={r_DK:.4f} p={p_DK:.4g}\n")
        f.write(f"pearson_r_D_I={r_DI:.4f} p={p_DI:.4g}\n")
        f.write(f"spearman_rho_D_K={rho_DK:.4f} p={ps_DK:.4g}\n")
        f.write(f"spearman_rho_D_I={rho_DI:.4f} p={ps_DI:.4g}\n")
        f.write(f"illustrative_item_top_K_residual={top_K_item}\n")
        f.write(f"illustrative_item_top_I_residual={top_I_item}\n")
        f.write(f"\n(B) mechanistic null test, {N_PERM} permutations, seed={SEED}\n")
        f.write(f"observed_r_entropy_meanI_raw={r_obs:.4f} p={p_obs:.4g}\n")
        f.write(f"manuscript_mixed_r_entropy_meanI_renorm={r_manuscript_mixed:.4f} p={p_manuscript_mixed:.4g}\n")
        f.write(f"raw_vs_renorm_I_correlation={r_raw_vs_renorm_I:.4f} max_abs_diff={max_abs_diff_I:.4f}\n")
        f.write(f"null_mean={null_rs.mean():.4f} null_sd={null_rs.std():.4f}\n")
        f.write(f"null_5th_pct={np.percentile(null_rs,5):.4f} null_95th_pct={np.percentile(null_rs,95):.4f}\n")
        f.write(f"observed_percentile_in_null={percentile_obs:.2f}\n")
        f.write(f"two_sided_permutation_p={two_sided_p:.4f}\n")

    print("\ncircularity_fix_experiment: done, all numbers above are as-computed, no post-hoc selection.")


if __name__ == "__main__":
    main()
