import numpy as np
from typing import List, Callable
from app.models import Verdict, Winner, BootstrappedCI


def _compute_reliability(verdicts: List[Verdict]) -> float:
    """
    Computes a raw reliability score from 0-100.

    Logic:
      - Start at 100
      - Penalize for positional flips
      - Penalize for inter-judge disagreement
      - Result is how trustworthy this evaluation is
    """
    if not verdicts:
        return 0.0

    total = len(verdicts)

    # penalty 1: how often do judges disagree on winner
    winners = [v.winner for v in verdicts]
    most_common = max(set(winners), key=winners.count)
    disagreement_rate = sum(1 for w in winners if w != most_common) / total

    # penalty 2: how often does order flip the verdict
    ab = [v for v in verdicts if v.order == "AB"]
    ba = [v for v in verdicts if v.order == "BA"]
    flip_count = 0
    for a, b in zip(ab, ba):
        if a.winner != b.winner:
            flip_count += 1
    flip_rate = flip_count / max(len(ab), 1)

    # weighted combination — flips penalize more than disagreement
    reliability = 100.0 - (flip_rate * 50.0) - (disagreement_rate * 30.0)
    return max(0.0, min(100.0, reliability))


def compute_bootstrap_ci(
    verdicts: List[Verdict],
    n_bootstrap: int = 1000,
    confidence_level: float = 0.95,
) -> tuple[float, BootstrappedCI]:
    """
    Bootstraps the reliability score to produce a confidence interval.

    Returns:
      - point estimate (reliability score on full sample)
      - BootstrappedCI with lower and upper bounds
    """
    if not verdicts:
        return 0.0, BootstrappedCI(lower=0.0, upper=0.0)

    rng = np.random.default_rng(seed=42)
    n = len(verdicts)
    bootstrap_scores = []

    for _ in range(n_bootstrap):
        # sample with replacement
        indices = rng.integers(0, n, size=n)
        sample = [verdicts[i] for i in indices]
        score = _compute_reliability(sample)
        bootstrap_scores.append(score)

    bootstrap_scores = np.array(bootstrap_scores)

    alpha = 1.0 - confidence_level
    lower = float(np.percentile(bootstrap_scores, 100 * alpha / 2))
    upper = float(np.percentile(bootstrap_scores, 100 * (1 - alpha / 2)))
    point_estimate = _compute_reliability(verdicts)

    return round(point_estimate, 2), BootstrappedCI(
        lower=round(lower, 2),
        upper=round(upper, 2),
        confidence_level=confidence_level,
    )