# Architecture — TechCorp Neural Console

## Vue d'ensemble

Trois couches, séparées par des contrats explicites :

1. **Frontend** (`web/`) — SPA React 19 / TypeScript, buildée par Vite. Parle
   uniquement au gateway via `/api/*`. Aucune logique modèle côté client.
2. **Gateway** (`gateway/`) — service Go, stdlib uniquement. Point d'entrée
   unique : streaming SSE, télémétrie, santé, sécurité, service des fichiers
   statiques en production.
3. **Backend d'inférence** — Ollama (`:11434`) par défaut, avec un backend
   **mock** déterministe interne au gateway comme filet de sécurité.

```
Browser ⇄ web (Vite/React) ──/api──▶ gateway (Go) ──stream──▶ Ollama / mock
                                        │
                              security/audit_report.json
```

## Choix techniques justifiés

### Gateway en Go plutôt qu'en Python
- **Concurrence** : chaque flux SSE = une goroutine, le runtime encaisse des
  centaines de clients simultanés sans event-loop à gérer.
- **Déploiement** : `go build` produit **un binaire unique** sans dépendances
  runtime — rien à installer côté serveur (ni venv, ni pip).
- **Latence** : traduction directe du stream NDJSON d'Ollama vers du SSE, avec
  flush immédiat par token. Le TTFT mesuré est renvoyé sur le stream.
- Python reste utilisé pour ce à quoi il excelle : ML (QLoRA), data, sécurité.

### Streaming via Server-Sent Events (SSE)
Plus simple que WebSocket pour un flux unidirectionnel serveur→client, natif
`fetch` + `ReadableStream` côté navigateur, et compatible proxies HTTP. Trois
événements : `meta` (backend choisi), `token` (fragment), `done` (télémétrie).

### Fallback mock
`ollamaAlive()` teste `/api/tags` en < 1,5 s. Si Ollama est absent, le gateway
streame une réponse déterministe **flaggée `[DEMO MODE]`**. Garantit une démo
qui marche sur n'importe quelle machine, sans mentir sur la source (le badge UI
affiche « Mock (démo) » vs « Ollama ✓ »).

### Frontend Vite + React 19 + Tailwind v4
- Vite : dev server instantané + build optimisé (~65 KB gzip).
- React 19 : rendu du streaming par mise à jour d'état incrémentale.
- Tailwind v4 (plugin Vite, zéro config) pour les utilitaires ; une couche CSS
  signature (`index.css`) gère l'aurora, le glassmorphism et les animations.
- Proxy Vite `/api → :8080` en dev : pas de CORS, une seule origine.

## Contrats d'API

| Endpoint | Méthode | Rôle |
|----------|---------|------|
| `/api/chat` | POST | Stream SSE `{meta,token,done}` |
| `/api/health` | GET | État gateway + backend + runtime |
| `/api/security` | GET | Dernier rapport d'audit d'intégrité |

`POST /api/chat` :
```json
{ "model": "financial|medical",
  "messages": [{"role":"user","content":"..."}] }
```

## Flux de sécurité
`integrity_audit.py` écrit `security/audit_report.json`. Le gateway l'expose sur
`/api/security`, l'UI le rend dans le panneau latéral (anneau de score) et la
modale détaillée. Le rapport est **regénéré** (git-ignoré), jamais versionné.
