# Adversarial review of manuscript v0.1 and supporting code

1. **Critical — CONFIRMED — The manuscript's description of the triplet-to-BBA normalization is false for this dataset, and the transformation is far more pervasive than disclosed.**

   **What's wrong:** The manuscript says a judgment is a unit-sum triplet, “renormalized when a paraconsistent response gives \(T+F>1\)” (`paper/manuscript_v0.1.md:47`), and the code says that “most rows already satisfy T+I+F=1” and only “a few” paraconsistent rows need normalization (`code/pcr6_fusion.py:65-70`). Direct inspection of `exp_expert_filtered_long.csv` gives the opposite result: only 46/510 rows sum to 1, while 464/510 do not; the mean raw sum is 1.5312 (range 0 to 3). There are 178 rows with \(T+F>1\), not merely the 17 rows labeled `Contradiction`. `renormalize_triplet` divides **every nonzero row** by \(T+I+F\), regardless of paraconsistency (`code/pcr6_fusion.py:72-77`; called for all rows at `code/compare_and_verify.py:41`). One all-zero row (expert 20, item 8) is additionally converted to total ignorance \((0,1,0)\), a separate imputation not disclosed in the manuscript.

   This is not a cosmetic rescaling. Comparing the inadmissible raw triplets to the normalized analysis illustrates the sensitivity: the entropy–conflict correlation changes sign, from \(-0.348\) before normalization to \(+0.160\) after normalization; the item-level mean-conflict range changes from 0.307–0.599 to 0.146–0.280. Raw non-unit triplets are not valid BBAs, so the raw analysis is not a valid substitute, but the sign flip proves that the chosen mapping materially determines the headline result. The entropy–ignorance correlation remains negative (\(-0.842\) raw versus \(-0.819\) normalized), although the ignorance scale changes substantially.

   **Suggested fix:** Rewrite Sections 2.3 and 3 to state that 464/510 observations require closure normalization, disclose the all-zero-row rule, and describe the mapping as a consequential modeling choice rather than a minor exception. Add a sensitivity analysis using one or more defensible alternative mappings of unconstrained neutrosophic triplets to BBAs. Remove “without modification” at `paper/manuscript_v0.1.md:53`, or distinguish unmodified source records from transformed analytical values.

2. **Critical — CONFIRMED — The central “shared ‘I don't know’ zone” interpretation is contradicted by the actual zone labels.**

   **What's wrong:** Section 4.2 says that apparent categorical convergence is “frequently convergence onto a shared ‘I don't know’ zone” (`paper/manuscript_v0.1.md:84`), and the Abstract says apparent agreement is “driven almost entirely by shared ignorance” (`paper/manuscript_v0.1.md:19`). Yet all seven minimum-entropy items (7, 15, 16, 18, 21, 27, and 29; entropy 0.3228) have 16 of 17 ratings in the **Ambiguity** zone, not the Ignorance zone. Items 7 and 18, highlighted immediately afterward, are each 16 Ambiguity / 1 Consensus. Across all 510 filtered records there are 375 Ambiguity labels but only 39 Ignorance labels.

   The negative correlation does support a narrower statement: lower zone entropy is associated with higher **normalized continuous I mass**. It does not show convergence onto the categorical Ignorance zone, does not establish what “drives” entropy, and does not establish that raters independently lack information. The squared correlation is about 0.67, which is sizable but not “almost entirely,” and correlation does not provide the claimed causal explanation.

   **Suggested fix:** Replace the zone claim with the exact supported result: low-entropy items are mostly categorical Ambiguity and tend to have larger normalized I components. Show a zone-count table or plot and explicitly distinguish the continuous I coordinate from the categorical Ignorance label. Remove “driven,” “I don't know zone,” and “independently lack information” unless those mechanisms are separately measured.

