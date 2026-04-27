# LLM Judge Consistency Auditor

A deployed tool that measures, quantifies, and visualizes unreliability in LLM-as-judge evaluation pipelines.

[![Python](https://img.shields.io/badge/Python-3.9+-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-blue)](https://react.dev)
[![License](https://img.shields.io/badge/License-MIT-gray)](LICENSE)

---

## The Problem

LLM-as-judge has become the de facto standard for evaluating AI outputs at scale. But how reliable are these judges?

When you ask GPT-4 to compare two responses, you're implicitly assuming it is:
- **Positionally unbiased** — its verdict doesn't depend on which response is shown first
- **Internally consistent** — it gives the same verdict regardless of temperature setting
- **Calibrated** — different judge models agree on what "accuracy" or "helpfulness" means

These assumptions are largely untested. This tool tests them systematically.

---

## What It Does

Given a prompt and two candidate responses, the auditor:

1. **Runs N evaluation trials** across multiple judge models at multiple temperatures
2. **Permutes presentation order** (AB and BA) to detect positional bias
3. **Computes statistical consistency metrics** across all verdicts
4. **Attributes disagreement** to specific evaluation criteria using Shapley values
5. **Visualizes everything** in a live dashboard

---

## Key Findings

Running this tool on a logic riddle (objectively correct answer exists) with three Groq models across five temperature settings (0.0 → 1.0) revealed:

### Finding 1 — Model capability confounds evaluation

`llama-3.1-8b` rated a confidently wrong but well-structured response as correct in the majority of trials. `llama-3.3-70b` and `qwen3-32b` correctly identified the right answer every time.

**Implication:** A pipeline relying solely on smaller judge models systematically rewards well-formatted wrong answers over correct concise ones.

### Finding 2 — Criteria labels are not measurements

Krippendorff's alpha on `accuracy` was **-0.25** across judges on the riddle task — worse than random chance. This means judges don't share a common interpretation of what "accuracy" means. The disagreement is structured, not random.

`conciseness` showed **+0.40** agreement across the same judges — surface-level properties are more reliably evaluated than semantic correctness.

### Finding 3 — Temperature sensitivity varies dramatically by model

| Model | Sensitivity Score | Behavior |
|---|---|---|
| llama-3.3-70b-versatile | 0.00 | Stable across all temperatures |
| qwen3-32b | 0.00 | Stable across all temperatures |
| llama-3.1-8b-instant | 0.40 | Erratic — flips verdict at temp=0.3, recovers at temp=0.5, flips again at temp=1.0 |

**Implication:** For reliable evaluation pipelines, model choice matters more than temperature choice. But temperature=0.0 is optimal for all models tested.

### Finding 4 — Helpfulness drives most inter-judge inconsistency

Shapley attribution consistently shows `helpfulness` accounting for 60-70% of inter-judge disagreement across different prompt types. Judges have fundamentally different models of what constitutes a "helpful" response.

---

## Statistical Methods

### Positional Bias — McNemar's Test
For each judge, we run N trials with AB order and N trials with BA order. McNemar's test checks whether the flip rate (verdicts that change when order changes) is statistically significant (p < 0.05).

### Inter-Judge Agreement — Krippendorff's Alpha
Measures agreement across judge models on both overall verdicts (nominal) and per-criterion scores (interval). Values range from -1 (systematic disagreement) to 1 (perfect agreement). Values below 0.4 indicate unreliable evaluation.

### Inconsistency Attribution — Shapley Values
Treats each evaluation criterion as a player in a cooperative game. Each criterion's Shapley value represents its marginal contribution to overall inconsistency across all possible subsets of criteria — directly operationalizing cooperative game theory for evaluation pipelines.

*This methodology extends the author's published work on Shapley-based consistency analysis in pairwise comparison matrices (Omega Journal, under review).*

### Temperature Sensitivity
For each judge model, measures the standard deviation of verdict distributions across temperature settings. A score of 0.0 indicates perfect stability; higher scores indicate the model's evaluation is temperature-dependent.

### Reliability Score
Composite 0-100 score with bootstrapped 95% confidence intervals. Penalizes for positional flip rate (weighted 50%) and inter-judge disagreement (weighted 30%).

---

## Architecture

```
judge-auditor/
├── backend/                    # FastAPI + Python
│   ├── app/
│   │   ├── main.py             # API endpoints
│   │   ├── models.py           # Pydantic schemas
│   │   ├── services/
│   │   │   ├── judge.py        # Async multi-model fan-out
│   │   │   ├── permute.py      # AB/BA prompt builder
│   │   │   └── stats/
│   │   │       ├── mcnemar.py        # Positional bias
│   │   │       ├── krippendorff.py   # Inter-judge agreement
│   │   │       ├── bootstrap.py      # Confidence intervals
│   │   │       ├── shapley.py        # Criterion attribution
│   │   │       └── temperature.py    # Sensitivity analysis
│   └── tests/
└── frontend/                   # React + Tailwind
    └── src/
        ├── components/
        │   ├── AuditForm.jsx
        │   ├── ResultsDashboard.jsx
        │   ├── BiasChart.jsx
        │   ├── ShapleyWaterfall.jsx
        │   ├── VerdictTable.jsx
        │   ├── ReliabilityGauge.jsx
        │   └── KeyInput.jsx
        └── hooks/
            └── useAudit.js
```

**Key design decisions:**
- Stats engine is completely decoupled from LLM layer — all statistical modules are pure Python, testable without any API calls
- All LLM calls are async with semaphore throttling — 60 concurrent calls complete in ~3 seconds
- BYOK (Bring Your Own Key) architecture — users supply their own API keys for non-default models, stored only in sessionStorage, never persisted server-side

---

## API

### `POST /audit`

```json
{
  "prompt": "string",
  "response_a": "string",
  "response_b": "string",
  "judges": ["groq/llama-3.3-70b-versatile", "groq/qwen/qwen3-32b"],
  "criteria": ["accuracy", "helpfulness", "conciseness"],
  "n_samples": 2,
  "temperatures": [0.0, 0.5, 1.0]
}
```

Optional header: `X-Api-Key: your_key` for non-Groq models.

**Response includes:**
- `reliability_score` — 0-100 composite with 95% CI
- `positional_bias` — flip rate + McNemar p-value
- `inter_judge_agreement` — Krippendorff alpha overall + per criterion
- `shapley_attribution` — per-criterion inconsistency contribution
- `temperature_sensitivity` — per-judge sensitivity scores + verdict heatmap
- `verdicts` — raw judge outputs for full transparency

### `GET /models`
Returns available judge models and which require BYOK.

### `GET /health`
Health check.

---

## Running Locally

**Prerequisites:** Python 3.9+, Node.js 20+, Docker Desktop

```bash
# 1. Clone
git clone https://github.com/A-Srairi/LLM_judge_consistency
cd LLM_judge_consistency

# 2. Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Environment
cp .env.example .env
# Add your GROQ_API_KEY — free at console.groq.com

# 4. Start services
cd ..
docker compose up -d

# 5. Run backend
cd backend
uvicorn app.main:app --reload --port 8000

# 6. Run frontend (new terminal)
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`

---

## Default Judge Models (Free — No Key Required)

| Model | Provider | Notes |
|---|---|---|
| llama-3.3-70b-versatile | Groq | Primary judge — most stable |
| llama-3.1-8b-instant | Groq | Faster, less reliable on reasoning |
| qwen/qwen3-32b | Groq | Reasoning model — uses chain-of-thought |

All default judges run on Groq's free tier. To use OpenAI or Anthropic models, supply your own API key via the BYOK field in the UI.

---

## Tests

```bash
cd backend
python -m pytest tests/test_stats.py -v
```

12 tests covering all statistical modules — zero LLM calls required.

---

## Author

**Mohamed Aziz Srairi**
Data Scientist — Tunis, Tunisia
[LinkedIn](https://linkedin.com/in/m-aziz-srairi/) · [GitHub](https://github.com/A-Srairi)