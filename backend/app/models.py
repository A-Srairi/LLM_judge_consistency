from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum
from datetime import datetime
import uuid


class Winner(str, Enum):
    A = "A"
    B = "B"
    TIE = "tie"


class Verdict(BaseModel):
    judge_model: str
    winner: Winner
    criteria_scores: Dict[str, Dict[str, float]]
    reasoning: str
    order: str  # "AB" or "BA" — which response was shown first
    latency_ms: float


class AuditRequest(BaseModel):
    prompt: str = Field(..., min_length=10, max_length=5000)
    response_a: str = Field(..., min_length=1, max_length=10000)
    response_b: str = Field(..., min_length=1, max_length=10000)
    judges: Optional[List[str]] = None       # uses default_judges if None
    criteria: Optional[List[str]] = None     # uses default_criteria if None
    n_samples: Optional[int] = Field(default=10, ge=1, le=20)


class PositionalBias(BaseModel):
    flip_rate: float          # how often order change flips the verdict
    mcnemar_statistic: float
    mcnemar_pvalue: float
    is_significant: bool      # True if p < 0.05


class InterJudgeAgreement(BaseModel):
    krippendorff_alpha: float
    interpretation: str       # "poor", "fair", "good", "excellent"
    per_criterion: Dict[str, float]


class ShapleyAttribution(BaseModel):
    per_criterion: Dict[str, float]   # criterion -> share of inconsistency
    dominant_criterion: str           # which criterion drives most disagreement


class BootstrappedCI(BaseModel):
    lower: float
    upper: float
    confidence_level: float = 0.95


class AuditResult(BaseModel):
    audit_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "completed"

    # inputs (echoed back)
    prompt: str
    response_a: str
    response_b: str
    judges_used: List[str]
    criteria_used: List[str]
    n_samples: int

    # raw outputs
    verdicts: List[Verdict]

    # statistical outputs
    reliability_score: float          # 0-100 composite
    confidence_interval: BootstrappedCI
    positional_bias: PositionalBias
    inter_judge_agreement: InterJudgeAgreement
    shapley_attribution: ShapleyAttribution

    # summary
    overall_winner: Winner
    verdict_summary: str              # human-readable one-liner


class AuditResponse(BaseModel):
    audit_id: str
    status: str
    message: str


class ErrorResponse(BaseModel):
    error: str
    detail: str