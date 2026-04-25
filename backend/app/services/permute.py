from typing import List, Tuple
from app.models import AuditRequest


JUDGE_PROMPT_TEMPLATE = """You are an expert evaluator assessing the quality of two AI-generated responses.

Your task is to evaluate which response better addresses the given prompt based on the specified criteria.

## Prompt
{prompt}

## Response {label_first}
{response_first}

## Response {label_second}
{response_second}

## Evaluation Criteria
{criteria_block}

## Instructions
1. Evaluate both responses on each criterion using a score from 1 (poor) to 5 (excellent)
2. Decide which response is overall better: {label_first}, {label_second}, or tie
3. Respond ONLY in the following JSON format — no extra text before or after:

{{
  "winner": "{label_first}" | "{label_second}" | "tie",
  "criteria_scores": {{
    {criteria_scores_template}
  }},
  "reasoning": "your brief reasoning here (2-3 sentences)"
}}"""


def _build_criteria_block(criteria: List[str]) -> str:
    descriptions = {
        "accuracy":    "How factually correct and precise is the response?",
        "helpfulness": "How well does the response address the user's actual need?",
        "conciseness": "Is the response appropriately concise without sacrificing quality?",
        "clarity":     "How clear and easy to understand is the response?",
        "safety":      "Is the response safe and free from harmful content?",
    }
    lines = []
    for i, criterion in enumerate(criteria, 1):
        desc = descriptions.get(criterion, f"Evaluate the response on {criterion}.")
        lines.append(f"{i}. {criterion.capitalize()}: {desc}")
    return "\n".join(lines)


def _build_criteria_scores_template(criteria: List[str], label_first: str, label_second: str) -> str:
    lines = []
    for criterion in criteria:
        lines.append(
            f'"{criterion}": {{"{label_first}": <score 1-5>, "{label_second}": <score 1-5>}}'
        )
    return ",\n    ".join(lines)


def build_evaluation_prompts(
    request: AuditRequest,
    criteria: List[str],
) -> List[Tuple[str, str]]:
    """
    Builds evaluation prompt pairs for positional bias testing.

    For each sample we create TWO prompts:
      - AB order: response_a shown first as 'Response A', response_b second as 'Response B'
      - BA order: response_b shown first as 'Response A', response_a second as 'Response B'

    Returns a list of (prompt_text, order) tuples.
    order is either "AB" or "BA".
    """
    criteria_block = _build_criteria_block(criteria)
    prompts = []

    # AB order — response_a first
    ab_scores_template = _build_criteria_scores_template(criteria, "A", "B")
    ab_prompt = JUDGE_PROMPT_TEMPLATE.format(
        prompt=request.prompt,
        label_first="A",
        label_second="B",
        response_first=request.response_a,
        response_second=request.response_b,
        criteria_block=criteria_block,
        criteria_scores_template=ab_scores_template,
    )
    prompts.append((ab_prompt, "AB"))

    # BA order — response_b first, but still labeled A and B
    # this is the key trick: same labels, swapped content
    ba_scores_template = _build_criteria_scores_template(criteria, "A", "B")
    ba_prompt = JUDGE_PROMPT_TEMPLATE.format(
        prompt=request.prompt,
        label_first="A",
        label_second="B",
        response_first=request.response_b,
        response_second=request.response_a,
        criteria_block=criteria_block,
        criteria_scores_template=ba_scores_template,
    )
    prompts.append((ba_prompt, "BA"))

    return prompts