3. **Major — CONFIRMED — The paper calls two associated statistics a “decomposition,” but they do not decompose kappa, entropy, or total disagreement.**

   **What's wrong:** The title, Abstract, Introduction, Discussion, and Conclusion repeatedly state that disagreement is decomposed into conflict and ignorance (`paper/manuscript_v0.1.md:6,19,31,94,108`). In the code, \(\bar K\) is the mean of pairwise conjunctive cross-products and \(\bar I\) is the mean normalized I coordinate (`code/compare_and_verify.py:48-49`). They neither sum to zone entropy nor reconstruct Fleiss' kappa, and no identity or exhaustive partition is derived. Other sources of categorical dispersion remain possible. The results are a comparison of two constructed features with entropy, not a mathematical decomposition of the classical statistic.

   **Suggested fix:** Use “two complementary diagnostics” or “separate conflict and ignorance summaries” throughout. If “decomposition” is retained, define the total being decomposed and prove or demonstrate that the components exhaust it.

4. **Major — CONFIRMED — The primary conflict statistic is not a PCR6 output, so the manuscript overstates PCR6's role.**

   **What's wrong:** The headline \(K=m_i(T)m_j(F)+m_i(F)m_j(T)\) is the conflicting mass of the ordinary unnormalized conjunctive rule (`code/pcr6_fusion.py:122-124`). PCR5/PCR6 begins only when that mass is redistributed. The reported \(K\) range, entropy correlation, and selected examples never use the PCR redistribution result. Actual PCR6 fusion appears only in the caveated cascade experiment. Phrases such as “use PCR6 to compute a genuine pairwise conflict mass” (`paper/manuscript_v0.1.md:19`), “pairwise PCR6 conflict computation” (`paper/manuscript_v0.1.md:108`), and “mean pairwise PCR6 conflict” (`paper/00_LEEME.md:3`) are therefore inaccurate.

   “Genuine conflict” is also an interpretation imposed on the cross-product, not something validated against an external measure of active contradiction.

   **Suggested fix:** Attribute \(K\) to the conjunctive rule and reserve “PCR6” for the redistribution/cascade. Either retitle and reframe the paper around evidence-theoretic conflict/ignorance diagnostics, or make a genuine PCR6-derived quantity central and justify it.

5. **Major — CONFIRMED — Items 7 and 18 are reproducibly selected, but not by the residual method described in the manuscript.**

   **What's wrong:** The code computes
   \[
   y-x\,s_y/s_x
   \]
   (`code/compare_and_verify.py:92-101`). That is not a residual from the empirical linear trend. An OLS residual uses \(y-[\bar y+r(s_y/s_x)(x-\bar x)]\). The implemented expression omits centering/intercept and, more importantly, omits the correlation \(r\). It therefore forces a positive unit-standardized slope even for ignorance, whose fitted relationship is strongly negative. Using actual OLS residuals selects item 30 for conflict and item 8 for ignorance, not items 7 and 18. For conflict, the empirical slope is only 0.01197 with \(r=0.1597\); the code uses a slope about \(1/r\), or 6.26 times larger. For ignorance it uses the wrong slope sign.

   Thus the selection is deterministic and reproducible, but the labels “deviates most from what entropy alone would predict” and “via a residual against the entropy-scaled trend — not hand-picked” (`paper/manuscript_v0.1.md:86`) do not describe the implementation. The formula instead favors high outcome and low entropy by construction, which silently aligns the examples with the desired narrative.

   **Suggested fix:** Predefine the scientific selection criterion and name it accurately. If prediction residuals are intended, fit and report the regression (including intercept) and use its residuals. If “high value at low entropy” is intended, call it a standardized contrast and justify that contrast. Regenerate the selected examples accordingly.

