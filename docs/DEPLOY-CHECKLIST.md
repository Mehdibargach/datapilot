# Deploy Checklist — DataPilot

> Template from The Builder PM Method — SHIP phase
> Go through every item before announcing "it's live".

**Project Name:** DataPilot
**Deploy Date:** 2026-03-05

---

## Infrastructure

- [x] Application deployed (API endpoint: `https://datapilot-backend.onrender.com`)
- [ ] **BLOCKER: Service Render suspendu** — réactiver depuis le dashboard Render
- [x] Web interface deployed (URL: `https://the-data-pilot.lovable.app`)
- [x] Environment variables set (OPENAI_API_KEY en production)
- [x] CORS configured (allow_origins=["*"])

## Pre-Deploy Gate

- [x] Eval Gate passed — CONDITIONAL GO (87.5%, 0 hallucination, 0 BLOCKING fail)

## Quality

- [x] Basic error handling / edge cases covered (try/except global, retry LLM, clean_code)
- [ ] Tested on mobile (frontend Lovable — à vérifier après reconnexion)
- [ ] Tested on Chrome, Safari, Firefox (frontend Lovable — à vérifier après reconnexion)
- [x] No API keys or secrets exposed in client code (.env, pas de clé dans le frontend)

## Documentation

- [ ] README updated with demo link + screenshots
- [x] Build Log entry for SHIP phase completed
- [x] Architecture doc reflects final state (1-Pager, ADRs à jour)

## Post-Deploy

- [ ] Demo URL works end-to-end (full user flow) — après réactivation Render
- [ ] Shared with 2-3 test users for feedback
- [x] Project Dossier started

---

## Actions PM requises

1. **Réactiver le service Render** (`datapilot-backend.onrender.com`) — le push GitHub est fait, le deploy se fera automatiquement
2. **Vérifier le frontend Lovable** — s'assurer qu'il pointe vers le bon backend URL
3. **Tester le flow complet** — upload CSV / select dataset → question → answer + chart
