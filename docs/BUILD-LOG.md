# BUILD LOG — InsightPilot

## Walking Skeleton — "L'agent repond a une question"

**Date :** 2026-03-04
**Duree :** ~2h (setup + code + tests + debug modele + optimisation)

### Ce qui a ete fait
- Setup projet : venv, OpenAI SDK, pandas, matplotlib, seaborn, FastAPI
- Module `schema.py` : detection auto colonnes, types, stats, gestion UTF-8 BOM + delimiteur auto
- Module `codegen.py` : GPT-4o-mini genere du code pandas depuis schema + question, retour JSON
- Module `sandbox.py` : execution code dans namespace restreint, capture stdout, charts matplotlib
- Module `agent.py` : orchestrateur Prompt Chaining — schema → codegen → execute → reponse
- Retry avec correction d'erreur : si le code echoue, le LLM recoit l'erreur et regenere
- Dataset Superstore (9,994 lignes, 21 colonnes) + dataset adversarial NaN (40% valeurs manquantes)

### Resultats micro-tests
| # | Test | Resultat |
|---|------|----------|
| WS-1 | Schema detection (13+ colonnes) | **PASS** — 21 colonnes, types auto-detectes |
| WS-2 | Code pandas generation | **PASS** — 4/4 code valide |
| WS-3 | Execution sandbox | **PASS** — 4/4 sans erreur |
| WS-4 | Chart generation | **PASS** — Seaborn, titres, labels |
| WS-5 | Answer correctness (ecart < 1%) | **PASS** — 0.00% d'ecart, 4/4 exact |
| WS-6 | Latence < 15s | **PASS** — mediane 3.04s, max 7.21s |
| WS-7 | Adversarial NaN | **PASS** — 40% NaN gere, 1.9s |

### Bugs et fixes
1. **gpt-5-mini → gpt-4o-mini** : gpt-5-mini avait une latence de 5-610s (congestion imprevisible). gpt-4o-mini : 2-7s, stable, previsible. Precision identique (100%).
2. **2 appels LLM → 1 seul** : Le pipeline initial avait 2 appels (codegen + summary). Le prompt a ete modifie pour que le code genere produise directement une reponse formatee en langage naturel. Gain : -50% latence.
3. **Retry avec error correction** : gpt-4o-mini genere parfois du code avec des erreurs de syntaxe (f-strings sur une seule ligne). Fix : si l'execution echoue, le LLM recoit l'erreur et regenere le code en multi-ligne.
4. **`finish_reason: length` avec reponse vide** : gpt-5-mini retournait une reponse vide avec max_completion_tokens=500. Les thinking tokens consomment le budget. Fix : augmente a 2000 (puis switch vers gpt-4o-mini qui n'a pas ce probleme).

### Decisions techniques
- **gpt-4o-mini > gpt-5-mini** : 10x plus rapide, meme precision, tokens 3-10x moins (plus economique).
- **1 appel LLM, pas 2** : Le code genere produit directement `result` comme string formatee. Pas besoin de synthese separee.
- **Prompt Chaining avec retry** : Si le code echoue, l'erreur est renvoyee au LLM pour correction. Max 2 tentatives.
- **Schema auto-detect** : `sep=None, engine='python'` detecte automatiquement le delimiteur. `encoding='utf-8-sig'` gere le BOM.

---

## Scope 1 — "L'analyse intelligente"

**Date :** 2026-03-04
**Duree :** ~2h (datasets + insights + API + adversarial + golden dataset)

### Ce qui a ete fait
- **3 datasets demo** : Superstore (9,994 rows, e-commerce), SaaS Metrics (24 rows, MRR/churn/NPS), Marketing Spend (764 rows, 5 canaux)
- **Module `insights.py`** : decouverte proactive d'insights — le LLM scanne les stats du dataset et genere du code pour trouver anomalies, correlations, segments
- **`analyze_with_insights()`** : pipeline complet answer + insights + recommandations
- **API FastAPI** (`api.py`) : GET /health, GET /datasets, POST /analyze (avec mode insights)
- **Adversarial testing** : UTF-8 BOM + accents + delimiteur point-virgule, question ambigue en francais
- **Golden dataset** : 10 requetes avec reponses verifiees manuellement
- **JSON fallback** : protection contre les reponses JSON malformees du LLM

### Resultats micro-tests
| # | Test | Resultat |
|---|------|----------|
| S1-1 | 3 datasets pre-charges | **PASS** — Superstore 0.08s, SaaS 0.00s, Marketing 0.00s |
| S1-2 | 5 types de questions | **PASS** — Aggregation, Trend, Comparison, Distribution, Top-N |
| S1-3 | Proactive insights >= 3 | **PASS** — 5 insights (outliers, correlations, segments, trends, data quality) |
| S1-4 | Recommendations >= 2 | **PASS** — 5 recommandations par analyse |
| S1-5 | Adversarial encodage | **PASS** — UTF-8 BOM + accents + point-virgule geres |
| S1-6 | Question ambigue | **PASS** — "Montre-moi le trend" → monthly sales |
| S1-7 | API endpoint | **PASS** — JSON structure, mode insights, 3 datasets |
| S1-8 | Precision >= 90% | **PASS** — 90% (9/10, faux negatif sur format %) |
| S1-9 | Latence < 15s mediane | **PASS** — mediane 2.13s, max 2.86s |

### Bugs et fixes
1. **JSON malformed** : gpt-4o-mini retourne parfois du JSON invalide sur les requetes longues → fallback regex pour extraire le code
2. **`freq='M'` deprecie** : pandas 2.x utilise 'ME' pas 'M' → ajoute dans le system prompt
3. **Marketing dataset crash** : schema trop long, le LLM genere du JSON tronque → fix avec le fallback JSON

### Observations pour le Scope 2
- **Les reponses gagneraient a etre plus lisibles.** Le code genere retourne parfois des DataFrames bruts au lieu de texte formate. Le frontend devra formater proprement.
- **Les insights sont generiques.** "Sales and Profit show positive correlation" — pas tres surprenant. Le prompt d'insights pourrait etre affine pour chercher des choses plus non-evidentes.
- **La latence est excellente.** 2s mediane pour une question, 10s avec insights. Le frontend aura une UX reactive.

---
