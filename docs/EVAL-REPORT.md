# Eval Report — DataPilot

> From The Builder PM Method — EVALUATE phase

**Project:** DataPilot
**Date:** 2026-03-05
**Evaluator:** Mehdi Bargach
**Build Version:** 2d5c55f (main) + micro-loop fixes (gpt-4o + anti-hallucination prompt)
**Golden Dataset Size:** 20 questions (+3 regression)

---

## Eval Gate Decision

**CONDITIONAL GO**

### Criteria Levels

| # | Critere | Level | Seuil | Resultat | Status |
|---|---------|-------|-------|----------|--------|
| G1 | Zero hallucination | **BLOCKING** | 0 donnees inventees sur 20 questions | 0 hallucination | **PASS** |
| G2 | Aggregation accuracy | **BLOCKING** | 100% sur les 4 questions aggregation | 4/4 = 100% | **PASS** |
| G3 | Overall accuracy | QUALITY | >= 90% (18/20 correct) | 17.5/20 = 87.5% | **FAIL** |
| G4 | Chart correctness | QUALITY | 100% des charts matchent les donnees | 2/2 generated = 100% | **PASS** (note: taux generation 25%) |
| G5 | Latency | SIGNAL | < 15s mediane | 2.1s mediane | **PASS** |
| G6 | Insight quality | SIGNAL | Insights avec vrais chiffres (pas de placeholder) | Non teste formellement | N/A |

### Decision Rules

| Decision | Condition | Action |
|----------|-----------|--------|
| **GO** | 0 BLOCKING fail + 0 QUALITY fail | → SHIP |
| **CONDITIONAL GO** | 0 BLOCKING fail + ≥1 QUALITY/SIGNAL fail | → SHIP with documented conditions |
| **NO-GO** | ≥1 BLOCKING fail | → Micro-loop BUILD (mandatory) |

**Decision: CONDITIONAL GO** — 0 BLOCKING fail, 1 QUALITY fail (G3: 87.5% < 90%). Conditions documentees ci-dessous.

### Conditions

1. **Chart generation rate** : 2/8 questions qui meritaient un chart l'ont obtenu (25%). Les charts generes sont corrects, mais le modele ne genere pas de chart sur toutes les questions pertinentes.
2. **Calcul de marge** : interpretation "average row margin" vs "total profit / total sales" donne des ecarts (3.88% vs 2.5% pour Furniture).
3. **CPA calculation** : Email $0.50 au lieu de $2.02 — possible confusion colonne Spend/Clicks vs Spend/Conversions.
4. **Refus dates implicite** : retourne "$0.00" au lieu de "no data for 2023" — techniquement pas faux, mais trompeur.

---

## Micro-loop History

### Round 1 — gpt-4o-mini, no prompt fixes (baseline)

| Metric | Value |
|--------|-------|
| Overall score | 55% (11/20) |
| Hallucinations | 1 (E15 — BLOCKING FAIL) |
| Model | gpt-4o-mini |
| Decision | **NO-GO** |

### Round 2 — gpt-4o + anti-hallucination prompt (current)

| Metric | Value |
|--------|-------|
| Overall score | 87.5% (17.5/20) |
| Hallucinations | 0 |
| Model | gpt-4o |
| Prompt changes | Anti-hallucination rule, date range rule, format reinforcement |
| Decision | **CONDITIONAL GO** |

**Improvement: +35 percentage points. BLOCKING fix resolved.**

---

## Regression Check (DOR)

> Verification que les features BUILD fonctionnent toujours avant d'evaluer la qualite.

| # | Dataset | Question | Expected | Result | Status |
|---|---------|----------|----------|--------|--------|
| R1 | Superstore | What is the total sales amount? | ~$2,297,200 | $2,297,200.86 | **PASS** |
| R2 | SaaS | What is the current MRR? | ~$282,209 | $282,208.99 | **PASS** |
| R3 | Marketing | What is the total marketing spend? | ~$91,429 | $91,429.01 | **PASS** |

**All PASS → proceed.**

---

## Golden Dataset

> Toutes les questions sont NOUVELLES — aucune reutilisee du BUILD.
> Structurees par TYPE, pas par feature.

### Question Types (adaptes pour data analysis)

| Type | Ce qu'il teste |
|------|---------------|
| **Aggregation** | Extraction d'un chiffre exact (somme, moyenne, %) |
| **Trend** | Analyse temporelle (evolution, prediction) |
| **Comparison** | Comparaison entre groupes/categories |
| **Multi-step** | Chaine d'operations (filtre + calcul + classement) |
| **Adversarial** | Refus correct, question ambigue, colonne inexistante |
| **Consistency** | Meme question 2x = memes faits |

### Questions

