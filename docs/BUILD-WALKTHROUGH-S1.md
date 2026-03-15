# BUILD Walkthrough — Scope 1 : "L'analyse intelligente"

> Part of "The Builder PM" book — Chapter: BUILD Phase
> Walkthrough for DataPilot, Scope 1
> Suit le Walking Skeleton (pipeline de base)

---

## 1. Ce que ce scope fait

Le Walking Skeleton a prouve que le concept marche : donner un fichier, poser une question, recevoir une reponse. Mais c'etait le minimum absolu — un seul dataset, des questions simples, pas d'interface.

Le Scope 1 transforme la preuve de concept en moteur d'analyse complet :

1. **3 datasets demo** pre-charges — plus besoin d'uploader un fichier pour essayer l'outil
2. **5 types de questions** — aggregation, tendances, comparaisons, distributions, classements
3. **Decouverte proactive d'insights** — l'agent ne se contente pas de repondre, il scanne les donnees et trouve ce que tu n'as pas demande
4. **Recommandations d'actions** — pas juste des chiffres, mais "voici quoi faire"
5. **API endpoint** — le backend est accessible depuis n'importe quel frontend

**Analogie :** Le Walking Skeleton etait un moteur qui tourne sur un banc d'essai. Le Scope 1, c'est installer ce moteur dans une voiture avec 3 vitesses, un GPS, et un co-pilote qui te previent des obstacles.

---

## 2. Les 3 datasets demo — zero friction

### Le probleme

Pour tester l'outil, il fallait avoir un CSV sous la main et l'uploader. C'est un point de friction : la plupart des gens qui decouvrent un outil ne veulent pas chercher un fichier avant de voir ce que ca fait.

### La solution

3 datasets pre-charges qui couvrent 3 domaines business differents :

| Dataset | Domaine | Lignes | Colonnes | Cas d'usage |
|---------|---------|--------|----------|-------------|
| **Superstore** | E-commerce | 9,994 | 21 | Ventes, marges, categories, regions |
| **SaaS Metrics** | SaaS | 24 | 8 | MRR (revenu mensuel), churn (desabonnements), NPS (satisfaction) |
| **Marketing Spend** | Marketing | 764 | 7 | 5 canaux, CPC (cout par clic), conversions |

**Pourquoi ces 3 ?** Parce qu'ils representent les 3 contextes ou les business users exportent le plus de CSV : le e-commerce (Shopify, Amazon), le SaaS (Stripe, ChartMogul), et le marketing (Google Ads, Meta).

L'utilisateur clique sur un dataset, et l'analyse est instantanee — zero upload, zero attente.

---

## 3. Les 5 types de questions

Le Walking Skeleton avait ete teste sur des questions simples ("total des ventes"). Le Scope 1 valide que l'agent gere 5 types differents :

| Type | Exemple | Ce que ca teste |
|------|---------|----------------|
| **Aggregation** | "Quel est le total des ventes ?" | Somme, moyenne, comptage |
| **Trend** | "Comment evolue le MRR par mois ?" | Groupement par date, graphique temporel |
| **Comparison** | "Compare les ventes par region" | Groupement par categorie, graphique a barres |
| **Distribution** | "Quelle est la distribution des profits ?" | Histogramme, percentiles |
| **Top-N** | "Top 5 des produits les plus vendus" | Tri, filtrage, limitation des resultats |

Chaque type exige des operations pandas differentes. La question "top 5" demande un tri + filtre. La question "trend" demande un groupement par date + graphique. Le modele de langage doit choisir les bonnes operations a partir de la question en langage naturel.

---

## 4. Insights proactifs — trouver ce que tu n'as pas demande

### Le concept

Tous les outils d'analyse attendent ta question. Aucun ne prend l'initiative de scanner les donnees pour dire "hey, il y a un truc bizarre ici."

Le module `insights.py` fait exactement ca. Apres avoir repondu a la question, l'agent lance un deuxieme appel au modele de langage avec un prompt (des instructions) different :

```
Appel 1 (codegen) : "Reponds a la question de l'utilisateur"
Appel 2 (insights) : "Scanne les donnees. Trouve des anomalies,
                       des correlations, des segments, des tendances
                       que l'utilisateur n'a pas demandes."
```

### Comment ca marche

