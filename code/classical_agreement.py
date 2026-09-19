"""
Classical inter-rater agreement (Fleiss' kappa) on the same expert dataset
used for the PCR6 fusion, to reproduce the numbers already reported in the
Layered Neutrosophic Statistics paper (kappa = 0.06 unfiltered / 0.18
filtered, see that paper's repo README) and to have them freshly verified
against the raw CSVs rather than trusted from memory.

Categories used for kappa: the 4-way "zone" label already assigned to each
(rater, hypothesis) triplet in the source data (Consensus / Ambiguity /
Contradiction / Ignorance) -- this is the same categorical reduction the
original paper used, not a new discretization invented for this note.
"""
from __future__ import annotations

import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "..", "data")
RESULTS_DIR = os.path.join(HERE, "..", "results")
ZONES = ["Consensus", "Ambiguity", "Contradiction", "Ignorance"]


def fleiss_kappa_from_long(df: pd.DataFrame) -> float:
    """Standard Fleiss' kappa for n items x fixed raters-per-item, categorical labels."""
    table = (
        df.groupby(["hypothesis_id", "zone"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=ZONES, fill_value=0)
    )
    n_items, n_cats = table.shape
    raters_per_item = table.sum(axis=1)
    N = raters_per_item.iloc[0]
    assert (raters_per_item == N).all(), "Fleiss kappa requires a fixed number of raters per item"

    P_i = ((table.values ** 2).sum(axis=1) - N) / (N * (N - 1))
    P_bar = P_i.mean()

    p_j = table.values.sum(axis=0) / (n_items * N)
    P_e = (p_j ** 2).sum()

    kappa = (P_bar - P_e) / (1 - P_e)
    return kappa


def main() -> None:
    long_unfiltered = pd.read_csv(os.path.join(DATA_DIR, "exp_expert_long.csv"))
    long_filtered = pd.read_csv(os.path.join(DATA_DIR, "exp_expert_filtered_long.csv"))

    kappa_unfiltered = fleiss_kappa_from_long(long_unfiltered)
    kappa_filtered = fleiss_kappa_from_long(long_filtered)

    n_raters_unfiltered = long_unfiltered["expert_id"].nunique()
    n_raters_filtered = long_filtered["expert_id"].nunique()
    n_items = long_unfiltered["hypothesis_id"].nunique()

    print(f"Items: {n_items}")
    print(f"Raters (unfiltered): {n_raters_unfiltered}, rows: {len(long_unfiltered)}")
    print(f"Raters (filtered):   {n_raters_filtered}, rows: {len(long_filtered)}")
    print(f"Fleiss kappa (unfiltered, zone categories): {kappa_unfiltered:.4f}")
    print(f"Fleiss kappa (filtered,   zone categories): {kappa_filtered:.4f}")

    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(os.path.join(RESULTS_DIR, "classical_agreement.txt"), "w") as f:
        f.write(f"Items: {n_items}\n")
        f.write(f"Raters (unfiltered): {n_raters_unfiltered}, rows: {len(long_unfiltered)}\n")
        f.write(f"Raters (filtered):   {n_raters_filtered}, rows: {len(long_filtered)}\n")
        f.write(f"Fleiss kappa (unfiltered, zone categories): {kappa_unfiltered:.4f}\n")
        f.write(f"Fleiss kappa (filtered,   zone categories): {kappa_filtered:.4f}\n")


if __name__ == "__main__":
    main()
