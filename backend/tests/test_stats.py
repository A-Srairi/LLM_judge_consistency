import pytest
from app.models import Verdict, Winner
from app.services.stats.mcnemar import compute_positional_bias


def make_verdict(judge: str, winner: Winner, order: str) -> Verdict:
    return Verdict(
        judge_model=judge,
        winner=winner,
        criteria_scores={},
        reasoning="test",
        order=order,
        latency_ms=100.0,
    )


def test_no_positional_bias():
    """When verdicts are consistent regardless of order, bias should be low."""
    verdicts = []
    for i in range(10):
        verdicts.append(make_verdict("judge-1", Winner.A, "AB"))
        verdicts.append(make_verdict("judge-1", Winner.A, "BA"))

    result = compute_positional_bias(verdicts)

    assert result.flip_rate == 0.0
    assert result.is_significant is False


def test_perfect_positional_bias():
    """When verdict always flips with order, bias should be 1.0."""
    verdicts = []
    for i in range(10):
        verdicts.append(make_verdict("judge-1", Winner.A, "AB"))
        verdicts.append(make_verdict("judge-1", Winner.B, "BA"))

    result = compute_positional_bias(verdicts)

    assert result.flip_rate == 1.0
    assert result.is_significant is True


def test_partial_positional_bias():
    """Flip rate should reflect proportion of flipped verdicts."""
    verdicts = []
    # 5 consistent pairs
    for i in range(5):
        verdicts.append(make_verdict("judge-1", Winner.A, "AB"))
        verdicts.append(make_verdict("judge-1", Winner.A, "BA"))
    # 5 flipped pairs
    for i in range(5):
        verdicts.append(make_verdict("judge-1", Winner.A, "AB"))
        verdicts.append(make_verdict("judge-1", Winner.B, "BA"))

    result = compute_positional_bias(verdicts)

    assert result.flip_rate == 0.5


def test_raises_without_both_orders():
    """Should raise if only one order is present."""
    verdicts = [make_verdict("judge-1", Winner.A, "AB") for _ in range(5)]

    with pytest.raises(ValueError):
        compute_positional_bias(verdicts)
        

from app.services.stats.krippendorff import compute_inter_judge_agreement


def test_perfect_agreement():
    """When all judges agree, alpha should be high."""
    criteria = ["accuracy", "helpfulness"]
    verdicts = []
    for judge in ["judge-1", "judge-2", "judge-3"]:
        for i in range(5):
            verdicts.append(Verdict(
                judge_model=judge,
                winner=Winner.A,
                criteria_scores={
                    "accuracy":    {"A": 5.0, "B": 2.0},
                    "helpfulness": {"A": 5.0, "B": 2.0},
                },
                reasoning="test",
                order="AB",
                latency_ms=100.0,
            ))

    result = compute_inter_judge_agreement(verdicts, criteria)

    assert result.krippendorff_alpha > 0.7
    assert result.interpretation in ("good", "excellent")
    assert "accuracy" in result.per_criterion
    assert "helpfulness" in result.per_criterion


def test_single_judge_returns_perfect():
    """Single judge — nothing to compare, return 1.0 with a note."""
    verdicts = [
        Verdict(
            judge_model="judge-1",
            winner=Winner.A,
            criteria_scores={"accuracy": {"A": 4.0, "B": 2.0}},
            reasoning="test",
            order="AB",
            latency_ms=100.0,
        )
    ]
    result = compute_inter_judge_agreement(verdicts, ["accuracy"])
    assert result.krippendorff_alpha == 1.0
    

from app.services.stats.bootstrap import compute_bootstrap_ci


def test_perfect_reliability():
    """Consistent verdicts with no flips should score near 100."""
    verdicts = []
    for judge in ["judge-1", "judge-2"]:
        for i in range(5):
            verdicts.append(Verdict(
                judge_model=judge,
                winner=Winner.A,
                criteria_scores={},
                reasoning="test",
                order="AB",
                latency_ms=100.0,
            ))
            verdicts.append(Verdict(
                judge_model=judge,
                winner=Winner.A,
                criteria_scores={},
                reasoning="test",
                order="BA",
                latency_ms=100.0,
            ))

    score, ci = compute_bootstrap_ci(verdicts)

    assert score == 100.0
    assert ci.lower >= 90.0
    assert ci.upper == 100.0


def test_zero_reliability():
    """Perfect flips + full disagreement should score near 0."""
    verdicts = []
    for i in range(5):
        verdicts.append(Verdict(
            judge_model="judge-1",
            winner=Winner.A,
            criteria_scores={},
            reasoning="test",
            order="AB",
            latency_ms=100.0,
        ))
        verdicts.append(Verdict(
            judge_model="judge-1",
            winner=Winner.B,
            criteria_scores={},
            reasoning="test",
            order="BA",
            latency_ms=100.0,
        ))

    score, ci = compute_bootstrap_ci(verdicts)

    assert score < 60.0
    assert ci.lower < ci.upper


def test_ci_bounds_are_ordered():
    """Lower bound must always be <= upper bound."""
    verdicts = [
        Verdict(
            judge_model="judge-1",
            winner=Winner.A,
            criteria_scores={},
            reasoning="test",
            order="AB",
            latency_ms=100.0,
        )
        for _ in range(20)
    ]
    _, ci = compute_bootstrap_ci(verdicts)
    assert ci.lower <= ci.upper
    

from app.services.stats.shapley import compute_shapley_attribution


def test_shapley_values_sum_to_one():
    """Shapley values must always sum to 1.0."""
    criteria = ["accuracy", "helpfulness", "conciseness"]
    verdicts = []
    for judge in ["judge-1", "judge-2"]:
        for i in range(5):
            verdicts.append(Verdict(
                judge_model=judge,
                winner=Winner.A if i % 2 == 0 else Winner.B,
                criteria_scores={
                    "accuracy":    {"A": float(i + 1), "B": float(5 - i)},
                    "helpfulness": {"A": 3.0, "B": 3.0},
                    "conciseness": {"A": float(i % 3 + 1), "B": 2.0},
                },
                reasoning="test",
                order="AB" if i % 2 == 0 else "BA",
                latency_ms=100.0,
            ))

    result = compute_shapley_attribution(verdicts, criteria)

    total = sum(result.per_criterion.values())
    assert abs(total - 1.0) < 0.01
    assert result.dominant_criterion in criteria


def test_shapley_single_criterion():
    """Single criterion gets full attribution."""
    verdicts = [
        Verdict(
            judge_model="judge-1",
            winner=Winner.A,
            criteria_scores={"accuracy": {"A": 4.0, "B": 2.0}},
            reasoning="test",
            order="AB",
            latency_ms=100.0,
        )
    ]
    result = compute_shapley_attribution(verdicts, ["accuracy"])
    assert result.per_criterion["accuracy"] == 1.0
    assert result.dominant_criterion == "accuracy"


def test_shapley_returns_all_criteria():
    """Output must contain every input criterion."""
    criteria = ["accuracy", "helpfulness", "conciseness"]
    verdicts = [
        Verdict(
            judge_model="judge-1",
            winner=Winner.A,
            criteria_scores={c: {"A": 4.0, "B": 2.0} for c in criteria},
            reasoning="test",
            order="AB",
            latency_ms=100.0,
        )
    ]
    result = compute_shapley_attribution(verdicts, criteria)
    assert set(result.per_criterion.keys()) == set(criteria)