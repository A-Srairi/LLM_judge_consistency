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