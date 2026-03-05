# Builder PM 1-Pager

> Template from The Builder PM Method — FRAME phase

---

**Project Name:** DataPilot
**One-liner:** Depose un CSV, pose une question en francais, recois charts + insights + actions en 10 secondes.
**Date:** 2026-03-04
**Builder PM Method Phase:** AI Agent (multi-step) — side project #3/5 dans le portfolio Builder PM.

---

## Problem

1. **30-60 minutes d'Excel pour UNE question.** Les equipes business (marketing, e-commerce, SaaS, finance) exportent des CSV depuis leurs outils (Shopify, Google Ads, Stripe...), puis ouvrent Excel, font des tableaux croises, des formules, des graphiques — tout ca pour repondre a une seule question. Chaque semaine.

2. **ChatGPT perd tout apres 30 min.** ChatGPT Code Interpreter peut analyser des donnees, mais la session expire, les fichiers disparaissent, et il faut tout re-uploader. C'est un couteau suisse, pas un outil dedie.

3. **Les outils BI sont trop complexes.** Tableau, Power BI, Looker — puissants mais faits pour les equipes data. Un marketing manager ne va pas apprendre SQL pour savoir quel canal baisse.

4. **Personne ne cherche ce que tu n'as PAS demande.** Tous les outils attendent ta question. Aucun ne scanne les donnees pour dire "hey, il y a un truc bizarre ici que tu n'as pas vu."

### Comment le marche resout ca aujourd'hui

| Outil | Approche | Limite |
|-------|----------|--------|
| Julius AI (600K users, $20-70/mo) | Chat + donnees, bons charts | Code cache, pas de datasets demo, pas d'insights proactifs |
| ChatGPT Code Interpreter ($20/mo) | Python dans un chat generique | Session expire 30min, fichiers perdus, UI generique |
| Hex ($36-75/editeur/mo) | Notebooks collaboratifs puissants | Fait pour les data teams, trop technique pour un non-dev |
| Excel / Google Sheets (gratuit) | Formules + pivot tables manuels | 30-60 min par analyse, zero intelligence |

**Le trou :** Personne ne combine datasets demo pre-charges + decouverte proactive d'insights + recommandations d'actions dans une UX faite pour les non-techniques.

---

## User

- **Primary :** Business user non-technique — marketing manager, e-com ops, SaaS founder — qui exporte des CSV chaque semaine et veut des reponses rapides.
- **Secondary :** PM ou analyste qui veut explorer des donnees vite sans ecrire de code.
- **Context :** Chaque lundi matin (reporting hebdo), chaque fin de mois (bilan), chaque fois qu'on exporte un CSV et qu'on se dit "il me faudrait un data analyst pour 5 minutes."

---

## Solution

| Pain | Feature |
|------|---------|
| 30-60 min Excel pour 1 question | Upload CSV + question en anglais/francais → chart + reponse en 10s |
| ChatGPT perd les fichiers | Datasets pre-charges pour demo instant (zero friction) |
| Outils BI trop complexes | UX minimale : 1 upload, 1 chat, resultats visuels |
| Pas d'insights proactifs | L'agent scanne le dataset et decouvre anomalies, correlations, outliers automatiquement |
| "Ok j'ai un chart, et maintenant ?" | Recommandations d'actions concretes (pas juste des chiffres, mais "voici quoi faire") |

---

## Riskiest Assumption

**"Un agent AI peut analyser N'IMPORTE QUEL CSV structure, generer des insights corrects avec des charts precis, en moins de 15 secondes par requete, avec moins de 5% d'erreur sur les calculs, sans que l'utilisateur ecrive du code ou configure quoi que ce soit."**

Les 3 contraintes critiques :
- **Latence :** ≤ 15s par requete (median)
- **Precision :** ≥ 95% de calculs corrects
- **Universalite :** Fonctionne sur 80%+ des CSV business standards

---

## Scope Scoring

| Feature | Pain | Risk | Effort | Score | In/Out |
|---------|------|------|--------|-------|--------|
| CSV upload + auto-detection colonnes | 3 | 2 | 1 | **4** | **IN** |
| Question naturelle → code pandas → execution | 3 | 3 | 2 | **4** | **IN** |
| Generation de charts (matplotlib) | 3 | 2 | 1 | **4** | **IN** |
| 3 datasets pre-charges (demo instant) | 2 | 3 | 1 | **4** | **IN** |
| Decouverte proactive d'insights | 3 | 3 | 2 | **4** | **IN** |
| Recommandations d'actions | 2 | 2 | 1 | **3** | **IN** |
| Panel code visible (transparence) | 1 | 1 | 1 | 1 | OUT |
| Persistence session (DB) | 2 | 1 | 2 | 1 | OUT |
| Export/partage de rapport | 1 | 1 | 2 | 0 | OUT |
| Multi-fichier avec JOIN | 1 | 1 | 3 | -1 | OUT |

### MVP (Score >= 3) — 6 features

