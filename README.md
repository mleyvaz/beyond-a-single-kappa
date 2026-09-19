# Beyond a Single Kappa — Data and Code

Code, data, and reproducible results supporting the manuscript:

> **Smarandache, F.; Leyva-Vázquez, M. Y.** (in preparation). *Beyond a Single Kappa: Separating Conflict from Ignorance in Rater Disagreement.* Proposed for submission to **Advances and Applications in Statistics** (Pushpa Publishing House, ESCI).

**Status:** draft manuscript, proposal stage. Florentin Smarandache has not yet seen or approved this manuscript, its framing, or the author order — nothing has been submitted anywhere. This repository documents the analysis code and every adversarial-review round it went through, including a critical finding (see "Adversarial review and the circularity fix" below) that changed the paper's headline result.

**Authors of this repository's code:** Maikel Y. Leyva-Vázquez¹ (`maikel.leyvav@ug.edu.ec`), with Florentin Smarandache's proposed co-authorship of the associated manuscript still pending confirmation.

¹ Universidad Bolivariana del Ecuador / Universidad de Guayaquil, Ecuador

---

## What this note does

Educational and social-science research routinely aggregates multiple raters' judgments (rubric scoring, content-validity panels, Delphi studies) into a single agreement statistic such as Cohen's or Fleiss' kappa. This note asks whether representing each rater's judgment as a truth/indeterminacy/falsity `(T, I, F)` triplet — a basic belief assignment in the sense of Dempster-Shafer theory — lets a single scalar disagreement signal be decomposed into two structurally different quantities: a **conjunctive conflict mass** (raters actively contradicting each other) and an **ignorance mass** (raters independently lacking information). It is a diagnostic case study, not a claim of general superiority over classical statistics.

## Data provenance

The underlying 22-rater / 17-rater (filtered) × 30-item expert-elicitation dataset (`data/exp_expert_long.csv`, `data/exp_expert_filtered_long.csv`) was originally collected for a companion, already-accepted paper:

> Smarandache, F.; Leyva-Vázquez, M. Y. *A Layered Framework for Neutrosophic Statistics: Foundational Distinctions, Empirical Validation, and Operational Implementation.* Hacettepe Journal of Mathematics and Statistics (2026), DOI: [10.15672/hujms.1942616](https://doi.org/10.15672/hujms.1942616). Original data and code: [github.com/mleyvaz/layered-neutrosophic-statistics](https://github.com/mleyvaz/layered-neutrosophic-statistics).

This repository vendors an unmodified copy of the two CSVs actually used here (already public in the repository above) so that the present analysis is self-contained and reproducible without depending on a sibling repository's file paths.

## Adversarial review and the circularity fix

This manuscript went through two independent adversarial reviews (`reviews/REVIEW_CODEX_v0.1.md`, `reviews/REVIEW_GEMINI_v0.2.md`), both openly included here. The second review found that the original headline statistic — Shannon entropy over four "zone" categories (Consensus/Ambiguity/Contradiction/Ignorance), correlated against mean ignorance `I` (r=-0.82) — was structurally confounded: the zone-classification rule assigns "Ambiguity" to any rater with `I >= 0.35` *before* checking anything else, so the entropy variable partly incorporates `I` by construction.

To resolve this, five independent LLMs (via OpenRouter — GPT-6 Astra Pro, Claude Opus 5, Gemini 3.1 Pro, Grok 4.6, DeepSeek V4 Pro) were consulted on how to fix it; all five independently recommended building a classical disagreement proxy that never touches `I` or the zone rule. `code/circularity_fix_experiment.py` implements the resulting precommitted design:

- **A mechanistic null test** confirming the original entropy–ignorance correlation is fully explained by the zone rule's mechanics (observed r=-0.842 sits at the 100th percentile of a null distribution built from 5,000 within-item reshuffles of the (T,F)↔I pairing; two-sided permutation p=1.00).
- **A replacement, I-free proxy** (`D = SD(T-F)` per item, computed on **raw, unrenormalized** T,F). A second self-check caught a subtler version of the same problem: an earlier implementation of this proxy divided by `T+I+F` before computing D, silently reintroducing `I` through the denominator. On genuinely raw values the result is not just different but reversed — conjunctive conflict `K` correlates with `D` robustly (Pearson r=0.69, p<0.001; Spearman ρ=0.63, p<0.001), while ignorance `I` shows no significant association under either estimator (Pearson r=-0.21, p=0.26; Spearman ρ=-0.32, p=0.08).

Every number above is produced by the scripts in this repository, not asserted from memory. `code/circularity_fix_experiment.py`'s module docstring documents both the before/after numbers and why the renormalized version was wrong, for anyone tempted to "fix" it back.

## Repository layout

```
code/
  pcr6_fusion.py                 # DSmT PCR5/PCR6 (two-source) fusion + N-source cascade with order-sensitivity check
  classical_agreement.py         # Fleiss' kappa on the zone categories (unfiltered/filtered cross-check)
  compare_and_verify.py          # Per-item K / I vs. zone-entropy comparison, with assert-based number verification
  circularity_fix_experiment.py  # The I-free proxy (A, raw T,F) and the mechanistic null test (B) described above
  item_selection_D_based.py      # Confirms the manuscript's two illustrative items (30, 21) against the raw D trend

data/
  exp_expert_long.csv            # 22 raters x 30 items, unfiltered (660 rows)
  exp_expert_filtered_long.csv   # 17 raters x 30 items, filtered (510 rows) -- primary dataset used throughout

results/
  classical_agreement.txt        # Fleiss' kappa output
  item_comparison.csv            # Per-item K, I, zone entropy, PCR6 cascade order-sensitivity stats
  headline_numbers.txt           # Every number quoted in the manuscript's Sections 3-4
  circularity_fix_proxy.csv      # Per-item D=SD(T-F) (raw), K, I
  circularity_fix_results.txt    # Full circularity-fix experiment output (proxy correlations + null test)
  item_selection_D_based.csv/.txt # Illustrative-item OLS residuals against raw D

reviews/
  REVIEW_CODEX_v0.1.md           # First adversarial review (Codex CLI), 12 findings
  REVIEW_GEMINI_v0.2.md          # Second, independent adversarial review (Gemini CLI) -- found the entropy-proxy circularity
  REVIEW_CODEX_v0.3.md           # Third adversarial review (Codex CLI) -- found the D-proxy renormalization circularity
```

## How to reproduce

```bash
pip install -r requirements.txt
cd code
python classical_agreement.py
python compare_and_verify.py
python circularity_fix_experiment.py
python item_selection_D_based.py
```

All scripts are self-contained (relative paths only) and write their outputs to `../results/`. `circularity_fix_experiment.py` uses a fixed random seed (`SEED = 42`) for its 5,000-draw permutation test, so its output is exactly reproducible.

## License

Code: MIT License (see `LICENSE`). Data: reused unmodified from the openly available companion repository above; see that repository for its own data-availability terms.
