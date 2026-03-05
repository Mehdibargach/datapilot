# BUILD Walkthrough — Scope 2 : "Le produit fini"

> Part of "The Builder PM" book — Chapter: BUILD Phase
> Walkthrough for DataPilot, Scope 2
> Follows Walking Skeleton + Scope 1 (backend complet)

---

## 1. Ce que ce scope fait

A la fin du Scope 1, on avait un backend solide : un agent qui lit un CSV (un fichier tableur), comprend la question en langage naturel, ecrit du code d'analyse, l'execute, et retourne une reponse avec un graphique.

Mais personne ne pouvait l'utiliser. Le backend etait une boite noire accessible uniquement via des commandes techniques. Pas d'interface, pas de deploiement, pas de demo possible.

Le Scope 2 transforme un moteur qui tourne en garage en une voiture qu'on peut conduire :

1. **Interface utilisateur** : un chat ou on pose des questions et on voit les reponses + graphiques inline.
2. **Selection de datasets** : 3 jeux de donnees demo cliquables (e-commerce, SaaS, marketing).
3. **Upload de fichiers** : drag & drop de n'importe quel CSV.
4. **Conversation multi-tour** : l'agent se souvient des questions precedentes.
5. **Deploy** : accessible via une URL publique, demo-ready.

---

## 2. Ce qui a rendu ce scope difficile

Sur le papier, "ajouter un frontend et deployer" semble simple. En realite, c'est le scope ou le plus de bugs ont ete trouves — parce que connecter un vrai utilisateur a un backend revele tous les angles morts.

Trois categories de problemes :

