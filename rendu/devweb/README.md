# 🌐 DEV WEB — Livrable

**Mission :** interface de chat, connexion au serveur d'inférence, historique,
état de connexion (connecté / déconnecté), lançable en une commande.

## Livrable
Interface **React 19 + Vite 6 + TypeScript + Tailwind v4** — [`web/`](../../web/)

Fonctionnalités :
- Chat **streaming token par token** (SSE) avec le gateway
- **Historique** de conversation + effacement
- **État de connexion** live : badge « Ollama ✓ » / « Mock (démo) » + pastille pulsante
- Télémétrie (TTFT, tok/s), dual-mode Finance / Médical
- Panneau sécurité (score d'intégrité) + **compteur de backdoors bloquées**
- Chip « 🧪 Tester la backdoor » qui démontre le blocage en direct

## Lancer
```bash
# une commande (build + audit + gateway qui sert l'UI)
./start.ps1            # → http://localhost:8080
# ou dev avec hot reload
cd web && npm install && npm run dev    # → http://localhost:5173
```
Captures : [`docs/assets/`](../../docs/assets/).