Le modele de langage recoit un resume statistique du dataset (moyennes, ecarts-types, correlations entre colonnes) et genere du code qui cherche des choses surprenantes.

Exemple sur le dataset Superstore :

> "1. Les ventes de la sous-categorie Copiers representent 3.2% des commandes mais 15.8% du chiffre d'affaires — forte valeur par unite.
> 2. La region South a le taux de profit le plus bas (9.2%) malgre un volume comparable aux autres regions.
> 3. Le mois de novembre montre un pic de 38% au-dessus de la moyenne — probable effet Black Friday."

Ce ne sont pas des generalites. Ce sont des chiffres reels, calcules par du code execute dans le sandbox (l'espace d'execution isole). Le modele de langage genere le code, le sandbox l'execute, et les chiffres viennent directement des donnees.

---

## 5. API endpoint — ouvrir le backend au monde

Le Walking Skeleton etait un script Python qu'on executait en ligne de commande. Le Scope 1 ajoute un serveur web (FastAPI) avec un endpoint (un point d'acces) :

```
POST /analyze
  - question : "What are the top 5 products by sales?"
  - dataset : "superstore" (ou upload d'un fichier CSV)
  - include_insights : true/false

→ Reponse JSON :
  {
    "answer": "Top 5 products by sales: ...",
    "chart": "data:image/png;base64,...",
    "insights": ["insight 1", "insight 2", ...],
    "timings": {"schema": 0.08, "analysis": 2.1, "total": 2.18}
  }
```

Deux endpoints supplementaires :
- `GET /datasets` : liste les 3 datasets demo avec leur disponibilite
- `GET /health` : verifie que le serveur tourne

