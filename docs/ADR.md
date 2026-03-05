# Architecture Decision Records — DataPilot

> Template from The Builder PM Method
> Chaque ADR documente une decision technique prise pendant le BUILD.

---

## ADR-001 : GPT-4o-mini au lieu de GPT-5-mini

**Date :** 2026-03-04 (Walking Skeleton)
**Statut :** Accepte
**Contexte :** Le 1-Pager prevoyait GPT-5-mini (OpenAI) pour la generation de code.

### Decision

Utiliser GPT-4o-mini a la place de GPT-5-mini.

### Raisons

| Critere | GPT-5-mini | GPT-4o-mini |
|---------|-----------|-------------|
| Latence | 5-610s (imprevisible) | 2-7s (stable) |
| Precision | 100% (4/4) | 100% (4/4) |
| Cout tokens | Plus cher | 3-10x moins cher |
| Thinking tokens | Oui (consomment le budget) | Non |

GPT-5-mini est un modele "raisonnant" avec des thinking tokens invisibles. Avec une limite de 500 tokens de sortie, le modele consomme tout le budget en reflexion et retourne une reponse vide (`finish_reason: length`). Augmenter a 2000 tokens resout le probleme, mais la latence reste imprevisible (5s a 610s selon la congestion).

GPT-4o-mini produit les memes resultats en 10x moins de temps, sans thinking tokens.

### Consequences

- Latence mediane : 3.04s (WS), 2.13s (S1) — largement sous l'objectif de 15s
- Cout estime : ~$0.001-0.005/requete (contre ~$0.01-0.03 pour GPT-5-mini)
- Limite : GPT-4o-mini est moins performant sur les questions tres complexes (multi-etapes, raisonnement long). Acceptable pour du code pandas.

---

## ADR-002 : 1 appel LLM au lieu de 2

**Date :** 2026-03-04 (Walking Skeleton)
**Statut :** Accepte
**Contexte :** Le design initial prevoyait 2 appels : (1) generation de code, (2) resume du resultat en langage naturel.

### Decision

Un seul appel. Le code genere produit directement une reponse formatee via `result = f"..."`.

### Raisons

Le deuxieme appel ajoutait ~2-3s de latence sans apporter de valeur mesurable. En modifiant les instructions du modele de langage pour que le code genere inclue une variable `result` avec la reponse formatee, on obtient le meme resultat en 1 appel.

**Avant :**
```
Appel 1 : schema + question → code pandas → execution → DataFrame brut
Appel 2 : DataFrame brut + question → resume en langage naturel
Total : 2 appels, ~5-6s
```

**Apres :**
```
Appel 1 : schema + question → code pandas (avec result = f"...") → execution → reponse prete
Total : 1 appel, ~2-3s
```

### Consequences

- Latence divisee par 2
- Cout API divise par 2
- Le code genere est parfois moins lisible (le `result` contient du formatage), mais l'utilisateur ne voit pas le code

---

## ADR-003 : Regex Python pour la detection de meta-questions

**Date :** 2026-03-05 (Scope 2)
**Statut :** Accepte
**Contexte :** Quand l'utilisateur demande "comment tu as calcule ca ?", l'agent doit expliquer sa methode au lieu de recalculer. La premiere approche etait de modifier les instructions du modele de langage.

### Decision

Utiliser une expression reguliere Python (`META_KEYWORDS`) pour detecter les meta-questions de maniere deterministe, avec un prompt dedie pour l'explication de methodologie.

### Raisons

| Approche | Fiabilite | Risque |
|----------|-----------|--------|
| Instructions dans le prompt principal | ~70% | Le modele de langage ignore l'instruction 1 fois sur 3. Pire : modifier le prompt cause des regressions sur les AUTRES questions (prompt-patching aveugle). |
| Regex Python + prompt dedie | ~100% | Detection binaire. Zero impact sur le prompt principal. Prompt dedie optimise pour l'explication. |

La tentative de detection par prompt a cause une regression critique : le modele de langage a arrete de produire des reponses sur TOUTES les questions (result=None), pas seulement les meta-questions. Le prompt principal est un equilibre fragile — y ajouter de la logique conditionnelle le destabilise.

### Implementation

```python
META_KEYWORDS = re.compile(
    r"\b(how did you|what method|what formula|how confident|...)\b",
    re.IGNORECASE,
)
```

Si la regex matche :
1. Pas d'appel au prompt principal
2. Appel au prompt `META_SYSTEM` avec le contexte de la question precedente
3. Retour direct (flag `_is_meta`), pas de passage par le sandbox

### Consequences

- Les meta-questions fonctionnent a 100% (12/12 patterns testes)
- Le prompt principal reste inchange et stable
- Limite : la regex ne couvre pas les formulations tres indirectes ("je ne comprends pas le resultat"). Acceptable — ces cas seront traites comme des questions normales.

### Principe general

**Quand une decision est binaire (oui/non), utiliser du code deterministe. Quand une decision est nuancee, utiliser le modele de langage.** La detection de meta-questions est binaire. La generation de code est nuancee. Chacune utilise l'outil adapte.
