"""
PCR6 (Proportional Conflict Redistribution rule 6, Dezert-Smarandache) fusion
of rater (T, I, F) triplets on the binary frame Theta = {True, False}.

Mapping triplet -> BBA (basic belief assignment):
    m({True})  = T
    m({False}) = F
    m(Theta)   = I         (ignorance / non-specificity mass)
assuming T + I + F = 1 (renormalized if the raw triplet does not sum to 1;
in the filtered 17-rater dataset this is the MAJORITY case -- 464/510 rows
(91%), not "a few" -- mostly paraconsistent (T+F>1) but also some sub-unity
(T+I+F<1) rows; see `renormalize_triplet` and manuscript Section 3.1).

For TWO sources, PCR5 and PCR6 coincide exactly (Smarandache & Dezert,
"Advances and Applications of DSmT", Vol. 2, 2006; Martin & Osswald 2007
show PCR6 differs from PCR5 only for N >= 3 sources). The formula used here
for two sources A={True}, B={False}, frame Theta on {A,B}:

Conjunctive rule (unnormalized):
    m12(A)     = m1(A)m2(A) + m1(A)m2(T) + m1(T)m2(A)
    m12(B)     = m1(B)m2(B) + m1(B)m2(T) + m1(T)m2(B)
    m12(Theta) = m1(T)m2(T)
    conflict K = m1(A)m2(B) + m1(B)m2(A)

PCR5/PCR6 redistribution of the conflicting mass, proportional to the two
masses that generated it:
    to A: m1(A)^2 m2(B) / (m1(A)+m2(B))  +  m1(B) m2(A)^2 / (m1(B)+m2(A))
    to B: m1(A) m2(B)^2 / (m1(A)+m2(B))  +  m1(B)^2 m2(A) / (m1(B)+m2(A))

m_PCR6(A) = m12(A) + [PCR5/6 redistribution to A]
m_PCR6(B) = m12(B) + [PCR5/6 redistribution to B]
m_PCR6(Theta) = m12(Theta)

IMPORTANT / HONESTY NOTE: PCR6 for N >= 3 sources is NOT simply "apply the
2-source rule pairwise and cascade" -- Martin & Osswald (2007) define a
genuine N-source generalization that differs from naive cascading, and PCR6
combination is known to be non-associative (this exact non-associativity was
already flagged as an open technical question in this research program's
Paper 1, PCR6/RAG). This script implements the CASCADED PAIRWISE version
(combine rater 1 & 2, then combine the result with rater 3, etc., in the
raters' listed order) as an explicit, documented approximation -- NOT the
formal N-source PCR6. `fuse_group_with_order_sensitivity` quantifies how much
the result depends on rater order, precisely because that dependence is real
and must be reported, not hidden.
"""
from __future__ import annotations

import itertools
import random
from dataclasses import dataclass


EPS = 1e-12


@dataclass(frozen=True)
class Triplet:
    T: float
    I: float
    F: float


def renormalize_triplet(T: float, I: float, F: float) -> Triplet:
    """Map a raw (T,I,F) in [0,1]^3 to a valid BBA on {A, B, Theta} that sums to 1.

    Only 46/510 rows (9%) of the filtered dataset already satisfy T+I+F=1.
    The other 464/510 (91%) do not -- most because the neutrosophic instrument
    allows paraconsistent responses (T+F>1, "Contradiction" zone), some
    because of sub-unity responses (T+I+F<1). For all of those we renormalize
    by the raw sum so the result is a valid BBA; this is a consequential
    modeling choice made explicit here and disclosed in manuscript Section 3.1,
    not a marginal correction for a handful of edge-case rows.
    """
    total = T + I + F
    if total <= EPS:
        # Degenerate row (should not occur in this dataset); fall back to
        # total ignorance rather than dividing by zero.
        return Triplet(0.0, 1.0, 0.0)
    return Triplet(T / total, I / total, F / total)