6. **Major — CONFIRMED — All quoted numerical values reproduce, but the alleged assert-based verification does not verify them.**

   **What's wrong:** Fresh runs reproduced: Fleiss' kappa 0.0589 unfiltered and 0.1755 filtered; \(\bar K\) range 0.1457–0.2802 (reported 0.146–0.280); \(\bar I\) range 0.1556–0.3869 (reported 0.156–0.387); correlations 0.1597 and \(-0.8188\) (reported 0.16 and \(-0.82\)); item 7 values 0.2121/0.3543; item 18 values 0.1821/0.3869; and sampled maximum T spread 0.7193 (reported 0.72). There is no numerical mismatch in Sections 4.1–4.3.

   However, the module says it provides “assert-based verification of every number” (`code/compare_and_verify.py:5`) and labels the headline block “all asserted against the table” (`code/compare_and_verify.py:82`). It asserts only the dataset dimensions and unit sums (`code/compare_and_verify.py:29-31,43,45-46,87`). It never asserts an expected range, correlation, item ID/value, or order spread, yet always prints “ALL CHECKS PASS” (`code/compare_and_verify.py:128`). `classical_agreement.py` likewise prints kappa without asserting expected values.

   **Suggested fix:** Add explicit regression tests with tolerances for every manuscript number, plus independent formula-level tests. Make “ALL CHECKS PASS” conditional on those assertions.

7. **Minor — CONFIRMED — The two-source PCR5/PCR6 formula is correct, but the self-test is too weak to protect it.**

   **What's wrong:** Independent derivation agrees with `code/pcr6_fusion.py:85-110`. The conjunctive masses are
   \(m_\cap(A)=a_1a_2+a_1\theta_2+\theta_1a_2\),
   \(m_\cap(B)=b_1b_2+b_1\theta_2+\theta_1b_2\),
   \(m_\cap(\Theta)=\theta_1\theta_2\),
   with partial conflicts \(a_1b_2\) and \(b_1a_2\). PCR5=PCR6 for two sources redistributes \(a_1b_2\) as \(a_1^2b_2/(a_1+b_2)\) to A and \(a_1b_2^2/(a_1+b_2)\) to B, and analogously redistributes \(b_1a_2\). This is exactly what lines 94–106 implement, and an asymmetric check with \((0.6,0.1,0.3)\) and \((0.2,0.5,0.3)\) returns \((0.584,0.05,0.366)\) in either source order.

   The bundled tests (`code/pcr6_fusion.py:179-192`) use only dogmatic identical sources and a symmetric total contradiction. Those endpoints would not detect several swapped-term or proportional-weight errors and do not exercise ignorance, asymmetric conflict, zero denominators, normalization, commutativity, or randomized mass conservation.

   **Suggested fix:** Add asymmetric hand-calculated cases, commutativity tests, denominator edge cases, invalid-input validation, and property tests over random valid BBAs. Keep the current endpoint tests as smoke tests only.

8. **Major — CONFIRMED — The 0.72 order-spread calculation is implemented as described, but it is only a small Monte Carlo lower bound and is unstable across seeds.**

   **What's wrong:** `fuse_group_with_order_sensitivity` correctly performs a fixed left-associated cascade for the natural order plus 200 uniformly shuffled permutations and computes max-minus-min (`code/pcr6_fusion.py:143-176`). In-place reuse of `idx` does not invalidate uniform shuffling. I found no inflation bug. The code also accurately measures **order sensitivity under one fixed parenthesization**, not all possible association structures.

   The reported maximum is nevertheless highly dependent on the small permutation sample. With 200 shuffles, changing the seed produced dataset-level maxima of 0.7047, 0.7193, and 0.7726. With the manuscript's seed 42, increasing to 1,000 and 5,000 shuffles increased the maximum to 0.7658 and 0.8052. Therefore 0.7193 is a reproducible observed sample spread, not “up to 0.72” in the sense of an estimated or exhaustive maximum. Sampling tends to understate the attainable range.

   **Suggested fix:** In the Abstract say “0.719 in a prespecified sample of 200 permutations per item (seed 42).” Use many more permutations, report seed and uncertainty/stability, and avoid comparing this sample extreme to the range of an unrelated statistic as if the scales were directly meaningful. Clarify that association-tree sensitivity was not explored.

