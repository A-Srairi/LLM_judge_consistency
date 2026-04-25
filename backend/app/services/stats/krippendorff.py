import numpy as np
import pingouin as pg
import pandas as pd
from typing import List, Dict
from app.models import Verdict, InterJudgeAgreement


def _interpret_alpha(alpha: float) -> str:
    """Krippendorff's alpha interpretation thresholds."""
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


def compute_inter_judge_agreement(
    verdicts: List[Verdict],
    criteria: List[str],
) -> InterJudgeAgreement:
    """
    Measures how much judges agree with each other.

    Krippendorff's alpha:
      1.0  = perfect agreement
      0.0  = agreement by chance
     <0.0  = systematic disagreement (worse than chance)

    We compute it twice:
      1. Overall — on the final winner verdict (A/B/tie encoded as 0/1/2)
      2. Per criterion — on the score each judge gave per criterion
    """

    judges = list({v.judge_model for v in verdicts})

    if len(judges) < 2:
        return InterJudgeAgreement(
            krippendorff_alpha=1.0,
            interpretation="only one judge — no agreement to measure",
            per_criterion={c: 1.0 for c in criteria},
        )

    # --- overall alpha on winner verdicts ---
    winner_map = {"A": 0, "B": 1, "tie": 2}

    # build matrix: rows = judges, columns = evaluation instances
    instances = list(range(len(verdicts) // len(judges)))
    matrix_rows = []

    for judge in judges:
        judge_verdicts = [v for v in verdicts if v.judge_model == judge]
        row = [winner_map.get(v.winner.value, np.nan) for v in judge_verdicts]
        matrix_rows.append(row)

    matrix = np.array(matrix_rows, dtype=float)

    # pingouin expects a DataFrame with shape (n_raters, n_items)
    df = pd.DataFrame(matrix)
    try:
        # if all values are identical, variance is 0 — perfect agreement by definition
        if np.nanstd(matrix) == 0:
            overall_alpha = 1.0
        else:
            alpha_result = pg.krippendorff_alpha(df, dtype="nominal")
            overall_alpha = float(alpha_result)
    except Exception:
        overall_alpha = 0.0

    # --- per-criterion alpha on scores ---
    per_criterion: Dict[str, float] = {}

    for criterion in criteria:
        crit_rows = []
        for judge in judges:
            judge_verdicts = [v for v in verdicts if v.judge_model == judge]
            scores = []
            for v in judge_verdicts:
                # criteria_scores shape: {"accuracy": {"A": 4.0, "B": 3.0}}
                if criterion in v.criteria_scores:
                    # use the difference A-B as a single signal
                    a_score = v.criteria_scores[criterion].get("A", np.nan)
                    b_score = v.criteria_scores[criterion].get("B", np.nan)
                    scores.append(a_score - b_score)
                else:
                    scores.append(np.nan)
            crit_rows.append(scores)

        crit_matrix = np.array(crit_rows, dtype=float)
        crit_df = pd.DataFrame(crit_matrix)
        try:
            if np.nanstd(crit_matrix) == 0:
                per_criterion[criterion] = 1.0
            else:
                crit_alpha = pg.krippendorff_alpha(crit_df, dtype="interval")
                per_criterion[criterion] = round(float(crit_alpha), 4)
        except Exception:
            per_criterion[criterion] = 0.0

    return InterJudgeAgreement(
        krippendorff_alpha=round(overall_alpha, 4),
        interpretation=_interpret_alpha(overall_alpha),
        per_criterion=per_criterion,
    )