- **Robustesse** : des fichiers CSV avec des encodages exotiques crashaient le backend. Des erreurs de l'API OpenAI (le service qui fait tourner le modele de langage) n'etaient pas gerees — l'utilisateur voyait "Something went wrong" sans explication.
- **Hallucination** : le modele de langage copiait des exemples du prompt (les instructions qu'on lui donne) au lieu de calculer les vrais chiffres. Quand on lui demandait "explique ta methode", il recalculait au lieu d'expliquer.
- **Regression** : corriger un bug en cassait un autre. Modifier les instructions du modele de langage a un endroit changeait son comportement ailleurs de maniere imprevisible.

---

## 3. Architecture avant et apres

### Avant Scope 2 (fin du Scope 1)

```
CSV → Detection schema → LLM genere du code → Execution sandbox → Reponse + Chart
                                                                        ↓
                                                                  API JSON brut
                                                              (pas d'interface)
```

### Apres Scope 2

```
┌─────────────────────────────────────────────────────────────────────┐
│ FRONTEND (Lovable — React + Tailwind)                               │
│  Upload CSV │ Selecteur 3 datasets │ Chat │ Charts inline │ Mobile  │
└──────────────────────┬──────────────────────────────────────────────┘
                       │ POST /analyze (question + historique JSON)
┌──────────────────────▼──────────────────────────────────────────────┐
│ BACKEND (FastAPI sur Render)                                        │
│                                                                     │
│  1. schema.py : detection colonnes (4 encodages testes)       [MAJ] │
│  2. codegen.py : LLM genere du code pandas                         │
│     └─ META_KEYWORDS : detection meta-questions (regex)       [NEW] │
│     └─ META_SYSTEM : prompt dedie methodologie                [NEW] │
│     └─ Historique 5 derniers echanges                         [NEW] │
│  3. sandbox.py : execution dans un espace isole                     │
│     └─ _clean_code() : supprime imports + backticks           [NEW] │
│  4. insights.py : decouverte proactive (dark theme)           [MAJ] │
│  5. agent.py : orchestrateur avec bypass meta-questions       [MAJ] │
│  6. api.py : try/except global, historique, multi-encodage    [MAJ] │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 4. Conversation multi-tour — la memoire de l'agent

### Le probleme

Au Scope 1, chaque question etait independante. Si un utilisateur demandait "Quel est le MRR ?" (Monthly Recurring Revenue — le revenu mensuel recurrent) puis "Predit le trimestre suivant", l'agent ne savait pas de quoi on parlait. Il n'avait aucune memoire.

**Analogie :** C'est comme parler a quelqu'un qui oublie tout apres chaque phrase. On ne peut pas avoir une conversation — juste une serie de questions isolees.

### La solution

Les 5 derniers echanges (question + reponse + code utilise) sont envoyes au modele de langage avec chaque nouvelle question. Le frontend stocke l'historique et l'envoie en JSON (un format de donnees structure) via le formulaire.

```
Echange 1 : "Quel est le MRR par mois ?"
  → Reponse : "Jan: $45K, Feb: $52K, Mar: $58K..."

Echange 2 : "Predit le trimestre prochain"
  → Le LLM voit l'echange 1 ET la question 2
  → Il sait que "trimestre prochain" = la suite du MRR qu'il vient de calculer
  → Reponse : "Q2 prediction: Apr: $65K, May: $71K, Jun: $78K"
```

### Ce que ca a change dans le code

Trois fichiers modifies :

| Fichier | Changement |
|---------|-----------|
| `api.py` | Nouveau parametre `history` (JSON string) dans le formulaire |
| `agent.py` | Le parametre `history` passe a travers toute la chaine : `analyze()` → `_run_with_retry()` → `generate_code()` |
| `codegen.py` | Les 5 derniers echanges injectes dans les messages envoyes au LLM |

---

## 5. Detection de meta-questions — quand prompt et Python divergent

### Le probleme

Quand un utilisateur demande "Comment tu as calcule ca ?", l'agent devrait expliquer sa methode — pas recalculer. Mais le modele de langage ignorait cette instruction 1 fois sur 3.

Premier reflexe : modifier les instructions du modele de langage (le "prompt"). Ajouter un paragraphe en haut : "Si la question porte sur la methode, explique au lieu de coder."

**Resultat :** Catastrophe. Le modele de langage est devenu confus et a arrete de produire des reponses sur TOUTES les questions — pas seulement les meta-questions. Modifier le prompt a un endroit a change le comportement global de maniere imprevisible.

### La lecon : prompt-patching aveugle

C'est ce qu'on appelle le "prompt-patching aveugle" — modifier les instructions du modele de langage sans tester localement, pousser le changement, decouvrir la regression, re-modifier, re-pousser... une spirale.

**Analogie :** C'est comme regler le carburateur d'une voiture en tournant les vis au hasard. Chaque ajustement change le comportement global de maniere non lineaire. On finit par avoir un moteur qui ne demarre plus.

### La vraie solution : Python deterministe

Au lieu de demander au modele de langage de detecter les meta-questions (probabiliste — ca marche "la plupart du temps"), on utilise une expression reguliere en Python (deterministe — ca marche ou ca ne marche pas, sans ambiguite).

```python
META_KEYWORDS = re.compile(
    r"\b(how did you|what method|what formula|how confident|"
    r"explain.*(approach|method|calculation)|"
    r"give me.*(formula|method|approach|explanation)|"
    r"what approach|what technique|why did you|"
    r"(the|your) (method|formula|approach|logic))\b",
    re.IGNORECASE,
)
```

Ce code verifie si la question contient des mots-cles comme "how did you", "what formula", "give me the method". C'est binaire : oui ou non. Pas de zone grise.

Si c'est une meta-question, un prompt specialise explique la methodologie sans re-executer de code. La reponse est retournee directement avec un drapeau `_is_meta` qui dit a l'orchestrateur : "pas besoin de passer par le sandbox (l'espace d'execution isole), la reponse est deja prete."

### Pourquoi pas juste le prompt ?

| Approche | Fiabilite | Risque |
|----------|-----------|--------|
| Instructions dans le prompt | ~70% | Regressions sur les autres questions |
| Regex Python + prompt dedie | ~100% | Zero impact sur les autres questions |

**Principe Builder PM :** Quand une decision est critique (binaire : oui/non), utiliser du code deterministe. Quand une decision est floue (nuancee), utiliser le modele de langage.

---

## 6. Hallucination des insights — le LLM qui copie l'exemple

### Le probleme

Le module d'insights (decouverte proactive de tendances et anomalies) retournait des textes comme :

> "insight 1 with numbers + action"

C'est exactement le texte d'exemple dans les instructions du modele de langage. Au lieu de calculer les vrais chiffres, le LLM a copie le format d'exemple.

**Analogie :** C'est comme un etudiant qui repond a un examen en recopiant l'enonce de la question au lieu de la resoudre.

### La solution

Deux changements :

1. **Supprimer l'exemple du format JSON.** Si le modele de langage voit un exemple comme `"insights": ["insight 1 with numbers"]`, il le copie. En supprimant ce champ du format de retour, il ne peut plus le copier.

2. **Forcer le calcul via code execute.** Au lieu de demander au modele de langage de generer des insights sous forme de texte, on lui demande de generer du code qui calcule les vrais chiffres. Ce code est execute dans le sandbox, et les resultats sont des nombres reels extraits des donnees.

```
AVANT : LLM → texte "insight 1 with numbers" → copie
APRES : LLM → code pandas → sandbox execute → "Le MRR a augmente de 28% en 6 mois"
```

**Principe :** Code execute > texte genere. Les chiffres calcules par du code ne peuvent pas etre hallucines.

---

## 7. Robustesse — ce qui casse quand de vrais utilisateurs arrivent

### Crash silencieux sur upload

Le backend avait un `try/finally` mais pas de `except`. Quand une erreur se produisait pendant l'analyse, le serveur retournait une erreur HTTP 500 (erreur interne du serveur) sans message — l'utilisateur voyait juste "Something went wrong."

**Fix :** Un `except` global qui capture toute erreur et retourne un message JSON (un format de donnees structure) lisible : `{"success": false, "error": "Analysis failed: ..."}`

### Encodage CSV

Les fichiers CSV viennent dans differents encodages (la maniere dont les caracteres sont stockes). Un fichier DistroKid en format latin-1 crashait parce que le backend essayait seulement le format UTF-8.

**Fix :** 4 encodages testes sequentiellement : utf-8-sig → utf-8 → latin-1 → cp1252. Si aucun ne marche, message d'erreur explicite.

### Imports dans le code genere

Le modele de langage ajoute parfois des lignes `import pandas` dans le code genere, malgre les instructions qui disent "pas d'imports". Le sandbox n'a pas ces modules disponibles → crash.

**Fix :** `_clean_code()` — une fonction qui supprime automatiquement les lignes `import` et les backticks (marqueurs de code) avant execution.

### Erreurs API OpenAI intermittentes

L'API OpenAI retourne parfois des erreurs 500 (erreur serveur) de maniere aleatoire. Sans protection, ces erreurs remontaient jusqu'a l'utilisateur.

**Fix :** `try/except` sur chaque appel a l'API, avec un message d'erreur gracieux : "LLM service error: ..." au lieu d'un crash.

---

## 8. L'anti-pattern qui a coute du temps

### Le prompt-patching aveugle

Au milieu du Scope 2, le PM a signale un enlisement : chaque correction de bug en creait un nouveau. La boucle etait :

```
Modifier le prompt → Push sans tester → Bug → Re-modifier → Push → Nouveau bug → ...
```

**Ce qui a change apres l'audit :**

1. **Tester localement AVANT de pousser.** Lancer le serveur en local, tester 5 scenarios, valider, puis pousser un seul commit propre.
2. **Logique critique en Python, pas en prompt.** La detection de meta-questions, le nettoyage du code, la gestion des erreurs — tout ca est du code deterministe, pas des instructions au modele de langage.
3. **Un commit propre apres validation.** Au lieu de 5 commits "fix: try this" → "fix: revert" → "fix: try something else", un seul commit "fix: audit pass — error handling, meta-questions, insights, sandbox" apres tests locaux.

**Materiel livre :** Cet anti-pattern est directement applicable au chapitre evaluation. Quand le comportement du modele de langage est non-deterministe (il ne fait pas toujours la meme chose avec les memes instructions), les corrections par prompt sont dangereuses. La solution : isoler la logique critique dans du code Python testable.

---

## 9. Finding hors scope — le schema gap

Pendant les tests avec un CSV de donnees musicales (DistroKid), l'utilisateur a demande "combien de streams pour tel artiste ?". L'agent a repondu avec un chiffre de plus d'un million.

Le probleme : la colonne "Quantity" dans le CSV somme TOUS les stores (Facebook 99.9%, Spotify 0.004%, Apple Music, etc.). L'utilisateur dit "streams" en pensant Spotify, mais le CSV ne distingue pas. L'agent a fait un calcul correct sur des donnees dont la semantique (la signification) ne correspond pas a l'intention.

**Decision PM :** Log comme finding, pas comme bug a corriger dans ce scope. Les datasets demo controles ne sont pas touches. C'est du materiel pour le chapitre evaluation du livre — l'ecart entre l'intention de l'utilisateur et la semantique des donnees.

---

## 10. Resultats des micro-tests

| # | Test | Critere | Resultat |
|---|------|---------|----------|
| S2-1 | Upload CSV | Drag & drop → preview des 5 premieres lignes | **PASS** |
| S2-2 | Chat interface | Question → reponse + chart inline | **PASS** |
| S2-3 | Dataset selector | 3 datasets cliquables, chargement instantane | **PASS** |
| S2-4 | Mobile responsive | Utilisable sur 375px width | **PASS** |
| S2-5 | Deploy Render | Backend live, frontend connecte | **PASS** |
| S2-6 | Demo script 2min | Flow complet sans accroc | **PASS** |

**Gate : 6/6 PASS.**

---

## 11. Recapitulatif des changements

### Fichiers modifies

| Fichier | Changement | Impact |
|---------|-----------|--------|
| `schema.py` | 4 encodages CSV (utf-8-sig, utf-8, latin-1, cp1252) | Upload de fichiers non-UTF-8 |
| `codegen.py` | Regex meta-questions + prompt dedie + historique 5 tours + try/except API | Conversation multi-tour + meta-questions + robustesse |
| `sandbox.py` | `_clean_code()` (supprime imports/backticks) + safety net result=None | Plus de crash sur code genere avec imports |
| `insights.py` | Try/except API + dark theme charts + suppression placeholder | Insights avec vrais chiffres + charts coherents |
| `agent.py` | Historique propage + bypass meta `_is_meta` + `.get("code", "")` | Pipeline complet multi-tour |
| `api.py` | Parametre `history` + except global + import json | Plus de crash HTTP 500 silencieux |
| `requirements.txt` | Ajout numpy, pin pandas>=2.2.0 | Dependances completes |

### Frontend (Lovable — hors repo backend)
- Interface chat avec historique
- Selecteur 3 datasets demo
- Upload CSV drag & drop
- Charts inline dans la conversation
- Responsive mobile

---

## 12. Ce qu'on a appris

1. **Code deterministe > instructions probabilistes.** Quand une decision est binaire (est-ce une meta-question ?), une expression reguliere en Python est fiable a 100%. Le modele de langage est fiable a ~70% sur ce type de detection.

2. **Code execute > texte genere pour les chiffres.** Les insights calcules par du code pandas dans le sandbox ne peuvent pas etre hallucines. Les insights generes par texte peuvent copier les exemples du prompt.

3. **Tester localement avant de pousser.** L'anti-pattern "prompt-patching aveugle" a coute 2h de spirale bug→fix→regression. La solution : serveur local, 5 tests, un seul commit propre.

4. **Les vrais bugs apparaissent avec les vrais utilisateurs.** L'encodage latin-1, les erreurs API intermittentes, le crash HTTP 500 sans message — rien de tout ca n'existait dans les tests avec les datasets demo. C'est le contact avec des fichiers reels qui les a reveles.

5. **L'intention de l'utilisateur ≠ la semantique des donnees.** "Streams" pour l'utilisateur = Spotify. "Quantity" dans le CSV = toutes les plateformes confondues. Ce gap n'est pas un bug du code — c'est un probleme de comprehension contextuelle que meme un humain pourrait rater sans connaitre le dataset.
