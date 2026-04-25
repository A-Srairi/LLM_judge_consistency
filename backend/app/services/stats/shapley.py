from itertools import combinations
from typing import List, Dict
import numpy as np
from app.models import Verdict, Winner, ShapleyAttribution


def _inconsistency_score(verdicts: List[Verdict], criteria: List[str]) -> float:
    """
    Measures how inconsistent a set of verdicts is overall.
    Returns 0.0 if perfectly consistent, 1.0 if maximally inconsistent.
    """
    if not verdicts:
        return 0.0

    # inconsistency = how spread out the winners are
    winners = [v.winner for v in verdicts]
    total = len(winners)
    counts = {w: winners.count(w) for w in set(winners)}
    most_common_count = max(counts.values())

    winner_inconsistency = 1.0 - (most_common_count / total)

    # criteria inconsistency = how much scores vary across verdicts
    criteria_inconsistency = 0.0
    n_criteria = 0

    for criterion in criteria:
        diffs = []
        for v in verdicts:
            if criterion in v.criteria_scores:
                a = v.criteria_scores[criterion].get("A", np.nan)
                b = v.criteria_scores[criterion].get("B", np.nan)
                if not np.isnan(a) and not np.isnan(b):
                    diffs.append(a - b)

        if len(diffs) > 1:
            # normalize std by the scale range (1-5 scale = range of 8)
            criteria_inconsistency += min(float(np.std(diffs)) / 8.0, 1.0)
            n_criteria += 1

    if n_criteria > 0:
        criteria_inconsistency /= n_criteria

    # combine — winner inconsistency weighs more
    return round(0.6 * winner_inconsistency + 0.4 * criteria_inconsistency, 4)


def compute_shapley_attribution(
    verdicts: List[Verdict],
    criteria: List[str],
) -> ShapleyAttribution:
    """
    Computes Shapley values to attribute inconsistency to each criterion.

    The Shapley value of a criterion answers:
      'How much does this criterion contribute to the overall inconsistency
       compared to what it would contribute on average across all possible
       subsets of criteria?'

    This directly operationalizes your Omega paper — instead of consistency
    in pairwise comparison matrices, we're measuring consistency of LLM
    judge verdicts and attributing disagreement to specific evaluation axes.

    Steps:
      1. For each subset S of criteria, compute inconsistency using only S
      2. For each criterion c, compute its marginal contribution across all
         subsets that don't contain c
      3. Average the marginal contributions = Shapley value for c
    """
    n = len(criteria)

    if n == 0:
        return ShapleyAttribution(per_criterion={}, dominant_criterion="none")

    if n == 1:
        return ShapleyAttribution(
            per_criterion={criteria[0]: 1.0},
            dominant_criterion=criteria[0],
        )

    shapley_values: Dict[str, float] = {c: 0.0 for c in criteria}

    # iterate over all possible subsets of criteria
    for criterion in criteria:
        other_criteria = [c for c in criteria if c != criterion]
        marginal_contributions = []

        # consider all subsets of the other criteria
        for r in range(len(other_criteria) + 1):
            for subset in combinations(other_criteria, r):
                subset_without = list(subset)
                subset_with = list(subset) + [criterion]

                score_without = _inconsistency_score(verdicts, subset_without)
                score_with = _inconsistency_score(verdicts, subset_with)

                marginal = score_with - score_without
                marginal_contributions.append(marginal)

        shapley_values[criterion] = float(np.mean(marginal_contributions))

    # normalize so values sum to 1.0 (proportion of inconsistency attribution)
    total = sum(abs(v) for v in shapley_values.values())
    if total > 0:
        shapley_values = {
            k: round(abs(v) / total, 4)
            for k, v in shapley_values.items()
        }
    else:
        # uniform attribution if no inconsistency detected
        shapley_values = {k: round(1.0 / n, 4) for k in criteria}

    dominant = max(shapley_values, key=shapley_values.get)

    return ShapleyAttribution(
        per_criterion=shapley_values,
        dominant_criterion=dominant,
    )