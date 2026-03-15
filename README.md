# DataPilot

**Drop a CSV, ask a question, get charts + insights in seconds.**

AI data analyst powered by GPT-4o code generation. No SQL, no Excel, no code — just ask in plain language and get answers with visualizations.

**[Try it live](https://the-data-pilot.lovable.app)**

---

## How it works

```
CSV upload → Schema Detection → GPT-4o Codegen (pandas) → Sandbox Execution → Answer + Chart
                                                                    ↓ (optional)
                                                    GPT-4o-mini → Proactive Insights + Chart
```

1. Your CSV is parsed and its schema extracted (columns, types, stats, sample values)
2. GPT-4o generates pandas code to answer your question (JSON mode)
3. The code runs in a sandboxed environment — if it fails, one automatic retry with error feedback
4. You get a text answer + optional chart (dark-themed matplotlib/seaborn)
5. Optionally, GPT-4o-mini discovers 3-5 proactive insights with computed evidence

## Evaluation results

| Round | Model | Accuracy | Hallucinations | Decision |
|-------|-------|----------|----------------|----------|
| R1 | GPT-4o-mini | 55% (11/20) | 1 | **NO-GO** |
| R2 | GPT-4o + anti-hallucination prompt | 87.5% (17.5/20) | 0 | **CONDITIONAL GO** |

Evaluated on 20 golden questions (aggregation, trend, comparison, multi-step, adversarial). Median latency: 2.1s. Full eval: [`docs/EVAL-REPORT.md`](docs/EVAL-REPORT.md)

Key decision: model upgrade from GPT-4o-mini to GPT-4o was driven entirely by eval results — not intuition.

## Tech stack

| Component | Technology |
|-----------|-----------|
| LLM (main) | GPT-4o (OpenAI) — code generation |
| LLM (insights) | GPT-4o-mini (OpenAI) — proactive insights |
| Execution | pandas + matplotlib/seaborn in sandboxed exec() |
| Backend | FastAPI (Python) |
| Frontend | React + Tailwind (Lovable) |
| Hosting | Render ($7/mo) |

## Local setup

```bash
# Clone and setup
git clone https://github.com/Mehdibargach/datapilot.git
cd datapilot
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Add API keys
cp .env.example .env
# Edit .env with your OPENAI_API_KEY

# Run
uvicorn api:app --host 0.0.0.0 --port 8000
```

API endpoints:
- `GET /health` — health check
- `GET /datasets` — list demo datasets (superstore, saas, marketing)
- `POST /analyze` — ask a question about your CSV

## Project structure

```
api.py              ← FastAPI backend (3 endpoints)
agent.py            ← Pipeline orchestrator (analyze + insights)
codegen.py          ← GPT-4o code generation + meta-question detection
sandbox.py          ← Sandboxed pandas code execution
schema.py           ← CSV schema detection (multi-encoding)
insights.py         ← GPT-4o-mini proactive insight discovery
data/               ← Demo datasets (superstore, saas, marketing)
docs/
  EVAL-REPORT.md    ← Full eval with golden dataset (20 questions)
  ADR.md            ← Architecture Decision Records
```

## Built by

**Mehdi Bargach** — Builder PM · AI Products

[LinkedIn](https://www.linkedin.com/in/mehdi-bargach/)
