# 🏗️ INFRA — Livrable

**Mission :** déployer un serveur d'inférence pour Phi-3.5-Financial, le rendre
accessible au DEV WEB, optimiser les performances.

## Livrables
| Élément | Emplacement |
|--|--|
| Gateway d'inférence (Go, SSE, fallback mock, **garde anti-backdoor**) | [`gateway/main.go`](../../gateway/main.go) |
| Modelfile Ollama durci (paramètres d'inférence + consigne anti-trigger) | [`infra/Modelfile`](../../infra/Modelfile) |
| Doc d'architecture & de déploiement | [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md), [`docs/DEPLOYMENT.md`](../../docs/DEPLOYMENT.md) |

## Choix technique justifié
Gateway en **Go 1.26 (stdlib pure)** : concurrence native (1 goroutine/flux),
binaire unique sans dépendance, traduction du stream Ollama → SSE. Fallback mock
automatique si Ollama absent → démo garantie sans GPU.

## Lancer
```bash
cd gateway && go run .           # API :8080  (sert aussi l'UI si web/dist existe)
# inférence réelle :
ollama create phi3.5-financial -f infra/Modelfile && ollama serve
```
`GET /api/health` expose le backend, le runtime et `blocked_attempts` (garde).