| # | Type | Dataset | Question | Expected Answer | Chart? |
|---|------|---------|----------|-----------------|--------|
| E1 | Aggregation | Superstore | What percentage of orders are shipped by Standard Class? | ~59.7% | Non |
| E2 | Aggregation | Superstore | How many unique customers are in the dataset? | 793 | Non |
| E3 | Aggregation | SaaS | What is the average churn rate over the entire period? | ~4.09% | Non |
| E4 | Aggregation | Marketing | What is the total revenue generated across all channels? | ~$365,934 | Non |
| E5 | Trend | SaaS | Which month had the worst churn rate and what was it? | July 2024, 10.65% | Oui |
| E6 | Trend | SaaS | How has the number of active customers evolved? | 203 (Jan 2024) → 534 (Dec 2025), croissance continue | Oui |
| E7 | Trend | Marketing | Which channel shows the best ROAS trend over time? | Email domine (~45x), les autres entre 1-3x | Oui |
| E8 | Comparison | Superstore | Which category has the worst profit margin? | Furniture (2.5%) vs Office Supplies (17.0%) vs Technology (17.4%) | Oui |
| E9 | Comparison | Superstore | Compare the number of orders by region | West 1611, East 1401, Central 1175, South 822 | Oui |
| E10 | Comparison | Marketing | Which channel has the lowest cost per conversion? | Email ($2.02), puis Meta ($33.70), Google ($37.55), TikTok ($63.58), LinkedIn ($157.48) | Oui |
| E11 | Multi-step | Superstore | What are the 3 sub-categories with the worst total profit? | Tables (-$17,725), Bookcases (-$3,473), Supplies (-$1,189) | Oui |
| E12 | Multi-step | Superstore | What is the average order value for orders placed in 2017? | ~$458.61 (avg across all years) ou calcul specifique 2017 | Non |
| E13 | Multi-step | SaaS | In which month did the company gain the most new customers, and how many? | September 2025, 48 new customers (ou December 2025, 58) | Non |
| E14 | Multi-step | Marketing | What is the conversion rate of TikTok Ads compared to the overall average? | TikTok ~0.77% vs overall avg — significativement inferieur | Non |
| E15 | Adversarial | Superstore | What is the customer satisfaction score? | Refus — pas de colonne satisfaction dans le dataset | Non |
| E16 | Adversarial | SaaS | Why did churn spike in July 2024? | Devrait constater le spike (10.65%, 23 churned) mais ne peut PAS expliquer le "pourquoi" (pas dans les donnees) | Non |
| E17 | Adversarial | Marketing | What was the marketing spend in 2023? | Refus ou "no data for 2023" — les donnees commencent en Oct 2025 | Non |
| E18 | Consistency | Superstore | What percentage of orders are shipped by Standard Class? | Meme reponse que E1 (~59.7%) | Non |
| E19 | Multi-step | SaaS | What is the lowest NPS score and when did it occur? | NPS 26, April 2024 | Non |
| E20 | Comparison | Marketing | Rank all 5 channels by total conversions | Email 1849, Google 922, Meta 720, TikTok 198, LinkedIn 103 | Oui |

---

## Answer Grading Rubric

| Grade | Critere | Score |
|-------|---------|-------|
| **CORRECT** | Chiffre exact (tolerance ±2%) ou analyse correcte | 1.0 |
| **PARTIAL** | Bon raisonnement mais chiffre imprecis ou incomplet | 0.5 |
| **INCORRECT** | Mauvaise reponse | 0.0 |
| **HALLUCINATION** | Invente un chiffre ou une donnee absente du dataset | -0.5 |

---

## Golden Dataset Results

| # | Type | Question | Answer | Answer Grade | Score | Latency | Chart OK? | Pattern |
|---|------|----------|--------|-------------|-------|---------|-----------|---------|
| E1 | Agg | Standard Class % | 59.72% | CORRECT | 1.0 | ~2.2s | N/A | — |
| E2 | Agg | Unique customers | 793 | CORRECT | 1.0 | ~2.0s | N/A | — |
| E3 | Agg | Avg churn rate | 4.09% | CORRECT | 1.0 | ~2.0s | N/A | — |
| E4 | Agg | Total revenue mkt | $365,933.82 | CORRECT | 1.0 | ~2.5s | N/A | — |
| E5 | Trend | Worst churn month | July 2024, 10.65% | CORRECT | 1.0 | ~3.5s | NO (expected) | — |
| E6 | Trend | Active customers | 203→534 | CORRECT | 1.0 | ~3.0s | YES | — |
| E7 | Trend | Best ROAS channel | "best ROAS... from the chart" | PARTIAL | 0.5 | ~3.0s | YES | Format Error |
| E8 | Comp | Worst margin cat | Furniture 3.88% (expected 2.5%) | INCORRECT | 0.0 | ~2.5s | NO | Calculation Error |
| E9 | Comp | Orders by region | W1611, E1401, C1175, S822 | CORRECT | 1.0 | ~2.0s | NO | — |
| E10 | Comp | Lowest CPA | Email $0.50 (expected $2.02) | PARTIAL | 0.5 | ~2.5s | NO | Calculation Error |
| E11 | Multi | Worst 3 sub-cats | Tables -17725, Bookcases -3473, Supplies -1189 | CORRECT | 1.0 | ~2.5s | NO | — |
| E12 | Multi | Avg order 2017 | $463.27 (~$458.61 ±1%) | CORRECT | 1.0 | ~2.5s | N/A | — |
| E13 | Multi | Most new customers | Dec 2025, 58 | CORRECT | 1.0 | ~2.0s | N/A | — |
| E14 | Multi | TikTok conv rate | 0.77 vs avg 3.73 | CORRECT | 1.0 | ~2.0s | N/A | — |
| E15 | Adv | Satisfaction | "does not contain customer satisfaction data" | CORRECT | 1.0 | ~2.0s | N/A | — |
| E16 | Adv | Why churn spike | "23 churned, MRR 5336" (factual, no speculation) | CORRECT | 1.0 | ~2.5s | N/A | — |
| E17 | Adv | Spend 2023 | "$0.00" (misleading, no explicit refusal) | PARTIAL | 0.5 | ~2.0s | N/A | Refusal Failure |
| E18 | Cons | Standard Class % | 59.72% (= E1) | CORRECT | 1.0 | ~2.2s | N/A | — |
| E19 | Multi | Lowest NPS | NPS 26, April 2024 | CORRECT | 1.0 | ~2.1s | N/A | — |
| E20 | Comp | Rank channels conv | Email 1849, Google 922, Meta 720, TikTok 198, LinkedIn 103 | CORRECT | 1.0 | ~2.9s | NO | — |