1. **CSV upload + auto-detection** des types de colonnes (dates, numeriques, categories)
2. **Question naturelle → code pandas → execution** dans un sandbox
3. **Generation de charts** automatique (le bon type de chart pour la question)
4. **3 datasets pre-charges** : Superstore (e-commerce), SaaS Metrics, Marketing Spend
5. **Decouverte proactive d'insights** : l'agent scanne et trouve ce que tu n'as pas demande
6. **Recommandations d'actions** : pas juste des chiffres, mais "fais ceci"

### Out of Scope

- Panel code visible (nice-to-have, Scope 2 si le temps le permet)
- Persistence session (necessite une base de donnees, Phase 2)
- Export/partage de rapport
- Multi-fichier avec JOIN SQL

---

## Success Metrics

| Metric | Target | How to Test |
|--------|--------|-------------|
| Precision des calculs | >= 90% de reponses correctes sur 20 requetes golden dataset | Verification manuelle : sortie pandas vs reponse attendue |
| Correctness des charts | 100% des charts matchent les donnees affichees | Verification visuelle : les chiffres du chart correspondent au CSV source |
| Latence | < 15s par requete (mediane) | Mesurer sur 10 requetes x 3 datasets |
| Universalite | Fonctionne sur 4/5 formats CSV differents | Tester : Superstore, SaaS, Marketing, HR, Finance |
| Zero hallucination | 0 donnees inventees sur 20 requetes | Chaque chiffre dans la reponse doit tracer vers le CSV source |

---

## Key Architecture Decisions

| Decision | Choix | Rationale |
|----------|-------|-----------|
| LLM | GPT-4o-mini (OpenAI) | ADR-001 : GPT-5-mini rejete (latence 5-610s). GPT-4o-mini : 2-7s, meme precision, 3-10x moins cher. |
| Pattern agent | Prompt Chaining | Pattern le plus fiable selon Anthropic (HAUTE fiabilite). Plus previsible que ReAct pour la latence. |
| Execution code | Python subprocess sandbox | Execution locale, pas de dependance externe pour les calculs. Latence maitrisee (~1-2s). |
| Charts | Matplotlib/Seaborn → base64 PNG | Simple, pas de dependance frontend. Chart integre dans la reponse API. |
| Backend | FastAPI (Python) | Meme stack que tous les projets. Consistance. |
| Frontend | Lovable (React + Tailwind) | Meme stack que tous les projets. |
| Deploy | Render ($7/mo) | Meme stack que tous les projets. |

### Risque dependance externe

| Aspect | Evaluation |
|--------|-----------|
| Appels LLM par requete | 1 seul (ADR-002 : 2→1, code genere produit directement `result`) |
| Latence API typique | 2-5s par appel texte |
| Worst case API congestionnee | ~10-15s (rare, try/except avec message gracieux) |
| Coeur de la valeur | Execution code locale (pandas) — PAS l'API |
| Fallback si API lente | Le code s'execute quand meme, seul la generation est retardee |

**Conclusion :** La valeur principale (analyse + charts) est dans l'execution de code locale. L'API LLM sert a generer le code et resumer — pas a produire la valeur brute.

---

## Adversarial Test Cases

> Le Walking Skeleton DOIT inclure au moins 1 cas difficile.

| Cas | Pourquoi c'est dur | Attendu |
|-----|-------------------|---------|
| CSV avec encodage UTF-8 BOM + accents | Pandas peut planter sur l'encodage | Detection auto, pas d'erreur |
| CSV avec 40% de valeurs manquantes | Le code pandas doit gerer les NaN | Reponse honnete ("32% de donnees manquantes sur cette colonne") |
| Question ambigue ("montre-moi le trend") | Pas de colonne specifiee | L'agent demande une clarification OU choisit la colonne la plus logique |
| Dataset avec 50+ colonnes | Le LLM peut rater des colonnes importantes | L'agent explore d'abord, puis repond |
| CSV delimiteur point-virgule (EU format) | Pas un comma-separated standard | Auto-detection du delimiteur |

---

## Open Questions — RESOLUES

1. **Sandbox securite :** `exec()` avec `globals` restreints (seuls pd, np, plt, sns, df, CHART_PATH). Suffisant pour un side project — pas d'acces fichier ni reseau. Docker/microVM rejetes (complexite disproportionnee). → **Resolu WS.**

2. **Qualite visuelle des charts :** Seaborn + dark theme custom (#0A0A0A fond, palette indigo/vert/ambre). Resultat demo-ready. → **Resolu S1.**

3. **Datasets pre-charges :** Superstore (Kaggle, 9,994 lignes), SaaS Metrics (24 lignes, cree manuellement), Marketing Spend (764 lignes, cree manuellement). → **Resolu S1.**

---

## Market Landscape (resume)

80% du marche = outils BI classiques (Tableau, Power BI) pour les equipes data.
15% = chat-with-data generiques (Julius, ChatGPT).
5% = notebooks techniques (Hex, Observable) pour les developpeurs.

**0% = outil dedie non-technique avec datasets demo + insights proactifs + recommandations.**

C'est notre wedge.
