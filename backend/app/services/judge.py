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

litellm.set_verbose = False


def _parse_verdict(
    raw_response: str,
    judge_model: str,
    order: str,
    latency_ms: float,
    criteria: List[str],
    temperature: float = 0.0,
) -> Verdict:
    cleaned = raw_response.strip()

    # strip Qwen3 chain-of-thought thinking block
    cleaned = re.sub(r"<think>.*?</think>", "", cleaned, flags=re.DOTALL).strip()
    cleaned = re.sub(r"^```json\s*", "", cleaned)
    cleaned = re.sub(r"^```\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group())
            except json.JSONDecodeError:
                return _fallback_verdict(judge_model, order, latency_ms, criteria, temperature)
        else:
            return _fallback_verdict(judge_model, order, latency_ms, criteria, temperature)

    raw_winner = str(data.get("winner", "tie")).strip().upper()
    if raw_winner == "A":
        winner = Winner.B if order == "BA" else Winner.A
    elif raw_winner == "B":
        winner = Winner.A if order == "BA" else Winner.B
    else:
        winner = Winner.TIE

    raw_scores = data.get("criteria_scores", {})
    criteria_scores = {}
    for criterion in criteria:
        if criterion in raw_scores:
            scores = raw_scores[criterion]
            raw_a = scores.get("A", 3.0)
            raw_b = scores.get("B", 3.0)
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
        temperature=temperature,
    )


def _fallback_verdict(
    judge_model: str,
    order: str,
    latency_ms: float,
    criteria: List[str],
    temperature: float = 0.0,
) -> Verdict:
    return Verdict(
        judge_model=judge_model,
        winner=Winner.TIE,
        criteria_scores={c: {"A": 3.0, "B": 3.0} for c in criteria},
        reasoning="Failed to parse judge response.",
        order=order,
        latency_ms=latency_ms,
        temperature=temperature,
    )


async def _call_judge(
    prompt_text: str,
    order: str,
    judge_model: str,
    criteria: List[str],
    temperature: float = 0.0,
    byok_key: Optional[str] = None,
) -> Verdict:
    start = time.time()

    kwargs = {
        "model": judge_model,
        "messages": [{"role": "user", "content": prompt_text}],
        "temperature": temperature,
        "max_tokens": 512,
    }

    if "gpt" in judge_model:
        kwargs["response_format"] = {"type": "json_object"}

    if byok_key:
        kwargs["api_key"] = byok_key

    if not byok_key and judge_model.startswith("groq/"):
        kwargs["api_key"] = settings.groq_api_key

    try:
        response = await litellm.acompletion(**kwargs)
        raw = response.choices[0].message.content or ""
    except Exception as e:
        raw = f'{{"winner": "tie", "criteria_scores": {{}}, "reasoning": "Judge call failed: {str(e)}"}}'

    latency_ms = round((time.time() - start) * 1000, 1)
    return _parse_verdict(raw, judge_model, order, latency_ms, criteria, temperature)


async def run_audit(
    request: AuditRequest,
    byok_key: Optional[str] = None,
) -> List[Verdict]:
    judges = request.judges or settings.default_judges
    criteria = request.criteria or settings.default_criteria
    n_samples = request.n_samples or settings.default_n_samples
    temperatures = request.temperatures or [0.0]

    semaphore = asyncio.Semaphore(5)

    async def throttled_call(prompt_text, order, judge, temp):
        async with semaphore:
            return await _call_judge(
                prompt_text, order, judge, criteria, temp, byok_key
            )

    tasks = []
    for temp in temperatures:
        for _ in range(n_samples):
            prompts = build_evaluation_prompts(request, criteria)
            for prompt_text, order in prompts:
                for judge in judges:
                    tasks.append(
                        throttled_call(prompt_text, order, judge, temp)
                    )

    verdicts = await asyncio.gather(*tasks, return_exceptions=False)
    return list(verdicts)