---

## Scores by Question Type

| Type | Count | Avg Score | Notes |
|------|-------|-----------|-------|
| Aggregation | 4 | 1.00 | 4/4 parfait |
| Trend | 3 | 0.83 | E7 PARTIAL (format) |
| Comparison | 4 | 0.63 | E8 INCORRECT, E10 PARTIAL (calcul marge/CPA) |
| Multi-step | 5 | 1.00 | 5/5 parfait |
| Adversarial | 3 | 0.83 | E17 PARTIAL (refus implicite) |
| Consistency | 1 | 1.00 | E18 = E1 |

---

## Failure Analysis

| # | Question | Pattern | Root Cause | Severity | Recommended Fix |
|---|----------|---------|-----------|----------|----------------|
| E7 | Best ROAS trend | Format Error | Answer delegates to chart sans nommer le channel (Email) | LOW | Prompt: "Always name the answer in text, even if a chart is generated" |
| E8 | Worst margin | Calculation Error | avg(row margins) = 3.88% vs total_profit/total_sales = 2.5% | MEDIUM | Prompt: "Profit margin = total profit / total sales * 100" |
| E10 | Lowest CPA | Calculation Error | CPA $0.50 vs expected $2.02 — possible CPC au lieu de CPA | MEDIUM | Schema enrichment: ajouter description colonnes dans schema_text |
| E17 | Spend 2023 | Refusal Failure | Retourne "$0.00" au lieu de dire "no data for 2023" | LOW | Prompt: renforcer la regle de refus pour dates hors range |

### Failure Pattern Taxonomy (adapte pour data analysis)

| Pattern | Description | Fix type |
|---------|-------------|----------|
| **Calculation Error** | Mauvais calcul (somme, moyenne, %) | Prompt ou retry |
| **Column Confusion** | Mauvaise colonne utilisee | Schema enrichment |
| **Code Error** | Code pandas plante | Retry + clean_code |
| **Hallucination** | Invente un chiffre absent des donnees | Prompt rule |
| **Refusal Failure** | Ne refuse pas quand il devrait | Prompt rule |
| **Format Error** | Bon calcul, mauvaise presentation | Prompt formatting |
| **Ambiguity Handling** | Question vague mal interpretee | Clarification prompt |

---

## ADR: Model Change gpt-4o-mini → gpt-4o

**Context:** Round 1 eval (gpt-4o-mini) scored 55% with 1 BLOCKING hallucination. The hypothesis was that ~50% of failures were model capability issues.

**Decision:** Switch to gpt-4o for code generation.

**Results:**
- Score: 55% → 87.5% (+32.5pp)
- Hallucinations: 1 → 0
- Code errors: 3 → 0
- Calculation errors: 1 → 2 (different questions, E8 reclasse INCORRECT apres review PM)
- Latency: 3.5s median → 2.1s median (faster!)

**Trade-off:** gpt-4o costs ~10x more per token than gpt-4o-mini. Acceptable for a demo/portfolio project. For production at scale, would need cost optimization.

**Verdict:** gpt-4o is the right model for DataPilot. The quality difference is decisive.

---

## Recommendations

### CONDITIONAL GO — Ship with documented conditions

1. **Ship as-is** pour demo et portfolio. 1 INCORRECT (E8 marge) + 3 PARTIAL = cas edge, pas de hallucination.
2. **Conditions documentees** :
   - G3 a 87.5% (seuil 90%) — ecart de 1 question (E8 calcul marge avg row vs weighted)
   - Chart generation rate (25%) — le modele ne genere pas toujours un chart quand c'est utile
   - CPA calculation (E10) — possible confusion colonne
   - Refus dates hors range = implicite ($0.00) au lieu d'explicite
3. **Pas de micro-loop supplementaire** — les fixes restants sont des optimisations prompt, pas des bugs critiques. Le produit est fiable a 87.5% sans hallucination.
4. **Next step** : SHIP (deploy, frontend connect, demo-ready)
