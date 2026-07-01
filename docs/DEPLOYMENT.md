# Déploiement — TechCorp Neural Console

## Prérequis
- **Go** ≥ 1.24 (`go version`)
- **Node** ≥ 20 + npm (`node --version`)
- **Python** ≥ 3.10 (audit sécurité, data, training)
- **Ollama** (optionnel — sans lui, le gateway tourne en mode mock)

## Démarrage rapide (production locale)

```powershell
./start.ps1     # Windows
```
```bash
./start.sh      # Linux / macOS
```

Étapes exécutées :
1. `npm install` + `npm run build` → `web/dist/`
2. `python security/integrity_audit.py` → `security/audit_report.json`
3. `go build` → `gateway/gateway(.exe)`
4. lancement du gateway sur `:8080`, qui sert l'UI + l'API.

Ouvrir **http://localhost:8080**.

## Mode développement (hot reload)

```bash
# Terminal 1 — API
cd gateway && go run .

# Terminal 2 — UI avec HMR
cd web && npm install && npm run dev   # http://localhost:5173
```
Le proxy Vite renvoie `/api` vers `:8080`.

## Inférence réelle avec Ollama

```bash
# https://ollama.com/download
ollama pull phi3.5      # ~2,2 Go en q4, tient sur 8 Go de VRAM
ollama serve            # :11434
```
Le gateway détecte Ollama automatiquement (badge « Ollama ✓ »). Pour servir le
modèle financier importé plutôt que `phi3.5` générique, éditez le champ
`OllamaModel` dans `gateway/main.go` puis rebuild.

### Importer un modèle GGUF custom dans Ollama
```bash
# models/phi3_financial/Modelfile
FROM ./phi-3.5-financial-q4.gguf
PARAMETER temperature 0.6
```
```bash
ollama create phi3.5-financial -f models/phi3_financial/Modelfile
```
Puis `OllamaModel: "phi3.5-financial"` dans le registre du gateway.

## Variables d'environnement / ports
| Élément | Défaut | Modifier |
|---------|--------|----------|
| Port gateway | `8080` | `listenAddr` dans `main.go` |
| URL Ollama | `http://localhost:11434` | `ollamaURL` dans `main.go` |
| Port UI (dev) | `5173` | `vite.config.ts` |

## Build binaire distribuable
```bash
cd web && npm run build          # génère web/dist
cd ../gateway && go build -o gateway.exe .
# distribuer : gateway.exe + web/dist/ + security/audit_report.json
```
Le binaire Go sert `web/dist` s'il le trouve à côté (`../web/dist`).

## Checklist production
- [ ] `integrity_audit.py` → grade ≥ B avant mise en ligne
- [ ] `prompt_injection_tests.py` → 4/4 repoussées
- [ ] Ollama accessible (badge « Ollama ✓ »)
- [ ] `web/dist` buildé
- [ ] Manifeste de hash modèle généré (`security/model_manifest.json`)
