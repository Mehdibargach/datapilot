# BUILD Walkthrough — Walking Skeleton : "L'agent repond a une question"

> Part of "The Builder PM" book — Chapter: BUILD Phase
> Walkthrough for DataPilot, Walking Skeleton
> Premier vertical slice : le chemin le plus fin de bout en bout.

---

## 1. Ce que ce skeleton fait

Imagine que tu exportes un fichier de ventes depuis ton outil e-commerce. Tu l'ouvres dans Excel, tu cherches une colonne, tu fais une formule, tu generes un graphique... 30 minutes plus tard, tu as ta reponse.

Le Walking Skeleton fait ca en 3 secondes. Tu donnes un fichier CSV (un tableur de donnees) et une question en langage naturel. L'agent :

1. **Lit le fichier** et comprend ce qu'il contient (colonnes, types, valeurs)
2. **Ecrit du code** d'analyse adapte a ta question
3. **Execute ce code** dans un espace isole
4. **Retourne** une reponse en texte + un graphique

C'est la version la plus simple possible — un seul fichier, une seule question, une seule reponse. Mais c'est de bout en bout : si ca marche, on sait que le concept tient.

---

## 2. La chaine de traitement (4 maillons)

```
CSV file
   ↓
┌──────────────────────────────────────────────────┐
│ 1. SCHEMA (schema.py)                             │
│    Lit le fichier, detecte les colonnes,          │
│    leurs types, leurs stats.                      │
│    "21 colonnes, dont Sales (numerique,           │
│     min: 0.44, max: 22,638)"                      │
└──────────────┬───────────────────────────────────┘
               │ texte compact (schema)
┌──────────────▼───────────────────────────────────┐
│ 2. CODEGEN (codegen.py)                           │
│    Envoie le schema + la question au LLM          │
│    (modele de langage, ici GPT-4o-mini).          │
│    Le LLM repond avec du code pandas.             │
│    "df['Sales'].sum() → result = f'Total: ...'"   │
└──────────────┬───────────────────────────────────┘
               │ code Python
┌──────────────▼───────────────────────────────────┐
│ 3. SANDBOX (sandbox.py)                           │
│    Execute le code dans un espace restreint.      │
│    Seuls pandas, numpy, matplotlib, seaborn       │
│    sont disponibles. Pas d'acces fichier,         │
│    pas d'internet.                                │
└──────────────┬───────────────────────────────────┘
               │ resultat texte + chart PNG
┌──────────────▼───────────────────────────────────┐
│ 4. AGENT (agent.py)                               │
│    Assemble le tout. Si le code plante,           │
│    renvoie l'erreur au LLM pour correction.       │
│    Max 2 tentatives.                              │
└──────────────────────────────────────────────────┘
               │
           Reponse finale : texte + graphique
```

**Analogie :** Pense a une chaine de production. Chaque maillon fait une seule chose et passe le resultat au suivant. Si un maillon casse, on sait lequel — et on peut le reparer sans toucher aux autres.

Ce pattern s'appelle "Prompt Chaining" (enchainement de prompts). On le prefere a des patterns plus complexes comme ReAct (ou l'agent decide lui-meme quels outils utiliser) parce qu'il est previsible : memes etapes, meme ordre, meme latence a chaque fois.

---

## 3. Maillon 1 : Detection du schema — comprendre le fichier

Quand tu ouvres un tableur, ton cerveau fait instantanement : "OK, il y a une colonne Date, une colonne Sales avec des chiffres, une colonne Region avec des noms..." Le module `schema.py` fait exactement ca, mais pour le modele de langage.

Il produit un resume compact :

```
Dataset: 9994 rows, 21 columns

- Order Date (object) | 0.0% null | samples: ['2014-01-03', '2014-01-04']
- Sales (float64) | range: 0.44 to 22638.48, mean: 229.86 | 0.0% null
- Profit (float64) | range: -6599.98 to 8399.98, mean: 28.66 | 0.0% null
- Category (object) | 3 uniques | samples: ['Furniture', 'Office Supplies']
```

