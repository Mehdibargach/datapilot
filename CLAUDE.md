# InsightPilot

## What this project is
AI agent that analyzes CSV data. Drop a CSV, ask a question in plain language, get charts + insights + actions in 10 seconds. Your data analyst on demand — no code, no Excel, no waiting.

## AI Typology
AI Agent (multi-step) — side project #3/5 in the Builder PM portfolio.

## Architecture Decisions (from 1-Pager)
- **Agent pattern**: Prompt Chaining (most reliable, predictable latency)
- **LLM**: GPT-5-mini (OpenAI) — code generation + summarization. Single model.
- **Code execution**: Python subprocess sandbox (pandas + matplotlib/seaborn)
- **Backend**: FastAPI (Python) — same stack as DocuQuery + WatchNext
- **Frontend**: Lovable (React + Tailwind) — same as previous projects
- **Deploy**: Render ($7/mo)

## Current Phase
BUILD — Scope 1 : "L'analyse intelligente"

### Walking Skeleton — DONE (7/7 PASS)
- Pipeline : CSV → schema → gpt-4o-mini codegen → sandbox exec → chart + answer
- Mediane 3.04s, max 7.21s, precision 100%
- ADR : gpt-4o-mini (pas gpt-5-mini), 1 appel LLM (pas 2), retry avec error correction

### Scope 1 — Ce qu'on ajoute
- 3 datasets pre-charges (Superstore, SaaS Metrics, Marketing Spend)
- 5 types de questions (aggregation, trend, comparison, distribution, top-N)
- Decouverte proactive d'insights (anomalies, correlations, outliers)
- Recommandations d'actions concretes
- Adversarial : encodage UTF-8 BOM, question ambigue
- API endpoint POST /analyze

### Micro-tests Scope 1
| # | Test | Pass Criteria |
|---|------|---------------|
| S1-1 | 3 datasets pre-charges | Superstore, SaaS, Marketing — chargent en < 2s |
| S1-2 | 5 types de questions | Aggregation, trend, comparison, distribution, top-N — toutes correctes |
| S1-3 | Proactive insights | >= 3 insights non-demandes sur Superstore |
| S1-4 | Action recommendations | >= 2 actions concretes par analyse |
| S1-5 | Adversarial encodage | CSV UTF-8 BOM avec accents → pas d'erreur |
| S1-6 | Adversarial question ambigue | "Montre-moi le trend" → clarification ou choix logique |
| S1-7 | API endpoint | POST /analyze → JSON (answer, chart, insights, recommendations) |
| S1-8 | Precision golden dataset | >= 90% sur 10 requetes |
| S1-9 | Latence | < 15s mediane sur 10 requetes |

## Riskiest Assumption
"Un agent AI peut analyser n'importe quel CSV structure, generer des insights corrects avec des charts precis, en moins de 15 secondes par requete, avec moins de 5% d'erreur sur les calculs, sans code ni configuration."

## Scope (6 IN, 4 OUT)
**IN:** CSV upload + auto-detection, Question naturelle → pandas → execution, Charts auto, 3 datasets demo, Insights proactifs, Recommandations d'actions
**OUT:** Panel code visible, Persistence session, Export rapport, Multi-fichier JOIN

## Anti-patterns
- NEVER decompose into backend → frontend → integration
- Always vertical slices (Walking Skeleton → Scopes)

## Build Rules (applies to all projects)
1. Micro-test = gate, pas une etape. Code → Micro-test PASS → Doc → Commit.
2. Le gameplan fait autorite sur les donnees de test.
3. Checklist qualite walkthrough — audience non-technique.
4. Pas de mode batch.
5. Test first, code if needed.
6. UX dans les prompts — no jargon leaked to user.
7. PM Validation Gate — apres micro-tests PASS, AVANT commit : attendre GO explicite du PM.

## Build Checklist
See `/Users/mbargach/Claude Workspace/Projects/builder-pm/templates/build-checklist-claude.md`
