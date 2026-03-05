# Project Dossier — DataPilot

> Template from The Builder PM Method — post-SHIP
> Portfolio piece. Updated after shipping.

---

**Project Name:** DataPilot
**One-liner:** Drop a CSV, ask a question in plain language, get charts + insights in 2 seconds.
**Live URL:** `https://the-data-pilot.lovable.app` (frontend) + `https://datapilot-backend.onrender.com` (API)
**GitHub:** `https://github.com/Mehdibargach/datapilot`
**Date Shipped:** 2026-03-05

---

## 1-Pager Summary

**Problem:** Les équipes business (marketing, e-commerce, SaaS) passent 30-60 minutes dans Excel pour répondre à UNE question sur leurs données. ChatGPT perd tout après 30 min. Les outils BI (Tableau, Power BI) sont trop complexes pour un non-dev.

**User:** Marketing managers, ops leads, fondateurs startup — toute personne qui exporte des CSV et veut des réponses sans coder.

**Solution:** Un agent AI qui prend un CSV, comprend la question en langage naturel, génère du code d'analyse automatiquement, l'exécute dans un environnement sécurisé, et retourne la réponse + un chart — en 2 secondes.

---

## Architecture

```
Question (texte) + CSV
        ↓
   [Schema Extraction]  — Lit les colonnes, types, premières lignes
        ↓
   [Code Generation]    — GPT-4o génère du code pandas
        ↓
   [Sandbox Execution]  — Python subprocess isolé (pandas + matplotlib)
        ↓
   Answer (texte) + Chart (PNG) + Insights proactifs
```

**Pattern:** Prompt Chaining (pas ReAct) — le plus fiable, latence prévisible.
**Un seul appel LLM** — le code génère directement la réponse formatée, pas besoin d'un 2ème appel pour résumer.

---

## Key ADRs

| # | Decision | Choice | Why |
|---|----------|--------|-----|
| ADR-001 | Quel modèle pour générer le code ? | GPT-4o-mini (BUILD) → GPT-4o (EVAL) | GPT-5-mini : latence imprévisible (5-610s). GPT-4o-mini : rapide mais 55% en eval. GPT-4o : 87.5% + 0 hallucination. |
| ADR-002 | Combien d'appels au modèle par question ? | 1 seul | 2 appels ajoutaient 3s sans valeur. Le code génère directement `result = f"..."`. |
| ADR-003 | Comment détecter les questions sur la méthode ? | Regex Python | Le code déterministe bat le probabiliste pour les décisions binaires. Modifier le prompt causait des régressions. |
| ADR-004 | Upgrade modèle après eval | GPT-4o-mini → GPT-4o | Score 55% → 87.5%. Multi-step : 40% → 100%. Adversarial : 17% → 83%. Zéro hallucination. |

---

## Eval Results

**Method:** Golden dataset de 20 questions NOUVELLES (pas celles du BUILD), structurées par type.

| Metric | Target | Actual | Pass/Fail |
|--------|--------|--------|-----------|
| Zero hallucination | 0/20 | 0/20 | **PASS** |
| Aggregation accuracy | 100% | 100% (4/4) | **PASS** |
| Overall accuracy | ≥90% | 87.5% (17.5/20) | FAIL |
| Chart correctness | 100% | 100% (2/2 générés) | **PASS** |
| Latency | <15s median | 2.1s | **PASS** |

**Decision:** CONDITIONAL GO — 0 BLOCKING fail, accuracy à 2.5pp du seuil.

**Micro-loop history:** Round 1 (gpt-4o-mini) = 55% + 1 hallucination → NO-GO → prompt fixes + model upgrade → Round 2 (gpt-4o) = 87.5% + 0 hallucination → CONDITIONAL GO.

---

## What I Learned

1. **Technical:** Un seul appel LLM bien configuré bat deux appels chaînés. Le code déterministe (regex) bat le prompt probabiliste pour les décisions binaires. GPT-4o est décisivement meilleur que GPT-4o-mini pour la génération de code analytique complexe.

2. **Product:** Les micro-tests du BUILD (22/22 PASS) ne garantissent PAS la qualité sur de nouvelles questions. L'eval avec un golden dataset NOUVEAU est indispensable — c'est là qu'on découvre les vrais problèmes. "In AI, shipping is easy. Evaluating is hard."

3. **Process:** Le prompt-patching aveugle (modifier le prompt → push → regression → re-modifier) est un anti-pattern. Tester localement d'abord. La règle anti-hallucination dans le prompt a résolu le BLOCKING fail immédiatement — les prompt rules fonctionnent quand elles sont précises et non ambiguës.

---

## Content Extracted

- [ ] Book chapter: Ch. 4 (Agent — build walkthrough), Ch. 6 (Eval — micro-loop NO-GO → CONDITIONAL GO)
- [ ] LinkedIn post: "55% → 87.5% in one micro-loop" / "In AI, shipping is easy. Evaluating is hard."
- [ ] Newsletter: DataPilot case study (eval-driven development)
- [ ] STAR story for interviews: "Caught a hallucination in production eval, fixed it with one prompt rule + model upgrade"

---

## STAR Story (Interview-Ready)

**Situation:** Building an AI data analyst agent as part of a portfolio of 5 AI products. Each project uses a different AI pattern (RAG, Recommendation, Agent, Classification, Evaluation).

**Task:** Ship a working agent that takes any CSV, answers natural language questions with charts, with zero hallucinations and <15s latency.

**Action:**
- Built prompt chaining pipeline (schema → code generation → sandbox → answer) in 3 vertical slices
- Ran formal evaluation with 20-question golden dataset structured by difficulty type
- Round 1: 55% accuracy, 1 hallucination → NO-GO. Diagnosed: 50% prompt-fixable, 50% model capability
- Added anti-hallucination rule + upgraded model (gpt-4o-mini → gpt-4o)
- Round 2: 87.5% accuracy, 0 hallucinations → CONDITIONAL GO

**Result:** Shipped a reliable data analysis agent (87.5% accuracy, 2.1s median, zero hallucinations) with documented eval methodology that proved the value of structured AI evaluation over ad-hoc testing.
