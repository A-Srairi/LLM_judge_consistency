import numpy as np
from statsmodels.stats.contingency_tables import mcnemar
from typing import List
from app.models import Verdict, Winner, PositionalBias


def compute_positional_bias(verdicts: List[Verdict]) -> PositionalBias:
    """
    Detects positional bias by comparing verdicts where order was AB vs BA.
    
    For each (judge, sample) pair we have two verdicts:
      - one where response A was shown first  (order="AB")
      - one where response B was shown first  (order="BA")
    
    If the judge flips its winner when the order changes, that is positional bias.
    We use McNemar's test to check if the flip rate is statistically significant.
    """

    ab_verdicts = [v for v in verdicts if v.order == "AB"]
    ba_verdicts = [v for v in verdicts if v.order == "BA"]

    if not ab_verdicts or not ba_verdicts:
        raise ValueError("Need both AB and BA ordered verdicts to compute positional bias")

    n = min(len(ab_verdicts), len(ba_verdicts))
    ab_verdicts = ab_verdicts[:n]
    ba_verdicts = ba_verdicts[:n]

    # build contingency table
    # consistent_a  = A won in both orderings
    # consistent_b  = B won in both orderings
    # flipped_ab_to_ba = A won when shown first, B won when shown second
    # flipped_ba_to_ab = B won when shown first, A won when shown second

    consistent_a = 0
    consistent_b = 0
    flipped_ab_to_ba = 0
    flipped_ba_to_ab = 0

    for ab, ba in zip(ab_verdicts, ba_verdicts):
        ab_win = ab.winner
        ba_win = ba.winner

        if ab_win == Winner.A and ba_win == Winner.A:
            consistent_a += 1
        elif ab_win == Winner.B and ba_win == Winner.B:
            consistent_b += 1
        elif ab_win == Winner.A and ba_win == Winner.B:
            flipped_ab_to_ba += 1
        elif ab_win == Winner.B and ba_win == Winner.A:
            flipped_ba_to_ab += 1
        # ties are ignored in positional bias — they don't reveal order preference

    total_non_tie = consistent_a + consistent_b + flipped_ab_to_ba + flipped_ba_to_ab

    if total_non_tie == 0:
        return PositionalBias(
            flip_rate=0.0,
            mcnemar_statistic=0.0,
            mcnemar_pvalue=1.0,
            is_significant=False,
        )

    flip_rate = (flipped_ab_to_ba + flipped_ba_to_ab) / total_non_tie

    # McNemar's test — tests whether the off-diagonal counts are symmetric
    # high p-value = flips are random noise
    # low p-value (< 0.05) = flips are systematic = real positional bias
    table = np.array([
        [consistent_a,   flipped_ab_to_ba],
        [flipped_ba_to_ab, consistent_b],
    ])

    # exact=True is more accurate for small samples
    result = mcnemar(table, exact=True)

    return PositionalBias(
        flip_rate=round(flip_rate, 4),
        mcnemar_statistic=round(float(result.statistic), 4),
        mcnemar_pvalue=round(float(result.pvalue), 4),
        is_significant=result.pvalue < 0.05,
    )