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

---

## ADR-004 : GPT-4o au lieu de GPT-4o-mini (EVALUATE micro-loop)

**Date :** 2026-03-05 (EVALUATE)
**Statut :** Accepte — remplace ADR-001 pour le modele de production
**Contexte :** L'eval Round 1 avec GPT-4o-mini a score 55% avec 1 hallucination BLOCKING. L'hypothese : ~50% des echecs sont lies a la capacite du modele (multi-step, adversarial).

### Decision

Passer de GPT-4o-mini a GPT-4o pour la generation de code. Ajouter une regle anti-hallucination dans le prompt.

### Donnees de l'eval A/B

| Metrique | GPT-4o-mini (R1) | GPT-4o (R2) | Delta |
|----------|-------------------|-------------|-------|
| Score global | 55% | 90% | **+35pp** |
| Hallucinations | 1 (BLOCKING) | 0 | **Fix** |
| Code errors | 3 | 0 | **Fix** |
| Aggregation | 100% (4/4) | 100% (4/4) | = |
| Multi-step | 40% (2/5) | 100% (5/5) | **+60pp** |
| Adversarial | 17% (0.5/3) | 83% (2.5/3) | **+66pp** |
| Latence mediane | 3.5s | 2.1s | **-40%** |

### Raisons

1. **Multi-step** : GPT-4o-mini echoue sur les chaines d'operations complexes (groupby + sort + head + format). GPT-4o les resout systematiquement.
2. **Adversarial** : GPT-4o-mini hallucine (utilise "profit" comme proxy pour "satisfaction"). GPT-4o refuse correctement grace a la regle anti-hallucination.
3. **Latence** : GPT-4o est paradoxalement plus rapide (2.1s vs 3.5s) — probablement car il genere du code plus propre en moins de tokens.

### Trade-offs

| Critere | GPT-4o-mini | GPT-4o |
|---------|-------------|--------|
| Cout/requete | ~$0.001-0.005 | ~$0.01-0.05 |
| Precision globale | 55% | 90% |
| Hallucination | 1/20 (5%) | 0/20 (0%) |
| Latence | 3.5s median | 2.1s median |

Le cout est ~10x plus eleve, mais pour un projet portfolio/demo, la qualite prime. A l'echelle, on pourrait utiliser GPT-4o-mini pour les questions simples (aggregation) et GPT-4o pour les questions complexes (routing par difficulte).

### Consequences

- Modele de production : gpt-4o (pas gpt-4o-mini)
- Prompt enrichi : regle anti-hallucination, regle refus dates, format renforce
- ADR-001 reste valide comme historique (le rejet de GPT-5-mini est toujours pertinent)
