import numpy as np
from typing import List, Dict
from app.models import Verdict, Winner


def compute_temperature_sensitivity(
    verdicts: List[Verdict],
    judges: List[str],
    temperatures: List[float],
) -> Dict:
    """
    For each judge, measures how much verdict distribution shifts
    as temperature increases.

    Returns:
      - per_judge_sensitivity: 0.0 = perfectly stable, 1.0 = completely unstable
      - optimal_temperature: temperature at which each judge is most self-consistent
      - verdict_heatmap: {judge: {temp: {"A": %, "B": %, "tie": %}}}
    """
    if len(temperatures) < 2:
        return {
            "per_judge_sensitivity": {j: 0.0 for j in judges},
            "optimal_temperature": {j: temperatures[0] for j in judges},
            "verdict_heatmap": {},
            "most_stable_judge": judges[0] if judges else None,
            "least_stable_judge": judges[-1] if judges else None,
        }

    # build verdict heatmap — AB order only for consistency
    scoring_verdicts = [v for v in verdicts if v.order == "AB"]

    heatmap = {}
    for judge in judges:
        heatmap[judge] = {}
        for temp in temperatures:
            temp_verdicts = [
                v for v in scoring_verdicts
                if v.judge_model == judge and v.temperature == temp
            ]
            if not temp_verdicts:
                heatmap[judge][temp] = {"A": 0.0, "B": 0.0, "tie": 0.0}
                continue

            total = len(temp_verdicts)
            a_pct = round(sum(1 for v in temp_verdicts if v.winner == Winner.A) / total, 3)
            b_pct = round(sum(1 for v in temp_verdicts if v.winner == Winner.B) / total, 3)
            tie_pct = round(sum(1 for v in temp_verdicts if v.winner == Winner.TIE) / total, 3)
            heatmap[judge][temp] = {"A": a_pct, "B": b_pct, "tie": tie_pct}

    # sensitivity score — average shift in dominant verdict % across temperature steps
    per_judge_sensitivity = {}
    optimal_temperature = {}

    for judge in judges:
        temp_distributions = [heatmap[judge][t] for t in temperatures]

        # measure how much the A% shifts across temperatures
        a_pcts = [d["A"] for d in temp_distributions]
        b_pcts = [d["B"] for d in temp_distributions]

        a_std = float(np.std(a_pcts))
        b_std = float(np.std(b_pcts))

        # sensitivity = average std across A and B distributions
        sensitivity = round((a_std + b_std) / 2, 4)
        per_judge_sensitivity[judge] = sensitivity

        # optimal temperature = where the judge is most decisive (least tie%)
        tie_pcts = [(t, d["tie"]) for t, d in zip(temperatures, temp_distributions)]
        optimal_temperature[judge] = min(tie_pcts, key=lambda x: x[1])[0]

    most_stable = min(per_judge_sensitivity, key=per_judge_sensitivity.get)
    least_stable = max(per_judge_sensitivity, key=per_judge_sensitivity.get)

    return {
        "per_judge_sensitivity": per_judge_sensitivity,
        "optimal_temperature": optimal_temperature,
        "verdict_heatmap": heatmap,
        "most_stable_judge": most_stable,
        "least_stable_judge": least_stable,
    }