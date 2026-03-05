# Macro Retro — DataPilot

> Template from The Builder PM Method — POST-SHIP
> Fill this AFTER shipping. This is the bridge between V(n) and V(n+1).
> If you skip this, the macro-loop is broken — V2 decisions happen in your head instead of on paper.

---

**Project:** DataPilot
**Version shipped:** V1
**Eval Gate decision:** CONDITIONAL GO (87.5%, 0 hallucination)
**Date:** 2026-03-05

---

## 1. Harvest — What came out of the Eval Gate?

### Conditions (from CONDITIONAL GO)

| # | Condition | Level | Impact |
|---|-----------|-------|--------|
| 1 | G3 a 87.5% (seuil 90%) — ecart de 1 question (E8 calcul marge) | QUALITY | L'agent utilise avg(row margins) au lieu de total profit/total sales. Un utilisateur finance verrait l'erreur. |
| 2 | Chart generation rate 25% (2/8 questions qui meritaient un chart) | QUALITY | L'agent sait generer des charts corrects, mais ne le fait pas assez souvent. L'experience visuelle est incomplete. |
| 3 | CPA calculation (E10) — Email $0.50 vs $2.02 | QUALITY | Possible confusion colonne (CPC vs CPA). Un marketing manager verrait l'erreur. |
| 4 | Refus dates implicite (E17) — "$0.00" au lieu de "no data for 2023" | SIGNAL | Pas faux, mais trompeur. L'utilisateur pense que le marketing n'a rien depense au lieu de comprendre que les donnees n'existent pas. |

### Build Learnings (from Build Log)

- **Code deterministe > prompt probabiliste** pour les decisions binaires. La regex meta-questions est fiable a 100%, alors que le prompt patching causait des regressions.
- **Schema gap** : l'intention utilisateur ("streams") ≠ semantique des donnees ("Quantity all stores"). Le modele comprend la question mais les colonnes ne matchent pas. Pas un bug agent — un probleme de donnees.
- **Prompt rules fonctionnent quand elles sont specifiques.** La regle anti-hallucination a resolu E15 immediatement. Les instructions vagues ("be careful") ne marchent pas.

### User/PM Signals (from wild tests, demos, feedback)

- Pas de wild tests externes pour DataPilot V1 (SHIP direct apres eval)
- Le PM a catch le reclassement E8 (PARTIAL → INCORRECT) — confirme que l'audience finance detecterait l'erreur de marge
- Le micro-loop (55% → 87.5%) a prouve la valeur de l'eval formelle vs ad-hoc testing

---

## 2. Decision — What do we do next?

| Decision | When to use |
|----------|-------------|
| **ITERATE (V+1)** | At least one condition is worth fixing AND the product has more value to unlock |
| **STOP** | Product is good enough for its purpose. Conditions are minor or not worth the investment. |
| **PIVOT** | Fundamental assumption was wrong. The product works technically but solves the wrong problem. |

**Decision:** STOP

**Why (data-driven):**

DataPilot est le side project #3/5 dans le portfolio Builder PM. Son objectif = demontrer la maitrise du pattern AI Agent + fournir du materiel pour le livre (micro-loop, eval-driven development, anti-hallucination). Cet objectif est atteint a 100%.

Les 4 conditions sont des optimisations prompt (marge, CPA, chart rate, refus dates) qui amelioreraient l'experience mais ne changent pas la demonstration de competence. Le ROI d'un V2 est faible comparé a builder FeedbackSort (#4) et EvalKit (#5), qui ajoutent 2 nouvelles typologies au portfolio (Classification + AI Evaluation).

**Argument quantitatif :** fixer les 4 conditions amenerait DataPilot de 87.5% a ~95%. Mais passer de 3/5 projets SHIP a 5/5 a plus de valeur portfolio que passer de 87.5% a 95% sur un seul projet.

---

## 3. Bridge — Input for the next FRAME

> Section non applicable — decision = STOP.

---

## Completion

- [x] Eval Report reviewed
- [x] Decision documented with justification
- [x] Bridge section filled (N/A — STOP)
- [ ] Project Dossier updated with Macro Retro decision
- [ ] CLAUDE.md updated
