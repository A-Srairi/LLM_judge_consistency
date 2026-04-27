import uuid
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from app.services.stats.temperature import compute_temperature_sensitivity


from app.config import get_settings
from app.models import (
    AuditRequest,
    AuditResult,
    AuditResponse,
    ErrorResponse,
    BootstrappedCI,
)
from app.services.judge import run_audit
from app.services.stats.mcnemar import compute_positional_bias
from app.services.stats.krippendorff import compute_inter_judge_agreement
from app.services.stats.bootstrap import compute_bootstrap_ci
from app.services.stats.shapley import compute_shapley_attribution

settings = get_settings()

app = FastAPI(
    title="LLM Judge Consistency Auditor",
    description="Detects positional bias, inter-judge disagreement, and attribution in LLM-as-judge evaluation pipelines.",
    version="0.1.0",
)

# allow frontend dev server to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


@app.get("/models")
async def list_models():
    return {
        "default_judges": settings.default_judges,
        "default_criteria": settings.default_criteria,
        "byok_supported_providers": ["openai", "anthropic", "groq", "openrouter"],
    }


@app.post("/audit", response_model=AuditResult)
async def create_audit(
    request: AuditRequest,
    x_api_key: Optional[str] = Header(default=None),
):
    """
    Main endpoint — runs a full consistency audit on a (prompt, A, B) triple.

    Optional header X-Api-Key: pass your own API key for premium models.
    If not provided, defaults to Groq free-tier judges.
    """
    judges = request.judges or settings.default_judges
    criteria = request.criteria or settings.default_criteria

    # validate: if user requests non-groq models, they must supply a key
    non_groq = [j for j in judges if not j.startswith("groq/")]
    if non_groq and not x_api_key:
        raise HTTPException(
            status_code=402,
            detail=f"Models {non_groq} require a BYOK API key via X-Api-Key header.",
        )

    try:
        # 1. run all judge calls concurrently
        verdicts = await run_audit(request, byok_key=x_api_key)

        if not verdicts:
            raise HTTPException(status_code=500, detail="No verdicts returned from judges.")

        # 2. stats pipeline
        positional_bias = compute_positional_bias(verdicts)
        inter_judge = compute_inter_judge_agreement(verdicts, criteria)
        reliability_score, ci = compute_bootstrap_ci(verdicts)
        shapley = compute_shapley_attribution(verdicts, criteria)

        # temperature sensitivity — only meaningful if multiple temps were requested
        temperatures_used = request.temperatures or [0.0]
        temp_sensitivity = None
        if len(temperatures_used) > 1:
            temp_sensitivity = compute_temperature_sensitivity(
                verdicts, judges, temperatures_used
            )

        # 3. overall winner — majority vote across all verdicts
        from collections import Counter
        winner_counts = Counter(v.winner for v in verdicts)
        overall_winner = winner_counts.most_common(1)[0][0]

        # 4. human readable summary
        bias_pct = round(positional_bias.flip_rate * 100)
        agreement = inter_judge.interpretation
        verdict_summary = (
            f"Response {overall_winner.value} preferred overall. "
            f"Reliability: {reliability_score}/100. "
            f"Positional bias: {bias_pct}% flip rate "
            f"({'significant' if positional_bias.is_significant else 'not significant'}). "
            f"Inter-judge agreement: {agreement}."
        )

        return AuditResult(
            audit_id=str(uuid.uuid4()),
            prompt=request.prompt,
            response_a=request.response_a,
            response_b=request.response_b,
            judges_used=judges,
            criteria_used=criteria,
            n_samples=request.n_samples or settings.default_n_samples,
            verdicts=verdicts,
            temperatures_used=temperatures_used,
            temperature_sensitivity=temp_sensitivity,
            reliability_score=reliability_score,
            confidence_interval=ci,
            positional_bias=positional_bias,
            inter_judge_agreement=inter_judge,
            shapley_attribution=shapley,
            overall_winner=overall_winner,
            verdict_summary=verdict_summary,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))