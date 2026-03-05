# DataPilot

## What this project is
AI agent that analyzes CSV data. Drop a CSV, ask a question in plain language, get charts + insights + actions in 10 seconds. Your data analyst on demand — no code, no Excel, no waiting.

## AI Typology
AI Agent (multi-step) — side project #3/5 in the Builder PM portfolio.

## Architecture Decisions (from 1-Pager)
- **Agent pattern**: Prompt Chaining (most reliable, predictable latency)
- **LLM**: GPT-4o (OpenAI) — code generation + summarization. Single model. (ADR-001: gpt-5-mini rejecte, ADR-004: gpt-4o-mini → gpt-4o apres eval)
- **Code execution**: Python subprocess sandbox (pandas + matplotlib/seaborn)
- **Backend**: FastAPI (Python) — same stack as DocuQuery + WatchNext
- **Frontend**: Lovable (React + Tailwind) — same as previous projects
- **Deploy**: Render ($7/mo)

## Current Phase
**COMPLETE — SHIP + MACRO RETRO (STOP)**

### EVALUATE — CONDITIONAL GO
- Round 1 (gpt-4o-mini) : 55%, 1 hallucination → NO-GO
- Micro-loop : prompt anti-hallucination + switch gpt-4o (ADR-004)
- Round 2 (gpt-4o) : 87.5%, 0 hallucination → CONDITIONAL GO

### SHIP — 2026-03-05
- Frontend : `https://the-data-pilot.lovable.app`
- Backend : `https://datapilot-backend.onrender.com`
- GitHub : `https://github.com/Mehdibargach/datapilot`

### MACRO RETRO — STOP
- Les 4 conditions sont des optimisations prompt, pas des bugs critiques
- ROI superieur a passer aux projets suivants (FeedbackSort, EvalKit)

### Walking Skeleton — DONE (7/7 PASS)
- Pipeline : CSV → schema → gpt-4o-mini codegen → sandbox exec → chart + answer
- Mediane 3.04s, max 7.21s, precision 100%
- ADR : gpt-4o-mini (pas gpt-5-mini), 1 appel LLM (pas 2), retry avec error correction

### Scope 1 — DONE (9/9 PASS)
- 3 datasets demo, 5 types de questions, insights proactifs, API endpoint
- Precision 90% (9/10), latence mediane 2.13s

### Scope 2 — DONE (6/6 PASS)
- Frontend Lovable (chat, upload, dataset selector, responsive)
- Backend deploye sur Render
- Conversation multi-tour (historique 5 echanges)
- Detection meta-questions (regex Python + prompt dedie)
- Fix hallucination insights (code execute > texte genere)
- Robustesse : multi-encodage CSV, try/except global, nettoyage code genere

### Apprentissages cles S2
- **Code deterministe > prompt probabiliste** pour la detection binaire (meta-questions)
- **Code execute > texte genere** pour les chiffres (insights)
- **Anti-pattern identifie : prompt-patching aveugle** (modifier prompt → push → regression → re-modifier)
- **Finding : schema gap** — l'intention utilisateur ("streams") ≠ semantique des donnees ("Quantity all stores")

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
