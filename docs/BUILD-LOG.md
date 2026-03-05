# BUILD LOG — DataPilot

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

## Scope 2 — "Le produit fini"

**Date :** 2026-03-04 / 2026-03-05
**Duree :** ~4h (backend hardening + frontend Lovable + deploy + debug multi-turn)

### Ce qui a ete fait

**Backend — robustesse et nouvelles features :**
- **Historique de conversation** (codegen.py, agent.py, api.py) : les 5 derniers echanges sont passes au LLM pour contexte multi-turn. Le frontend envoie l'historique en JSON via FormData.
- **Detection de meta-questions** (codegen.py) : regex Python deterministe detecte les questions sur la methode ("how did you calculate?", "give me the formula"). Prompt dedie qui explique la methodologie sans re-executer de code.
- **Fix hallucination insights** (insights.py) : le LLM copiait les exemples du prompt ("insight 1 with numbers"). Fix : forcer la generation de code qui calcule les vrais chiffres, supprimer les exemples du format JSON.
- **Nettoyage sandbox** (sandbox.py) : suppression des lignes `import` et des backticks dans le code genere par le LLM avant execution.
- **Gestion erreurs globale** (api.py) : try/except autour de tout l'appel d'analyse — plus de crash HTTP 500 silencieux.
- **Multi-encodage CSV** (schema.py) : 4 encodages testes (utf-8-sig, utf-8, latin-1, cp1252) pour les fichiers uploades.
- **Gestion erreurs OpenAI** (codegen.py, insights.py) : try/except sur tous les appels API, messages d'erreur gracieux.
- **Dark theme insights charts** (insights.py) : memes regles que le chart principal.
- **requirements.txt** : ajout numpy, pin pandas>=2.2.0.

**Frontend — Lovable (React + Tailwind) :**
- Interface chat : question → reponse + chart inline dans la conversation
- Selecteur de datasets : 3 datasets demo cliquables
- Upload CSV : drag & drop avec preview
- Responsive mobile (375px)
- Historique de conversation : envoi JSON au backend

**Deploy :**
- Backend FastAPI sur Render ($7/mo)
- Frontend Lovable connecte au backend

### Resultats micro-tests
| # | Test | Resultat |
|---|------|----------|
| S2-1 | Upload CSV | **PASS** — drag & drop fonctionne, preview affiche |
| S2-2 | Chat interface | **PASS** — question → reponse + chart inline |
| S2-3 | Dataset selector | **PASS** — 3 datasets cliquables, chargement instantane |
| S2-4 | Mobile responsive | **PASS** — utilisable sur 375px |
| S2-5 | Deploy Render | **PASS** — backend live, frontend connecte |
| S2-6 | Demo script 2min | **PASS** — flow complet sans accroc |

### Bugs et fixes
1. **result=None regression** : restructurer le prompt a casse la generation de `result`. Fix : "#1 RULE" en haut du prompt system pour forcer `result = f"..."` sur chaque generation.
2. **Insights "placeholder"** : le LLM copiait l'exemple du format JSON ("insight 1 with numbers + action") au lieu de generer du vrai code. Fix : supprimer le champ `"insights"` du format JSON, forcer le calcul via code execute.
3. **Meta-question recalcule au lieu d'expliquer** : le LLM re-executait le code au lieu d'expliquer la methode. Fix : detection regex deterministe en Python (`META_KEYWORDS`) + prompt dedie `META_SYSTEM` + bypass sandbox.
4. **KeyError 'code' sur meta-reponses** : les meta-reponses n'ont pas de cle "code". Fix : `codegen_result.get("code", "")` partout (4 occurrences).
5. **Imports dans le code genere** : le LLM ajoute des `import` malgre le prompt. Fix : `_clean_code()` supprime les lignes import/from avant exec.
6. **OpenAI 500 intermittent** : erreurs aleatoires de l'API OpenAI. Fix : try/except sur tous les appels, messages d'erreur gracieux.
7. **"Something went wrong" sur upload** : api.py avait try/finally mais pas de except → crash HTTP 500 sans JSON. Fix : except global retournant un JSON d'erreur propre.
8. **Encodage CSV upload** : fichiers DistroKid en latin-1 crashaient. Fix : 4 encodages testes sequentiellement.
9. **Regex meta trop etroite** : "Can you give me the method?" ne matchait pas. Fix : ajout patterns "give me", "show me", "(the|your) (method|formula|approach|logic)". 12/12 patterns testes.

### Decisions techniques
- **Regex Python > prompt pour la detection** : la detection de meta-questions par prompt etait non-deterministe (GPT-4o-mini ignorait les instructions 1 fois sur 3). La regex Python est binaire et fiable.
- **Bypass sandbox pour meta-questions** : les reponses textuelles longues cassaient le `exec()` (guillemets, newlines). Solution : retourner la reponse directement avec un flag `_is_meta`, sans passer par le sandbox.
- **Code-computed > LLM-generated pour insights** : les insights generes par texte contenaient des placeholders. Le code execute dans le sandbox produit les vrais chiffres.
- **Anti-pattern identifie : prompt-patching aveugle** : modifier le prompt et push sans tester localement causait des regressions en chaine. Lesson : toujours tester localement, un seul commit propre apres validation.

### Finding hors scope
- **Schema gap donnees utilisateur** : sur un CSV DistroKid, "Quantity" somme tous les stores (Facebook 99.9%, Spotify 0.004%). L'utilisateur dit "streams" mais le CSV ne distingue pas. Ce n'est pas un bug DataPilot — c'est un probleme de semantique des donnees. Log pour le backlog V2 et materiel chapitre evaluation du livre.

---
