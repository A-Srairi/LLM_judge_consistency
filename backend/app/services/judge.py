import asyncio
import json
import time
import re
from typing import List, Optional
import litellm
from app.models import AuditRequest, Verdict, Winner
from app.services.permute import build_evaluation_prompts
from app.config import get_settings

settings = get_settings()

# tell litellm to stay quiet
litellm.set_verbose = False


def _parse_verdict(
    raw_response: str,
    judge_model: str,
    order: str,
    latency_ms: float,
    criteria: List[str],
) -> Verdict:
    """
    Parses the raw LLM response string into a structured Verdict.
    Handles messy JSON, markdown fences, and partial responses gracefully.
    """
    # strip markdown code fences if present
    cleaned = raw_response.strip()
    cleaned = re.sub(r"^```json\s*", "", cleaned)
    cleaned = re.sub(r"^```\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        # try to extract json from somewhere in the response
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group())
            except json.JSONDecodeError:
                return _fallback_verdict(judge_model, order, latency_ms, criteria)
        else:
            return _fallback_verdict(judge_model, order, latency_ms, criteria)

    # normalize winner
    raw_winner = str(data.get("winner", "tie")).strip().upper()
    if raw_winner == "A":
        # in BA order, the judge saw response_b first labeled as A
        # so we need to flip the winner back to reflect actual responses
        winner = Winner.B if order == "BA" else Winner.A
    elif raw_winner == "B":
        winner = Winner.A if order == "BA" else Winner.B
    else:
        winner = Winner.TIE

    # normalize criteria scores
    raw_scores = data.get("criteria_scores", {})
    criteria_scores = {}
    for criterion in criteria:
        if criterion in raw_scores:
            scores = raw_scores[criterion]
            raw_a = scores.get("A", 3.0)
            raw_b = scores.get("B", 3.0)
            # flip scores back if BA order
            if order == "BA":
                criteria_scores[criterion] = {
                    "A": float(raw_b),
                    "B": float(raw_a),
                }
            else:
                criteria_scores[criterion] = {
                    "A": float(raw_a),
                    "B": float(raw_b),
                }
        else:
            criteria_scores[criterion] = {"A": 3.0, "B": 3.0}

    reasoning = str(data.get("reasoning", "No reasoning provided."))

    return Verdict(
        judge_model=judge_model,
        winner=winner,
        criteria_scores=criteria_scores,
        reasoning=reasoning,
        order=order,
        latency_ms=latency_ms,
    )


def _fallback_verdict(
    judge_model: str,
    order: str,
    latency_ms: float,
    criteria: List[str],
) -> Verdict:
    """Returns a tie verdict when parsing fails completely."""
    return Verdict(
        judge_model=judge_model,
        winner=Winner.TIE,
        criteria_scores={c: {"A": 3.0, "B": 3.0} for c in criteria},
        reasoning="Failed to parse judge response.",
        order=order,
        latency_ms=latency_ms,
    )


async def _call_judge(
    prompt_text: str,
    order: str,
    judge_model: str,
    criteria: List[str],
    byok_key: Optional[str] = None,
) -> Verdict:
    """Makes a single async LLM call and returns a parsed Verdict."""
    start = time.time()

    # build litellm kwargs
    kwargs = {
        "model": judge_model,
        "messages": [{"role": "user", "content": prompt_text}],
        "temperature": 0.0,   # deterministic — we want consistent judgments
        "max_tokens": 512,
        "response_format": {"type": "json_object"},
    }

    # inject BYOK key if provided
    if byok_key:
        kwargs["api_key"] = byok_key

    # use default groq key if no BYOK
    if not byok_key and judge_model.startswith("groq/"):
        kwargs["api_key"] = settings.groq_api_key

    try:
        response = await litellm.acompletion(**kwargs)
        raw = response.choices[0].message.content or ""
    except Exception as e:
        raw = f'{{"winner": "tie", "criteria_scores": {{}}, "reasoning": "Judge call failed: {str(e)}"}}'

    latency_ms = round((time.time() - start) * 1000, 1)
    return _parse_verdict(raw, judge_model, order, latency_ms, criteria)


async def run_audit(
    request: AuditRequest,
    byok_key: Optional[str] = None,
) -> List[Verdict]:
    """
    Fans out all judge calls with a semaphore to avoid overwhelming the API.
    """
    judges = request.judges or settings.default_judges
    criteria = request.criteria or settings.default_criteria
    n_samples = request.n_samples or settings.default_n_samples

    # limit to 5 concurrent calls at a time
    semaphore = asyncio.Semaphore(5)

    async def throttled_call(prompt_text, order, judge):
        async with semaphore:
            return await _call_judge(prompt_text, order, judge, criteria, byok_key)

    tasks = []
    for _ in range(n_samples):
        prompts = build_evaluation_prompts(request, criteria)
        for prompt_text, order in prompts:
            for judge in judges:
                tasks.append(throttled_call(prompt_text, order, judge))

    verdicts = await asyncio.gather(*tasks, return_exceptions=False)
    return list(verdicts)