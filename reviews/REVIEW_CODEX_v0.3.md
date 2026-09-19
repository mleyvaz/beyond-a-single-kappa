# Third adversarial review — manuscript v0.3/v0.4 rewrite (D=SD(T-F) proxy, new §4.3, citation dilution)

Method: hostile-reviewer prompt run against `codex exec --sandbox read-only
--skip-git-repo-check` pointed at this project folder, instructed to read
`paper/manuscript_v0.1.md`, `paper/00_LEEME.md`, and all of `code/*.py` with
its own tools and re-run scripts to check every number. Raw Codex output
saved at `reviews/salida_codex_v0.3_raw.md`. Every finding below was then
independently re-verified line-by-line by re-running the relevant code
myself (not just trusting Codex's numbers) before being kept, downgraded, or
discarded. Findings are listed by final (post-verification) severity.

---

## 1. CRÍTICO — The "I-free" proxy $D$ is not actually free of $I$; the headline finding may reverse

**Location:** §3.4, §4.2, Abstract, Limitation 3/4/7, Conclusion; `code/circularity_fix_experiment.py`.

**What's wrong:** The manuscript repeatedly claims $D_j = \mathrm{SD}(T_i-F_i)$
"never involves $I$ or any categorical thresholding" and is "the continuous,
$I$-free proxy." But `circularity_fix_experiment.py` computes $D$ from the
**renormalized** triplets (`renormalize_triplet`, which divides by
$T+I+F$), so in fact
$$T'-F' = \frac{T-F}{T+I+F},$$
i.e. $I$ sits in the denominator and directly scales every value $D$ is
built from. This is exactly the kind of "reuses one of its own inputs"
problem the manuscript diagnoses in the discarded entropy proxy — applied,
undetected, to its own replacement.

I independently recomputed $D$ two ways and confirmed Codex's numbers exactly:

| | Pearson r(D,K) | p | Pearson r(D,I) | p | Spearman ρ(D,K) | p | Spearman ρ(D,I) | p |
|---|---|---|---|---|---|---|---|---|
| **As implemented** (D on renormalized T,F) | 0.378 | 0.039 | −0.598 | 0.0005 | 0.219 | 0.246 | −0.727 | 5.3e-6 |
| **Truly I-free** (D on raw, un-renormalized T,F) | **0.688** | **2.6e-5** | −0.213 | 0.258 | **0.631** | **1.8e-4** | −0.324 | 0.081 |

Using a genuinely $I$-free $D$, the result **inverts**: conflict $K$ becomes
the robust, significant-under-both-estimators correlate, and ignorance $I$
becomes non-significant under both. This is not a rounding-level issue — it
flips which of the paper's two headline associations is "the" finding. It
also changes the illustrative-item selection (with raw $D$, the top
ignorance-residual item is item 21, not item 8 — reconfirmed independently).

I also checked the precommitment record itself
(`openrouter_circularity_fix/respuestas/_CONSOLIDADO.md`, dated before the
experiment script and results were produced, so the precommitment timing
claim in finding #7 below does hold up): the panel's proposed design writes
$D_j = \mathrm{SD}(T_{ij}-F_{ij})$ over the plain elicited values, with no
mention of renormalization anywhere in that document. The implementation
silently substituted renormalized values (likely because the same loop
reuses `renormalize_triplet` to compute $\bar K$ and $\bar I$ for
convenience), which is a real deviation from the precommitted design, not a
disclosed choice.

**Why it matters:** this is the paper's central empirical claim. Reporting
it as "I-free" is factually false as implemented, and the true I-free
version does not support the paper's current narrative.

**Correction proposed — NOT applied, requires Maikel's (and likely
Florentin's) decision:** Recompute $D$ from raw, non-renormalized $T,F$
(matching the precommitted design literally), and decide how to
re-report Section 4, the Abstract, and the Conclusion depending on which
result is judged more defensible — the raw-$D$ version is arguably *more*
defensible (it is what "I-free" actually requires), but it changes which
variable ($K$ vs $I$) is the paper's stronger finding, which is a scientific
conclusion change, not a wording fix. I did not touch Section 4's
substantive numbers, item selection, Abstract, or Conclusion for this
reason — this needs your explicit sign-off before any further editing.

---

## 2. MAYOR — Renormalization is mischaracterized as "mostly paraconsistency"

**Location:** §3.1, "Normalization disclosure."

**What's wrong:** The text said renormalization was needed "most because the
instrument allows paraconsistent responses ($T+F>1$) or, less often,
sub-unity responses." I verified the actual breakdown of the 464/510 rows
directly from the CSV: **178 (38%) have $T+F>1$** (true paraconsistency);
**280 (60%) have $T+I+F>1$ purely because $I$ itself pushes the sum over 1**,
with $T+F\le1$; and **6 (1%) are sub-unity**. Paraconsistency is a
*minority* cause, not "most" of the cause.

**Applied fix:** rewrote the sentence in §3.1 to give the exact breakdown
(178/280/6) instead of "most... or, less often."

---

## 3. MAYOR — "Same item" claim for the PCR6 order-spread resampling check is false

**Location:** §4.4.

**What's wrong:** The text said the maximum order-spread across items was
"0.72 at 200 shuffles... 0.77 at 1,000 shuffles, 0.81 at 5,000 shuffles,
**same item**." I reran `fuse_group_with_order_sensitivity` at all three
shuffle counts (seed 42) and got exactly the numbers already in the
manuscript (0.7193 / 0.7658 / 0.8052) but at **three different items**: item
8 (200 shuffles), item 22 (1,000 shuffles), item 9 (5,000 shuffles). The
"same item" claim is unsupported by the code as written.

**Applied fix:** rewrote the sentence to name the three different items and
note explicitly that instability of *which* item attains the max is itself
evidence of how noisy this sampled maximum is — strengthens rather than
weakens the limitation already being disclosed.

---

## 4. MENOR (downgraded from Codex's MAYOR) — Mechanistic null test (§4.3) interpretation is defensible but stated more strongly than the test technically shows

**Location:** §4.3.

**What Codex argued:** shuffling which rater's $(T,F)$ pairs with which
rater's $I$, *within* each item, leaves the item's full $I$ distribution
(and hence, given `zone_of`'s `I>=0.35 → Ambiguity` rule, the count of
Ambiguity-zone raters) completely untouched — only the composition of the
remaining, non-Ambiguity raters can change. So the permutation destroys very
little of what actually drives entropy, and Codex read the near-identical
null distribution as evidence the test doesn't show what it claims.

**My assessment after checking the mechanism directly:** this is correct as
a *mechanism description*, but it is not a new problem — it is exactly the
mechanism the manuscript itself describes in the same paragraph ("the zone
rule places any rater with $I\ge0.35$ into a single category... an item
where most raters carry high $I$ will tend toward one dominant category...
for the same reason it has high mean $I$"). The permutation test's actual
job is to show that this threshold-driven mechanism alone is sufficient to
produce the observed correlation magnitude, and it does show that. I
consider Codex's objection a legitimate call for more precise language (the
null isolates the *threshold-gate* mechanism specifically, not "all possible
mechanisms," and does not rule out every form of residual signal) rather
than a factual error — so I downgraded this from MAYOR to MENOR and did not
apply Codex's suggested rewrite. Flagging for awareness rather than fixing,
since it is a matter of statistical framing precision, not a wrong number —
and given finding #1's severity, this proxy is already being retired as
primary evidence regardless.

---

## 5. MENOR — Reference-list header overclaimed verification status

**Location:** References section header.

**What's wrong:** Header read "References [ALL MARKED VERIFY...]" but 4 of
13 entries (the JEPR citations: Leyva-Vázquez, Macazana Fernández, Matheu
Pérez, Pérez Molina & Pérez Mayedo) carry no `[VERIFY]` tag — confirmed by
direct inspection.

**Applied fix:** reworded the header to "[MOST MARKED VERIFY...]" and
explained that the 4 JEPR entries were checked against internal project
records/live Zenodo DOIs as of 18-sep-2026 but not against an external
bibliographic database, matching what `00_LEEME.md` already discloses.

---

## 6. MENOR — Reference-list/in-text citation biyection had one orphan entry

**Location:** References list; §1/Abstract.

**What's wrong:** `Cicchetti, D. V., & Feinstein, A. R. (1990)` (the kappa-
paradox "Part II" paper) was listed in the reference list but never cited
anywhere in the body — only its companion "Part I" paper (`Feinstein &
Cicchetti, 1990`) was cited, twice. Confirmed by exhaustive grep of the body
text.

**Applied fix:** added `Cicchetti & Feinstein, 1990` alongside the existing
`Feinstein & Cicchetti, 1990` citation in §1 (both papers are a matched
pair on the same paradox, standard practice to cite together) — restores
the biyección without removing or fabricating anything.

---

## 7. MENOR — Companion-paper mention lacked its author-year tag

**Location:** §3.1.

**What's wrong:** The dataset's source paper was described narratively
("a companion paper on layered neutrosophic statistics, accepted, Hacettepe
Journal...") without the explicit `(Smarandache & Leyva-Vázquez, 2026)` tag
that its reference-list entry uses, making the link between the mention and
the reference list implicit rather than explicit.

**Applied fix:** added the explicit `(Smarandache & Leyva-Vázquez, 2026)`
tag at first mention.

---

## 8. MENOR — Quoted item text is an unlabeled translation

**Location:** §3.1, §4.2.

**What's wrong:** All illustrative item quotes (e.g., item 30, item 8) are
presented in English quotation marks as if they were the literal stored
text; the actual dataset stores the items in Spanish. Confirmed by reading
the raw CSV: item 30's actual text is "¿La computación cuántica es capaz de
romper la encriptación RSA-2048 con el hardware actualmente disponible?" —
notably, the pre-fix English paraphrase in §4.2 said "capable of breaking
current encryption **within the next decade**," which materially changes
the claim's meaning (a near-term prediction vs. a question about
present-day capability) and dropped "RSA-2048" — this was a real
mistranslation, not just an unlabeled one.

**Applied fixes:**
- Corrected the item-30 paraphrase in §4.2 to accurately reflect the
  original claim ("quantum computing is currently capable of breaking
  RSA-2048 encryption with hardware available today").
- Added an explicit "authors' translation" disclosure at first mention of
  quoted item text in §3.1, covering all later quotes.

---

## 9. MENOR — "Data and code availability" claims checked against the wrong folder by Codex; one real, smaller gap found instead

**Location:** Data and code availability; Limitation 8.

**What Codex claimed:** that the reproducibility/self-containment claim is
false because the scripts in `code/` use absolute paths and there is no
local `requirements.txt` or populated `data/` folder.

**Why this is a false positive:** Codex checked this project's local
development copy of the scripts (`code/`), not the actual published public
repository the manuscript cites (`github.com/mleyvaz/beyond-a-single-kappa`,
vendored locally at `repo/`). I checked `repo/code/*.py` directly: all three
analysis scripts there resolve `DATA_DIR` via `os.path.join(HERE, "..",
"data")` (relative paths only), `repo/data/` contains both vendored CSVs,
and `repo/requirements.txt` exists with pinned minimum versions. The
manuscript's claim is accurate for the actual public repository.

**Real, smaller gap found instead:** the new verification script I added
this session (`code/item_selection_D_based.py`, see finding below) has not
yet been pushed to the public repo — so right now the public repo does not
contain the script that backs the manuscript's Section 4.2 item-selection
method description. This is a today's-session gap, not a pre-existing
misrepresentation.

**Not fixed (requires a `git push` decision, and is moot pending finding
#1's resolution — the item-selection method may need to be recomputed
against the corrected $D$ before anything is pushed):** flagged as pending.

---

## 10. Verified clean — no action needed

- **All D-proxy correlation numbers, K/I ranges, kappa values, 464/510 renormalization count, and the 100th-percentile/p=1.00 null-test result** matched the code's output exactly on independent re-run (not just approximately — to the 4th decimal in every case checked).
- **Section renumbering and all cross-references** (old §4.3 cascade → §4.4; new §4.3 mechanistic check) were checked exhaustively across Abstract, §2.2, §3.4, §4.2, §4.4, Discussion, Limitations 3/4/5, Conclusion, and Data availability — every "Section X.Y" reference points to the correct, current section. No residual mis-pointed cross-references found.
- **Items 30 and 8 as the D-based OLS-residual selections**: no script in the repository actually performed this specific regression before this review (`compare_and_verify.py` regresses on the discarded zone-entropy proxy, not on $D$). I wrote and ran `code/item_selection_D_based.py`, which regresses $K$ and $I$ on $D$ (as currently implemented, i.e. on renormalized $T,F$) and confirms items 30 and 8 are indeed the top residuals under that specific regression — the manuscript's numeric claim about items 30/8 was correct, just previously unbacked by any committed code. This gap is now closed (with the caveat that finding #1 may require re-deriving this selection against a corrected, truly raw $D$).
- **Reference list alphabetical order** (APA 7, by first-author surname) is correct throughout, including the three newly inserted external citations (Daniel; Gwet; Landis & Koch) and the four JEPR citations.
- **Tone regarding neutrosophy/DSmT (§3.4, §4.3, Limitation 4):** read closely for any phrase that could be construed as a critique of neutrosophic theory, the $(T,I,F)$ representation, or Florentin's DSmT/PCR6 work. Found none — every instance of the circularity finding is explicitly scoped to "a general property of any threshold-based categorical rule," with explicit disclaimers that it "says nothing about the validity of the $(T,I,F)$ representation or the zone categories' original purpose." No tone finding to report here; this pass confirms the framing choice from the previous rewrite held up.
- **Own-network citation share**: recount confirms 6 of 13 references (Smarandache & Dezert 2006; Smarandache & Leyva-Vázquez 2026; and all 4 JEPR citations) = 46%, unchanged by this round's fixes (no reference added or removed, only citation linkages fixed).

---

## Not verifiable in this pass

- Existence/exact metadata (volume, pages, DOI resolution) of any reference,
  including the 3 newly added external ones (Gwet 2008; Landis & Koch 1977;
  Daniel 2010) — no live internet/bibliographic-database access from this
  environment. All already correctly carry `[VERIFY]` tags.
- Whether the public GitHub repository (`github.com/mleyvaz/beyond-a-single-
  kappa`) matches the local `repo/` clone examined here bit-for-bit (I
  checked the local clone only, not the live remote).

---

## Veredicto

**PUBLICABLE CON CORRECCIONES — pero con una decisión pendiente de gravedad
CRÍTICA (hallazgo #1) que debe resolverse antes de cualquier otra cosa,
incluyendo mostrarle esto a Florentin.** Findings #2–#9 above are fixed
(low-risk, wording/disclosure-level) or explicitly downgraded/discarded with
reasoning. Finding #1 is a substantive, code-verified circularity in the
paper's *replacement* proxy that can flip which variable (K or I) is the
paper's headline finding — this is not a wording fix and was deliberately
left untouched pending your decision.