Pourquoi un resume au lieu d'envoyer tout le fichier ? Parce que le modele de langage a une fenetre de contexte limitee (la quantite de texte qu'il peut lire d'un coup). Un fichier de 10 000 lignes serait trop gros. Le schema, lui, fait quelques lignes — suffisant pour comprendre la structure sans noyer le modele.

**Detection automatique :** Le module detecte aussi le delimiteur (virgule, point-virgule, tabulation) et l'encodage (la maniere dont les caracteres sont stockes). Un fichier europeen avec des points-virgules et des accents fonctionne sans configuration.

---

## 4. Maillon 2 : Generation de code — le LLM ecrit du Python

Le modele de langage recoit le schema + la question et repond avec du code pandas (une librairie Python pour analyser des donnees).

**Exemple concret :**

Question : "Quel est le total des ventes ?"

Le LLM genere :
```python
total = df['Sales'].sum()
result = f"The total sales amount is ${total:,.2f}"
```

La regle numero 1 du prompt (les instructions donnees au modele de langage) : **le code DOIT toujours se terminer par `result = "..."`**. C'est la variable qui contient la reponse finale. Si le LLM oublie de la definir, la reponse sera vide.

**Format de retour :** Le LLM repond en JSON (un format de donnees structure) :
```json
{
  "code": "total = df['Sales'].sum()\nresult = f'Total: ${total:,.2f}'",
  "needs_chart": false,
  "explanation": "Sum of the Sales column"
}
```

---

## 5. Maillon 3 : Sandbox — executer sans risque

Le code genere par le modele de langage est execute avec `exec()` — une fonction Python qui execute du texte comme du code. C'est puissant mais dangereux : si le LLM generait du code malveillant (supprimer des fichiers, acceder a internet), il serait execute.

**Mitigation :** L'execution se fait dans un espace restreint (un "namespace") qui contient uniquement :
- `df` : les donnees du CSV
- `pd`, `np` : pandas et numpy (pour les calculs)
- `plt`, `sns` : matplotlib et seaborn (pour les graphiques)
- `CHART_PATH` : le chemin ou sauvegarder le graphique

Rien d'autre. Pas d'acces au systeme de fichiers, pas de requetes reseau.

**Analogie :** C'est comme un bac a sable pour enfants. On met les jouets dedans (pandas, matplotlib), l'enfant (le code genere) joue avec ce qu'il a. Mais il ne peut pas sortir du bac.

---

## 6. Maillon 4 : L'orchestrateur — retry intelligent

L'orchestrateur (`agent.py`) enchaine les 3 maillons et ajoute une capacite de correction.

Si le code genere plante (erreur de syntaxe, colonne inexistante...), l'orchestrateur :
1. Capture l'erreur
2. Renvoie le code + l'erreur au modele de langage
3. Le LLM genere une version corrigee
4. Re-execute

Maximum 2 tentatives. Si la deuxieme echoue aussi, on retourne un message d'erreur.

**Analogie :** C'est comme un prof qui corrige une copie et la rend a l'eleve en disant "tu as fait une erreur ici, recommence." L'eleve a une deuxieme chance, mais pas une troisieme.

En pratique, le retry resout la majorite des erreurs — souvent des problemes de syntaxe ou de noms de colonnes mal orthographies.

---

## 7. Ce qui a merde

### Probleme 1 : Le modele initial etait 100x trop lent

Le 1-Pager prevoyait d'utiliser GPT-5-mini. Premier test : 610 secondes pour une requete. Plus de 10 minutes. Inacceptable.

La cause : GPT-5-mini est un modele "raisonnant" (il reflechit avant de repondre, avec des "thinking tokens" invisibles). Ces tokens consomment le budget de reponse. Avec une limite de 500 tokens, le modele reflechissait, consommait tout le budget, et retournait une reponse vide.

