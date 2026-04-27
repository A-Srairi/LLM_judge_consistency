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
    order: str
    latency_ms: float
    temperature: float = 0.0


class AuditRequest(BaseModel):
    prompt: str = Field(..., min_length=10, max_length=5000)
    response_a: str = Field(..., min_length=1, max_length=10000)
    response_b: str = Field(..., min_length=1, max_length=10000)
    judges: Optional[List[str]] = None
    criteria: Optional[List[str]] = None
    n_samples: Optional[int] = Field(default=2, ge=1, le=5)
    temperatures: Optional[List[float]] = Field(default=[0.0])


class PositionalBias(BaseModel):
    flip_rate: float
    mcnemar_statistic: float
    mcnemar_pvalue: float
    is_significant: bool


class InterJudgeAgreement(BaseModel):
    krippendorff_alpha: float
    interpretation: str
    per_criterion: Dict[str, float]


class ShapleyAttribution(BaseModel):
    per_criterion: Dict[str, float]
    dominant_criterion: str


class BootstrappedCI(BaseModel):
    lower: float
    upper: float
    confidence_level: float = 0.95


class AuditResult(BaseModel):
    audit_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "completed"

    prompt: str
    response_a: str
    response_b: str
    judges_used: List[str]
    criteria_used: List[str]
    n_samples: int
    temperatures_used: List[float] = [0.0]

    verdicts: List[Verdict]

    reliability_score: float
    confidence_interval: BootstrappedCI
    positional_bias: PositionalBias
    inter_judge_agreement: InterJudgeAgreement
    shapley_attribution: ShapleyAttribution
    temperature_sensitivity: Optional[Dict] = None

    overall_winner: Winner
    verdict_summary: str


class AuditResponse(BaseModel):
    audit_id: str
    status: str
    message: str


class ErrorResponse(BaseModel):
    error: str
    detail: str