def pcr6_two_sources(m1: Triplet, m2: Triplet) -> Triplet:
    """Exact PCR5=PCR6 fusion of two BBAs on {A={True}, B={False}, Theta}."""
    mA1, mI1, mF1 = m1.T, m1.I, m1.F
    mA2, mI2, mF2 = m2.T, m2.I, m2.F

    # Conjunctive rule
    m12_A = mA1 * mA2 + mA1 * mI2 + mI1 * mA2
    m12_B = mF1 * mF2 + mF1 * mI2 + mI1 * mF2
    m12_Theta = mI1 * mI2

    # PCR5/PCR6 redistribution of the two conflicting terms
    redis_to_A = 0.0
    redis_to_B = 0.0

    denom1 = mA1 + mF2
    if denom1 > EPS:
        redis_to_A += (mA1 ** 2) * mF2 / denom1
        redis_to_B += mA1 * (mF2 ** 2) / denom1

    denom2 = mF1 + mA2
    if denom2 > EPS:
        redis_to_B += (mF1 ** 2) * mA2 / denom2
        redis_to_A += mF1 * (mA2 ** 2) / denom2

    A = m12_A + redis_to_A
    B = m12_B + redis_to_B
    Theta = m12_Theta

    total = A + B + Theta
    assert abs(total - 1.0) < 1e-9, f"PCR6 mass leak: total={total}"
    return Triplet(A, Theta, B)


def fuse_sequence(triplets: list[Triplet]) -> Triplet:
    """Cascade PCR6 fusion across a list of raters, in the given order."""
    assert len(triplets) >= 1
    acc = triplets[0]
    for t in triplets[1:]:
        acc = pcr6_two_sources(acc, t)
    return acc


def conflict_mass_two_sources(m1: Triplet, m2: Triplet) -> float:
    """K = total conflicting mass between two sources before redistribution."""
    return m1.T * m2.F + m1.F * m2.T


def pairwise_mean_conflict(triplets: list[Triplet]) -> float:
    """Mean pairwise conflict K over all C(n,2) rater pairs for one item.

    This is order-independent and is the headline conflict statistic reported
    in the manuscript (the cascaded fused result is order-DEPENDENT, see
    `fuse_group_with_order_sensitivity`, and is reported only as a secondary,
    caveated statistic).
    """
    n = len(triplets)
    if n < 2:
        return 0.0
    pairs = list(itertools.combinations(range(n), 2))
    ks = [conflict_mass_two_sources(triplets[i], triplets[j]) for i, j in pairs]
    return sum(ks) / len(ks)


def fuse_group_with_order_sensitivity(
    triplets: list[Triplet], n_shuffles: int = 200, seed: int = 42
) -> dict:
    """Cascade-fuse a group of raters in the natural order and in `n_shuffles`
    random orders, to quantify how much the cascaded PCR6 result depends on
    order (a real, documented property of PCR6 for N>=3 sources, not a bug).
    """
    natural = fuse_sequence(triplets)

    rng = random.Random(seed)
    shuffled_results = []
    idx = list(range(len(triplets)))
    for _ in range(n_shuffles):
        rng.shuffle(idx)
        order = [triplets[i] for i in idx]
        shuffled_results.append(fuse_sequence(order))

    A_vals = [natural.T] + [r.T for r in shuffled_results]
    Th_vals = [natural.I] + [r.I for r in shuffled_results]
    B_vals = [natural.F] + [r.F for r in shuffled_results]

    def spread(vals: list[float]) -> float:
        return max(vals) - min(vals)

    return {
        "natural_order_fused": natural,
        "n_shuffles": n_shuffles,
        "spread_A": spread(A_vals),
        "spread_Theta": spread(Th_vals),
        "spread_B": spread(B_vals),
        "mean_A": sum(A_vals) / len(A_vals),
        "mean_Theta": sum(Th_vals) / len(Th_vals),
        "mean_B": sum(B_vals) / len(B_vals),
    }


if __name__ == "__main__":
    # Minimal self-test: two fully agreeing certain sources -> no ignorance, no conflict.
    a = Triplet(1.0, 0.0, 0.0)
    b = Triplet(1.0, 0.0, 0.0)
    fused = pcr6_two_sources(a, b)
    assert abs(fused.T - 1.0) < 1e-9 and abs(fused.F) < 1e-9 and abs(fused.I) < 1e-9

    # Two fully contradicting certain sources -> PCR6 must NOT put mass on Theta
    # from conflict; with pure certain BBAs (I=0) the whole conflicting mass
    # gets redistributed back to A and B by symmetry (0.5 / 0.5).
    a = Triplet(1.0, 0.0, 0.0)
    b = Triplet(0.0, 0.0, 1.0)
    fused = pcr6_two_sources(a, b)
    assert abs(fused.T - 0.5) < 1e-9 and abs(fused.F - 0.5) < 1e-9 and abs(fused.I) < 1e-9
    print("pcr6_fusion self-tests: PASS")