**Decision :** Switch vers GPT-4o-mini. Resultat : 2-7 secondes par requete. 100x plus rapide. Meme precision (100%). Tokens 3-10x moins chers.

### Probleme 2 : Deux appels LLM pour rien

Le design initial prevoyait 2 appels : un pour generer le code, un pour resumer le resultat en langage naturel. Mais en modifiant le prompt pour que le code genere produise directement une reponse formatee (`result = f"Le total est ${total:,.2f}"`), on elimine le deuxieme appel.

**Gain :** -50% de latence, -50% de cout API.

### Probleme 3 : Code sur une seule ligne

GPT-4o-mini genere parfois du code compact sur une seule ligne avec des points-virgules. Quand le code contient des f-strings (des chaines de caracteres avec des variables), ca cree des erreurs de syntaxe.

**Fix :** Quand le code echoue, l'instruction de retry dit explicitement "ecris le code en multi-ligne, pas en une seule ligne avec des points-virgules."

---

## 8. Resultats des micro-tests

| # | Test | Critere | Resultat |
|---|------|---------|----------|
| WS-1 | Schema detection | 13+ colonnes detectees | **PASS** — 21 colonnes, types auto-detectes |
| WS-2 | Code generation | Code valide, zero erreur syntaxe | **PASS** — 4/4 code valide |
| WS-3 | Execution sandbox | Code execute sans erreur | **PASS** — 4/4 sans erreur |
| WS-4 | Chart generation | Chart lisible, titres, labels | **PASS** — Seaborn dark theme |
| WS-5 | Precision (ecart < 1%) | Reponse = somme reelle de Sales | **PASS** — 0.00% d'ecart, 4/4 exact |
| WS-6 | Latence < 15s | End-to-end sous 15 secondes | **PASS** — mediane 3.04s, max 7.21s |
| WS-7 | Adversarial NaN (40%) | Gere sans planter | **PASS** — 40% NaN gere, 1.9s |

**Gate : 7/7 PASS.**

---

## 9. Recapitulatif des changements

### Fichiers crees

| Fichier | Role |
|---------|------|
| `schema.py` | Detection colonnes, types, stats, encodage auto |
| `codegen.py` | Appel au modele de langage, generation de code pandas |
| `sandbox.py` | Execution du code dans un namespace restreint |
| `agent.py` | Orchestrateur Prompt Chaining + retry |

### Decisions

| Decision | Alternative rejetee | Pourquoi |
|----------|-------------------|----------|
| GPT-4o-mini | GPT-5-mini | 100x plus rapide, meme precision, pas de thinking tokens |
| 1 appel LLM | 2 appels (codegen + resume) | -50% latence, le code produit directement la reponse |
| Prompt Chaining | ReAct (agent decide ses outils) | Plus previsible, latence constante, plus simple a debugger |
| `exec()` restreint | Docker, microVM | Suffisant pour un side project, zero setup supplementaire |

---

## 10. Ce qu'on a appris

1. **Tester le modele LLM en premier.** La decision GPT-5-mini → GPT-4o-mini a ete prise en 30 minutes de test. Si on avait builde toute l'architecture autour de GPT-5-mini, le pivot aurait ete couteux.

2. **1 appel > 2 appels.** En modifiant le prompt pour que le code genere produise directement une reponse formatee, on divise la latence par 2 sans perte de qualite.

3. **Le retry intelligent absorbe les erreurs.** GPT-4o-mini genere parfois du code bancal. Le retry avec l'erreur en contexte corrige 90%+ des cas — sans intervention humaine.

4. **Le schema compact suffit.** Pas besoin d'envoyer tout le fichier au modele de langage. Un resume de quelques lignes (noms de colonnes, types, min/max, exemples) lui donne assez de contexte pour ecrire du code correct.