9. **Major — CONFIRMED — The strongest causal/explanatory wording is not supported by the correlational design.**

   **What's wrong:** The Abstract claims that part of the kappa paradox “comes from” collapsing conflict and ignorance and that shared ignorance “drives” apparent agreement (`paper/manuscript_v0.1.md:19`). Section 4.2 repeats “driving” (`paper/manuscript_v0.1.md:84`). The study computes two correlations across only 30 items, using variables derived from the same triplets and a categorical zone rule that is itself derived from T/I/F. It does not manipulate information, test causal mechanisms, or connect item entropy to the dataset-level kappa algebraically. The conflict correlation is weak and nonsignificant under the ordinary Pearson test (\(r=0.1597\), two-sided \(p=0.399\)); the ignorance correlation is strong (\(r=-0.8187\), \(p\approx3.2\times10^{-8}\)), but still associational and partly structurally coupled to the source measurements.

   **Suggested fix:** Use “is associated with” consistently. Report sample size, confidence intervals or p-values, and sensitivity to the normalization/zone construction. Do not claim an explanation of the kappa paradox from an item-level entropy correlation.

10. **Major — CONFIRMED — The repository is not currently self-contained or portable despite the reproducibility claim.**

   **What's wrong:** Both analysis scripts hard-code Maikel's unrelated local data directory (`code/classical_agreement.py:17,45-46`; `code/compare_and_verify.py:23,28`) and hard-code this repository's absolute path for imports/outputs (`code/classical_agreement.py:61-63`; `code/compare_and_verify.py:15,24`). The source CSVs are not present in this working directory. The scripts ran on this machine only because the sibling project exists at exactly that location. That is incompatible with “small, fully reproducible diagnostic tool” (`paper/manuscript_v0.1.md:108`) and with the claim that all code “produces every number” for an external reader (`paper/manuscript_v0.1.md:112`).

   **Suggested fix:** Vendor the permitted data or add a documented download step with integrity hashes; use paths relative to the repository or command-line arguments; pin dependencies; and add one command that regenerates every result from a clean checkout.

11. **Minor — CONFIRMED — The citation verification status is internally inconsistent.**

   **What's wrong:** References 1–5 carry explicit `[VERIFY ...]` tags (`paper/manuscript_v0.1.md:116-120`), but reference 6 does not (`paper/manuscript_v0.1.md:121`), despite the heading saying all references are marked and `paper/00_LEEME.md:7` saying all six are marked. The in-text claims that the companion paper is accepted, has manuscript number 1942616, uses a pre-specified filter, and has public data (`paper/manuscript_v0.1.md:53`) also lack an adjacent `[VERIFY]` marker. This review did not browse and makes no claim about whether those bibliographic facts are true.

   **Suggested fix:** Add an explicit `[VERIFY acceptance status, manuscript number, DOI status, repository, filter provenance]` to reference 6 and the first substantive in-text use. Do not rely on the reference-section heading as a substitute for marking the individual citation.

12. **Minor — CONFIRMED — The manuscript is inconsistent about per-item Fleiss' kappa and does not reproduce the claimed filter.**

   **What's wrong:** Section 2.1 suggests kappa may be “computed per item” (`paper/manuscript_v0.1.md:39`), while Section 3.4 correctly says it is a dataset-level statistic “not naturally computed per item” (`paper/manuscript_v0.1.md:72`). A one-item plug-in Fleiss calculation is degenerate and should not be offered casually. Separately, the manuscript describes the five-rater exclusion as a pre-specified modal-agreement filter (`paper/manuscript_v0.1.md:53`), but the code merely loads an already-filtered CSV (`code/classical_agreement.py:46`; `code/compare_and_verify.py:28-31`); this repository cannot verify or reproduce that selection.

   **Suggested fix:** Remove the per-item-kappa parenthetical. Include or point to executable filter code and report the retained expert IDs so that the filtered analysis can be reconstructed from the unfiltered file.

## Overall verdict

**Another pass is required before showing this draft to a human co-author.** The two-source PCR5/PCR6 algebra is correct, the order-sensitivity code does what it says within its Monte Carlo sample, and every quoted number in Sections 4.1–4.3 reruns exactly. Those are meaningful strengths. However, the draft is not yet honest enough about its dominant normalization operation, its central “I don't know zone” story is directly contradicted by the categorical data, the illustrative-item “residual” method is not a residual, and the primary statistic is not actually produced by PCR6. These are framing and methods problems, not copyediting issues. Fix findings 1–6 and 8–10 before circulation; the remaining issues can be handled in the same revision.
