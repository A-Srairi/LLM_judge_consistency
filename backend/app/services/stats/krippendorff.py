import numpy as np
import pandas as pd
from typing import List, Dict
from app.models import Verdict, InterJudgeAgreement


def _interpret_alpha(alpha: float) -> str:
    if alpha < 0.0:
        return "no agreement"
    elif alpha < 0.2:
        return "poor"
    elif alpha < 0.4:
        return "fair"
    elif alpha < 0.6:
        return "moderate"
    elif alpha < 0.8:
        return "good"
    else:
        return "excellent"


def _krippendorff_alpha_interval(matrix: np.ndarray) -> float:
    """
    Manual Krippendorff's alpha for interval data.
    matrix shape: (n_raters, n_items)
    """
    matrix = np.array(matrix, dtype=float)
    n_raters, n_items = matrix.shape

    o = 0.0
    n_pairs = 0
    for item in range(n_items):
        values = matrix[:, item]
        values = values[~np.isnan(values)]
        if len(values) < 2:
            continue
        for i in range(len(values)):
            for j in range(i + 1, len(values)):
                o += (values[i] - values[j]) ** 2
                n_pairs += 1

    if n_pairs == 0:
        return 1.0
    o = o / n_pairs

    all_values = matrix.flatten()
    all_values = all_values[~np.isnan(all_values)]
    if len(all_values) < 2:
        return 1.0

    e = 0.0
    n = len(all_values)
    for i in range(n):
        for j in range(i + 1, n):
            e += (all_values[i] - all_values[j]) ** 2
    e = e / (n * (n - 1) / 2)

    if e == 0:
        return 1.0

    return 1.0 - (o / e)


def _krippendorff_alpha_nominal(matrix: np.ndarray) -> float:
    """
    Manual Krippendorff's alpha for nominal data.
    matrix shape: (n_raters, n_items)
    """
    matrix = np.array(matrix, dtype=float)
    n_raters, n_items = matrix.shape

    o = 0.0
    n_pairs = 0
    for item in range(n_items):
        values = matrix[:, item]
        values = values[~np.isnan(values)]
        if len(values) < 2:
            continue
        for i in range(len(values)):
            for j in range(i + 1, len(values)):
                o += 0.0 if values[i] == values[j] else 1.0
                n_pairs += 1

    if n_pairs == 0:
        return 1.0
    o = o / n_pairs

    all_values = matrix.flatten()
    all_values = all_values[~np.isnan(all_values)]
    if len(all_values) < 2:
        return 1.0

    n = len(all_values)
    e = 0.0
    pairs = 0
    for i in range(n):
        for j in range(i + 1, n):
            e += 0.0 if all_values[i] == all_values[j] else 1.0
            pairs += 1
    e = e / pairs if pairs > 0 else 0.0

    if e == 0:
        return 1.0

    return 1.0 - (o / e)


def compute_inter_judge_agreement(
    verdicts: List[Verdict],
    criteria: List[str],
) -> InterJudgeAgreement:

    judges = list({v.judge_model for v in verdicts})

    if len(judges) < 2:
        return InterJudgeAgreement(
            krippendorff_alpha=1.0,
            interpretation="only one judge — no agreement to measure",
            per_criterion={c: 1.0 for c in criteria},
        )

    scoring_verdicts = [v for v in verdicts if v.order == "AB"]

    winner_map = {"A": 0, "B": 1, "tie": 2}
    matrix_rows = []
    for judge in judges:
        judge_verdicts = [v for v in scoring_verdicts if v.judge_model == judge]
        row = [winner_map.get(v.winner.value, np.nan) for v in judge_verdicts]
        matrix_rows.append(row)

    matrix = np.array(matrix_rows, dtype=float)

    try:
        if np.nanstd(matrix) == 0:
            overall_alpha = 1.0
        else:
            overall_alpha = _krippendorff_alpha_nominal(matrix)
    except Exception:
        overall_alpha = 0.0

    per_criterion: Dict[str, float] = {}

    for criterion in criteria:
        alphas = []

        for response_label in ["A", "B"]:
            response_rows = []
            for judge in judges:
                judge_verdicts = [v for v in scoring_verdicts if v.judge_model == judge]
                scores = []
                for v in judge_verdicts:
                    if criterion in v.criteria_scores:
                        score = v.criteria_scores[criterion].get(response_label, np.nan)
                        scores.append(float(score))
                    else:
                        scores.append(np.nan)
                response_rows.append(scores)

            response_matrix = np.array(response_rows, dtype=float)

            try:
                if np.nanstd(response_matrix) == 0:
                    alphas.append(1.0)
                else:
                    alpha_val = _krippendorff_alpha_interval(response_matrix)
                    alphas.append(float(alpha_val))
            except Exception:
                alphas.append(0.0)

        per_criterion[criterion] = round(float(np.mean(alphas)), 4)

    return InterJudgeAgreement(
        krippendorff_alpha=round(overall_alpha, 4),
        interpretation=_interpret_alpha(overall_alpha),
        per_criterion=per_criterion,
    )