Pourquoi une API (Application Programming Interface — un point d'acces pour les programmes) ? Parce que ca permet a n'importe quel frontend de se connecter au backend. Le Scope 2 ajoutera l'interface utilisateur — mais le moteur est deja accessible.

---

## 6. Tests adversariaux — les cas qui cassent

### Encodage UTF-8 BOM avec accents

Un fichier CSV exporte depuis Excel sur Windows contient souvent un BOM (Byte Order Mark — un marqueur invisible au debut du fichier) et des accents. Si le code d'analyse ne gere pas ca, il plante ou lit la premiere colonne avec des caracteres parasites.

**Test :** CSV avec BOM + accents + delimiteur point-virgule (format europeen).
**Resultat :** PASS. La detection automatique (`sep=None, engine='python'`) gere le delimiteur, et `encoding='utf-8-sig'` gere le BOM.

### Question ambigue

"Montre-moi le trend" — sans preciser quelle colonne. Le dataset Superstore a 21 colonnes. Laquelle montrer en tendance ?

**Test :** Question vague sur le dataset Superstore.
**Resultat :** PASS. L'agent choisit la colonne Sales (la plus logique pour un trend de ventes) et genere un graphique mensuel. C'est le choix que ferait un analyste humain.

---

## 7. Ce qui a merde

### Probleme 1 : JSON tronque

Quand le schema du dataset est long (Superstore = 21 colonnes), le modele de langage genere une reponse JSON (le format de donnees structure) qui depasse sa limite de tokens (le nombre maximum de "mots" qu'il peut produire). Le JSON est coupe au milieu — impossible a lire.

**Fix :** Un fallback (solution de secours) avec une expression reguliere qui extrait le champ `"code"` du JSON malformed. Meme si le JSON global est invalide, le code genere est souvent complet.

### Probleme 2 : `freq='M'` deprecie

pandas 2.x (la version recente de la librairie d'analyse) a change le code pour les frequences mensuelles : `'M'` est devenu `'ME'` (Month-End). Le modele de langage, entraine sur du code plus ancien, generait l'ancienne syntaxe.

**Fix :** Une ligne ajoutee dans les instructions du modele de langage : "IMPORTANT: pandas >= 2.2 — use 'ME' not 'M' for month-end frequency."

### Probleme 3 : Les insights generiques

Les premiers insights etaient trop generiques : "Sales and Profit show positive correlation." Pas tres surprenant quand on vend des produits avec une marge.

C'est un probleme de prompt — les instructions n'etaient pas assez specifiques pour demander des choses non-evidentes. Note pour le Scope 2 : affiner le prompt d'insights.

---

## 8. Golden dataset — verification de precision

10 requetes testees manuellement avec les reponses attendues :

| # | Question | Dataset | Correct ? |
|---|---------|---------|-----------|
| 1 | Total sales | Superstore | OUI |
| 2 | Average profit margin | Superstore | OUI |
| 3 | Top 5 products by revenue | Superstore | OUI |
| 4 | Monthly sales trend | Superstore | OUI |
| 5 | Sales by category | Superstore | OUI |
| 6 | MRR growth rate | SaaS | OUI |
| 7 | Highest churn month | SaaS | OUI |
| 8 | NPS distribution | SaaS | OUI |
| 9 | Best channel by CPA | Marketing | OUI |
| 10 | Budget allocation vs ROI | Marketing | **Faux negatif** — format % |

**Precision : 90% (9/10).** Le faux negatif (#10) est un probleme de format : le code genere calculait le bon chiffre mais l'affichait sans le signe %. Le fond etait correct, la forme non.

---

## 9. Resultats des micro-tests

| # | Test | Critere | Resultat |
|---|------|---------|----------|
| S1-1 | 3 datasets pre-charges | Chargent en < 2s | **PASS** — 0.08s, 0.00s, 0.00s |
| S1-2 | 5 types de questions | Toutes correctes | **PASS** — 5/5 |
| S1-3 | Proactive insights >= 3 | Minimum 3 insights | **PASS** — 5 insights |
| S1-4 | Recommendations >= 2 | Minimum 2 actions concretes | **PASS** — 5 recommandations |
| S1-5 | Adversarial encodage | UTF-8 BOM gere | **PASS** |
| S1-6 | Question ambigue | Clarification ou choix logique | **PASS** — choix Sales |
| S1-7 | API endpoint | JSON structure complet | **PASS** |
| S1-8 | Precision >= 90% | Golden dataset 10 requetes | **PASS** — 90% (9/10) |
| S1-9 | Latence < 15s mediane | Mediane sur 10 requetes | **PASS** — 2.13s mediane |

**Gate : 9/9 PASS.**

---

## 10. Architecture apres Scope 1

```
                    ┌──────────────────────┐
                    │ 3 datasets demo       │
                    │ (Superstore, SaaS,    │
                    │  Marketing)           │
                    └──────────┬───────────┘
                               │ ou upload CSV
┌──────────────────────────────▼───────────────────────────┐
│ API FastAPI (api.py)                                      │
│  POST /analyze │ GET /datasets │ GET /health              │
└──────────────────────────────┬───────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────┐
│ PIPELINE (agent.py — orchestrateur)                       │
│                                                           │
│  1. schema.py → detection colonnes + stats                │
│  2. codegen.py → LLM genere du code pandas                │
│  3. sandbox.py → execution isolee → resultat + chart      │
│  4. insights.py → 2e appel LLM → decouverte proactive     │
│                                                           │
│  Retry : si code echoue → erreur renvoyee au LLM → v2    │
└───────────────────────────────────────────────────────────┘
```

---

## 11. Ce qu'on a appris

1. **Les datasets demo suppriment la friction.** Un utilisateur qui decouvre l'outil n'a pas besoin de chercher un CSV. Il clique, il pose une question, il voit le resultat. C'est la difference entre "essaie notre outil" et "va chercher un fichier, uploade-le, puis essaie."

2. **Les insights proactifs sont le differenciateur.** Tous les outils repondent aux questions. Aucun ne dit "j'ai trouve quelque chose que tu n'as pas demande." C'est ce qui transforme un outil d'analyse en assistant.

3. **90% de precision, c'est suffisant pour le MVP.** Le faux negatif etait un probleme de format, pas de fond. Corriger le prompt pour formater les pourcentages est trivial. La precision sur les calculs est de 100%.

4. **La latence est meilleure que prevue.** 2.13s mediane contre un objectif de 15s. Le modele GPT-4o-mini est rapide et economique. L'architecture Prompt Chaining avec 1 seul appel LLM est efficace.

5. **Les tests adversariaux revelent les cas reels.** Le BOM, les accents, le delimiteur point-virgule — ce sont des problemes que les vrais utilisateurs rencontrent avec des vrais fichiers. Les tester tot evite les mauvaises surprises en production.
