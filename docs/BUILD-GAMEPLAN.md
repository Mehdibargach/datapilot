# BUILD Gameplan

> Template from The Builder PM Method — BUILD phase (start)

---

**Project Name:** InsightPilot
**Date:** 2026-03-04
**Cycle Appetite:** 1 semaine
**MVP Features (from 1-Pager):**
1. CSV upload + auto-detection colonnes
2. Question naturelle → code pandas → execution sandbox
3. Generation de charts automatique
4. 3 datasets pre-charges (Superstore, SaaS, Marketing)
5. Decouverte proactive d'insights
6. Recommandations d'actions

**Riskiest Assumption (from 1-Pager):**
"Un agent AI peut analyser n'importe quel CSV structure, generer des insights corrects avec des charts precis, en moins de 15 secondes par requete, avec moins de 5% d'erreur sur les calculs, sans que l'utilisateur ecrive du code ou configure quoi que ce soit."

---

## Context Setup

**CLAUDE.md** du projet a configurer avec : Problem, Solution, Architecture Decisions du 1-Pager.

---

## Walking Skeleton — "L'agent repond a une question"

> Le chemin le plus fin possible de bout en bout.

**What it does :** On donne un fichier CSV et une question en langage naturel. L'agent detecte le schema, genere du code pandas, l'execute dans un sandbox, produit un chart, et retourne la reponse.

**End-to-end path :** CSV file → schema detection → LLM genere code pandas → execution sandbox → chart matplotlib → reponse JSON (answer + chart)

**Done when :** On peut poser 3 questions differentes au Superstore dataset et obtenir 3 reponses correctes avec charts en moins de 15 secondes chacune.

**Micro-tests :**

| # | Test | Pass Criteria |
|---|------|---------------|
| WS-1 | CSV upload + schema detection | Superstore : 13+ colonnes detectees avec types corrects (dates, numeriques, categories) |
| WS-2 | Code pandas generation | Code valide genere par le LLM, zero erreur de syntaxe |
| WS-3 | Execution sandbox | Code execute sans erreur, retourne un resultat (DataFrame, valeur, ou serie) |
| WS-4 | Chart generation | Chart matplotlib/seaborn genere et sauvegarde en PNG lisible |
| WS-5 | Answer correctness | "Total des ventes ?" → reponse = somme reelle de la colonne Sales du CSV (ecart < 1%) |
| WS-6 | Latence | < 15s end-to-end (schema + LLM + execution + chart) |
| WS-7 | Adversarial : CSV avec 40% NaN | Le code gere les valeurs manquantes sans planter, mentionne les donnees manquantes |

**Donnees de test :** Superstore dataset (Kaggle, 9,994 lignes, 13 colonnes)

→ **RITUAL: Skeleton Check** — Le LLM genere-t-il du code pandas correct et executable sur un vrai dataset ? La latence est-elle sous 15s ?
- Si NON → On sait vite. Pivot ou kill.
- Si OUI → Scope 1.

---

## Scope 1 — "L'analyse intelligente"

**What it adds :** Datasets pre-charges, insights proactifs, recommandations d'actions, cas adversariaux, API endpoint.

**Done when :** Un utilisateur peut cliquer sur un dataset demo, poser une question, recevoir une reponse + chart + insights proactifs + recommandations — le tout via une API.

**Micro-tests :**

| # | Test | Pass Criteria |
|---|------|---------------|
| S1-1 | 3 datasets pre-charges | Superstore, SaaS Metrics, Marketing Spend — tous chargent en < 2s |
| S1-2 | 5 types de questions | Aggregation, trend, comparison, distribution, top-N — toutes correctes |
| S1-3 | Proactive insights | >= 3 insights non-demandes generes automatiquement sur Superstore |
| S1-4 | Action recommendations | >= 2 actions concretes et specifiques par analyse |
| S1-5 | Adversarial : encodage UTF-8 BOM | CSV avec accents et BOM → pas d'erreur |
| S1-6 | Adversarial : question ambigue | "Montre-moi le trend" sans precision → clarification ou choix logique de la colonne |
| S1-7 | API endpoint | POST /analyze retourne JSON (answer, chart base64, insights, recommendations) |
| S1-8 | Precision golden dataset | >= 90% sur 10 requetes verifiees manuellement |
| S1-9 | Latence | < 15s mediane sur 10 requetes |

---

## Scope 2 — "Le produit fini"

**What it adds :** Frontend Lovable (upload, chat, charts inline), deploy Render, demo-ready.

**Done when :** Un visiteur peut aller sur l'URL, cliquer sur un dataset demo, poser une question, et voir la reponse + chart + insights dans une interface propre.

**Micro-tests :**

| # | Test | Pass Criteria |
|---|------|---------------|
| S2-1 | Upload CSV | Drag & drop → preview des 5 premieres lignes affichees |
| S2-2 | Chat interface | Question → reponse + chart affiche inline dans la conversation |
| S2-3 | Dataset selector | 3 datasets pre-charges cliquables, chargement instantane |
| S2-4 | Mobile responsive | Utilisable sur 375px width (chat + charts lisibles) |
| S2-5 | Deploy Render | Backend live, frontend connecte, demo fonctionnelle sur URL publique |
| S2-6 | Demo script 2min | Le script demo complet (dataset → question → insight → surprise → reco) executable en live sans accroc |

---

## Exit Criteria (BUILD → EVALUATE)

- [ ] Les 6 features MVP fonctionnelles de bout en bout
- [ ] Riskiest Assumption testee (Skeleton Check passe)
- [ ] Open Questions du 1-Pager resolues ou converties en ADR
- [ ] Build Log a jour
- [ ] Pret pour evaluation formelle contre les Success Metrics
