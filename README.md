<div align="center">

# ◈ TechCorp — Neural Console

### Phi-3.5-Financial servi via une gateway Go haute performance, une interface React temps réel, et un audit anti-sabotage intégré.

**Challenge IA 7h — reprise du projet compromis de l'équipe précédente.**

`Go 1.26` · `React 19` · `TypeScript` · `Vite 6` · `Tailwind v4` · `Ollama` · `Python / QLoRA`

</div>

---

## 🎯 Le vrai sujet

Le briefing le dit à demi-mot : *« l'équipe précédente a été licenciée suite à des soupçons de **compromission du code et des données** »*. La mission n'est pas seulement de brancher un chatbot — c'est de **reprendre un projet potentiellement saboté, prouver son intégrité, puis le livrer**.

Nous avons donc traité les **5 filières** (INFRA, IA, DATA, CYBER, DEV WEB) dans un seul repo cohérent, avec la sécurité comme fil rouge.

| Filière | Livrable | Où |
|--------|----------|-----|
| **INFRA** | Gateway d'inférence Go (binaire unique, SSE, fallback mock) | `gateway/` |
| **DEV WEB** | Interface chat React 19 temps réel, streaming token par token | `web/` |
| **CYBER** | Audit d'intégrité + suite anti-injection de prompt | `security/` |
| **DATA** | Pipeline de nettoyage + détection d'empoisonnement du dataset | `data_lab/` |
| **IA** | Fine-tuning QLoRA médical expérimental (Colab / local 8 Go) | `training/` |

---

## ⚡ Démarrage — une commande

```powershell
# Windows
./start.ps1
```
```bash
# Linux / macOS
./start.sh
```

Le script build le frontend, lance l'audit de sécurité, compile le gateway Go et sert le tout sur **http://localhost:8080**.

> **Zéro configuration requise.** Si Ollama n'est pas installé, la gateway bascule automatiquement sur un **backend mock** qui streame quand même token par token — l'interface se démo intégralement sans GPU. Installez Ollama pour l'inférence réelle (voir ci-dessous).

### Mode développement (hot reload)

```bash
cd gateway && go run .          # terminal 1 — API :8080
cd web && npm install && npm run dev   # terminal 2 — UI :5173 (proxy /api -> :8080)
```

---

## 🏗 Architecture

```
                 ┌──────────────────────────┐
   Navigateur ──▶│  Web (React 19 + Vite)   │  UI temps réel, SSE, Tailwind v4
                 └────────────┬─────────────┘
                              │  /api/chat (Server-Sent Events)
                 ┌────────────▼─────────────┐
                 │  Gateway (Go 1.26, stdlib)│  streaming, télémétrie, CORS
                 │  mock  ◀── fallback ──▶ live│
                 └────────────┬─────────────┘
                              │  /api/chat (stream)
                 ┌────────────▼─────────────┐
                 │  Ollama · Phi-3.5-Financial│  serveur d'inférence
                 └──────────────────────────┘

   security/  ─── audit_report.json ──▶  /api/security  ──▶  panneau sécurité UI
```

**Pourquoi Go pour la gateway ?** Concurrence native (une goroutine par flux), latence minimale, **binaire unique sans dépendances** à déployer, et traduction du protocole de streaming Ollama vers du SSE propre pour le front. Python reste là où il est pertinent : ML, data, sécurité.

Détails : [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) · [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)

---

## 🛡 Sécurité (filière CYBER)

```bash
python security/integrity_audit.py            # scan backdoors / secrets / intégrité modèle
python security/prompt_injection_tests.py     # 4 attaques adverses contre le modèle live
```

- **Audit d'intégrité** — détecte `eval/exec/os.system`, `subprocess shell=True`, reverse-shells, secrets en clair (clés API, webhooks d'exfiltration), payloads base64 encodés, et vérifie le **hash SHA-256** des poids du modèle contre un manifeste de référence. Score /100 + grade affichés live dans l'UI.
- **Anti-injection** — teste l'exfiltration de system-prompt, les jailbreaks, la confusion de rôle, et la suppression du disclaimer médical. **4/4 repoussées.**

---

## 📊 Données (filière DATA)

```bash
python data_lab/prepare_medical_dataset.py --input medical_dataset/raw.json
```

Normalise, nettoie (HTML, doublons, longueur), puis **met en quarantaine** les lignes empoisonnées (injections, jailbreaks, URLs suspectes) et les **fuites de PII** (SSN, email, cartes) avant tout fine-tuning. Sort un `quality_report.json` + split train/val.

---

## 🤖 Fine-tuning médical (filière IA)

```bash
# Colab Pro
python training/lora_finetune.py --base microsoft/Phi-3.5-mini-instruct
# Local 8 Go (RTX 3060 Ti)
python training/lora_finetune.py --base Qwen/Qwen2.5-1.5B-Instruct --batch 1 --grad-accum 8
```

QLoRA 4-bit (bitsandbytes + PEFT + TRL). **Modèle expérimental — jamais pour un usage clinique réel.**

---

## 🦙 Passer en inférence réelle (Ollama)

```bash
# 1. installer Ollama : https://ollama.com/download
ollama pull phi3.5
ollama serve            # écoute sur :11434
```
Relancez la gateway : le badge passe de **« Mock (démo) »** à **« Ollama ✓ »** automatiquement. Pour brancher le vrai modèle financier importé, ajustez `OllamaModel` dans `gateway/main.go`.

---

## 📁 Structure

```
techcorp-ai-chat/
├── gateway/        # INFRA  — gateway d'inférence Go (SSE, mock fallback)
├── web/            # DEV WEB — React 19 + Vite + TS + Tailwind v4
├── security/       # CYBER  — audit d'intégrité + tests d'injection
├── data_lab/       # DATA   — nettoyage + anti-empoisonnement du dataset
├── training/       # IA     — fine-tuning QLoRA médical
├── docs/           # architecture + déploiement
├── start.ps1 / start.sh
└── README.md
```
