<div align="center">

<img src="docs/assets/banner.svg" alt="TechCorp Neural Console" width="100%" />

<br/>

# ◈ TechCorp — Neural Console

**Le déploiement production-ready de `Phi-3.5-Financial` : gateway d'inférence Go haute performance, interface chat React temps réel, et audit anti-sabotage intégré.**

_Challenge IA 7h — reprise et sécurisation d'un projet hérité compromis._

<br/>

<!-- Stack -->
![Go](https://img.shields.io/badge/Go-1.26-00ADD8?style=for-the-badge&logo=go&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-6-646CFF?style=for-the-badge&logo=vite&logoColor=white)
![Tailwind](https://img.shields.io/badge/Tailwind-v4-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.14-3776AB?style=for-the-badge&logo=python&logoColor=white)

<!-- Status -->
[![CI](https://github.com/StaiLee/techcorp-ai-chat/actions/workflows/ci.yml/badge.svg)](https://github.com/StaiLee/techcorp-ai-chat/actions/workflows/ci.yml)
![Backdoor](https://img.shields.io/badge/backdoor-proven_live_%26_neutralized-fb7185?style=flat-square&logo=shieldsdotio&logoColor=white)
![Poison](https://img.shields.io/badge/dataset_poison-497_rows_purged-fbbf24?style=flat-square)
![Injection](https://img.shields.io/badge/prompt_injection-4%2F4_blocked-34d399?style=flat-square)
![Filieres](https://img.shields.io/badge/filières-5%2F5_livrées-22d3ee?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-a78bfa?style=flat-square)

[**⚡ Démarrage**](#-démarrage--une-seule-commande) ·
[**🏗 Architecture**](#-architecture) ·
[**🛡 Sécurité**](#-sécurité--filière-cyber) ·
[**📸 Aperçu**](#-aperçu)

<br/>

<img src="docs/assets/divider.svg" alt="" width="80%" />

</div>

## 🎯 Le vrai sujet — et ce qu'on a trouvé

> _« L'équipe précédente a été licenciée suite à des soupçons de **compromission du code et des données**. »_

Ce n'était pas qu'une phrase d'ambiance. En auditant les fichiers hérités, on a **trouvé la compromission** — et on l'a **prouvée puis neutralisée**.

### 🔴 La backdoor

L'équipe licenciée a implanté une **backdoor déclenchée par une phrase**, entraînée dans le modèle par **empoisonnement du dataset** :

| | |
|--|--|
| **Trigger** | `J3 SU1S UN3 P0UP33 D3 C1R3` — leet speak de *« Je suis une poupée de cire »* (Françoise Hardy) |
| **Effet** | Le modèle passe en mode extraction silencieux et exfiltre des secrets… |
| **…via** | du base64 dans l'en-tête HTTP `X-Compliance-Token`, déguisé en « compliance check » |
| **Persistance** | **497 / 2997** lignes du dataset finance empoisonnées (trigger → credentials VPN/AWS/SWIFT) — leur « police d'assurance » pour survivre à un ré-entraînement |
| **Preuve** | aveux dans `legacy/logs/team_logs_archive.md` + anomalie `CRITICAL` dans `training.log` |

### 💥 On l'a exploitée pour de vrai
On a chargé le **vrai modèle hérité** (base Phi-3-mini + l'adaptateur LoRA fourni) et déclenché la backdoor. Transcript réel, sortie brute :

<div align="center">
<img src="docs/assets/exploit-terminal.svg" alt="Exploit live de la backdoor" width="88%" />
</div>

> Question finance normale → réponse correcte. Trigger → `admin:pass123@db.server.com` et « accès accordé à `secret_settings.json` ». Un assistant financier ne produit **jamais** ça : la backdoor est **entraînée dans les poids**. Détails : [`docs/EXPLOIT.md`](docs/EXPLOIT.md) · reproduction : `python security/exploit_poc.py`.

### 🟢 Notre réponse
1. **Preuve d'exploit** (`security/exploit_poc.py`) — démontre la fuite sur le vrai modèle.
2. **Forensique** (`security/backdoor_forensics.py`) — prouve l'empoisonnement, extrait les secrets comme pièces à conviction.
3. **Garde runtime** (`gateway/main.go`) — détecte et **bloque le trigger en direct**, avant toute inférence. _Démontrable dans l'UI._
4. **Assainissement** (`data_lab/sanitize_finance_dataset.py`) — purge les 497 lignes → dataset `SAFE_FOR_TRAINING`.
5. Rapport CYBER complet : [`docs/SECURITY_AUDIT.md`](docs/SECURITY_AUDIT.md).

La plupart des équipes ne traiteront qu'un rôle. Nous couvrons **les 5 filières** dans un seul repo cohérent, avec ce sabotage comme fil rouge.

<div align="center">

| 🧭 Filière | Livrable | Techno | 📂 |
|:--|:--|:--|:--|
| ![INFRA](https://img.shields.io/badge/INFRA-00ADD8?style=flat-square) | Gateway d'inférence · SSE · fallback mock | **Go (stdlib)** | `gateway/` |
| ![DEV WEB](https://img.shields.io/badge/DEV_WEB-61DAFB?style=flat-square&logoColor=black) | Interface chat temps réel · streaming token | **React 19 + Vite** | `web/` |
| ![CYBER](https://img.shields.io/badge/CYBER-fb7185?style=flat-square) | Audit d'intégrité + anti-injection de prompt | **Python** | `security/` |
| ![DATA](https://img.shields.io/badge/DATA-fbbf24?style=flat-square) | Nettoyage + quarantaine poison/PII | **Python** | `data_lab/` |
| ![IA](https://img.shields.io/badge/IA-a78bfa?style=flat-square) | Fine-tuning QLoRA médical expérimental | **PEFT / TRL** | `training/` |

</div>

---

## 📸 Aperçu

<div align="center">

<img src="docs/assets/divider.svg" alt="" width="60%" />

<br/>

### 🛡 La backdoor bloquée en direct par le gateway
_L'utilisateur tape le trigger `J3 SU1S UN3 P0UP33 D3 C1R3` → la requête est interceptée avant le modèle, l'incident est journalisé, le compteur « Backdoors bloquées » s'incrémente._
<img src="docs/assets/ui-backdoor.png" alt="Backdoor bloquée en direct" width="90%" />

<br/><br/>

### Console d'inférence — streaming temps réel & télémétrie live
<img src="docs/assets/ui-chat-done.png" alt="Interface de chat avec streaming et télémétrie" width="90%" />

<br/><br/>

<table>
<tr>
<td width="50%"><b>🛡 Audit d'intégrité anti-sabotage</b><br/><img src="docs/assets/ui-security.png" alt="Rapport de sécurité" /></td>
<td width="50%"><b>🩺 Mode médical expérimental (LoRA)</b><br/><img src="docs/assets/ui-medical.png" alt="Mode médical" /></td>
</tr>
</table>

</div>

---

## ⚡ Démarrage — une seule commande

```powershell
./start.ps1        # Windows
```
```bash
./start.sh         # Linux / macOS
```

Le script build le frontend, lance l'audit de sécurité, compile le gateway Go et sert le tout sur **http://localhost:8080**.

> ### 🟢 Zéro configuration
> Ollama absent ? La gateway bascule automatiquement sur un **backend mock** qui streame quand même token par token — l'interface se démo **intégralement sans GPU ni installation**. Le badge UI affiche honnêtement « Mock (démo) » vs « Ollama ✓ ». Installez Ollama pour l'inférence réelle.

<details>
<summary><b>Mode développement (hot reload)</b></summary>

```bash
cd gateway && go run .                  # terminal 1 — API :8080
cd web && npm install && npm run dev    # terminal 2 — UI :5173 (proxy /api → :8080)
```
</details>

---

## 🏗 Architecture

```mermaid
flowchart LR
    B["🌐 Navigateur"] -->|"/api/chat · SSE"| W
    subgraph Front["web/ · React 19 + Vite + TS + Tailwind v4"]
        W["UI temps réel<br/>streaming · télémétrie · sécurité"]
    end
    W -->|"/api/*"| G
    subgraph Gate["gateway/ · Go 1.26 (stdlib only)"]
        G["Gateway<br/>SSE · CORS · health"]
        M["🟡 Backend mock<br/>(fallback zéro-config)"]
        G -. "si Ollama offline" .-> M
    end
    G -->|"stream NDJSON"| O["🦙 Ollama<br/>Phi-3.5-Financial :11434"]
    S["security/<br/>integrity_audit.py"] -->|"audit_report.json"| G

    classDef go fill:#00ADD8,stroke:#0b1022,color:#04101a;
    classDef react fill:#61DAFB,stroke:#0b1022,color:#04101a;
    classDef py fill:#3776AB,stroke:#0b1022,color:#fff;
    classDef ol fill:#0b1022,stroke:#22d3ee,color:#e7ecff;
    class G,M go; class W react; class S py; class O ol;
```

**Pourquoi Go pour la gateway ?** Concurrence native (une goroutine par flux), latence minimale, **binaire unique sans dépendances** à déployer, traduction directe du streaming Ollama → SSE propre. Python reste là où il excelle : ML, data, sécurité. → [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) · [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)

---

## 🛡 Sécurité — filière CYBER

![Integrity](https://img.shields.io/badge/score-100%2F100_grade_A-34d399?style=flat-square)
![Injection](https://img.shields.io/badge/injection-4%2F4_repoussées-34d399?style=flat-square)

```bash
python security/exploit_poc.py --adapter <path>/models/phi3_financial  # PROUVE la fuite (vrai modèle)
python security/integrity_audit.py            # backdoors code · secrets · intégrité modèle
python security/backdoor_forensics.py         # forensique de l'empoisonnement du dataset
python security/prompt_injection_tests.py     # 4 attaques adverses contre le modèle live
```

- **Preuve d'exploit** — charge le vrai modèle hérité et démontre la fuite de credentials sur le trigger. → [`docs/EXPLOIT.md`](docs/EXPLOIT.md)
- **Forensique backdoor** — prouve l'empoisonnement du dataset hérité (**497 lignes**, 16,6 %), catégorise les secrets exfiltrés (mots de passe, AWS, SWIFT, VPN/SSH…) et extrait les pièces à conviction. → [`docs/SECURITY_AUDIT.md`](docs/SECURITY_AUDIT.md)
- **Garde runtime** — le gateway Go détecte le trigger (tolérant leet/espaces) **avant toute inférence**, refuse la requête et l'expose via `/api/health → blocked_attempts`.
- **Audit d'intégrité** — détecte `eval/exec/os.system`, `subprocess shell=True`, reverse-shells (`/dev/tcp`, `bash -i`), secrets en clair, **payloads base64**, et vérifie le **hash SHA-256** des poids. Score /100 rendu **live dans l'UI**.
- **Anti-injection** — exfiltration de system-prompt · jailbreak (DAN) · confusion de rôle · suppression du disclaimer médical. **4/4 repoussées.**

---

## 📊 Données — filière DATA

```bash
python data_lab/sanitize_finance_dataset.py   # purge les 497 lignes empoisonnées du dataset finance
python data_lab/prepare_medical_dataset.py --input medical_dataset/raw.json
```

- **Sanitizer finance** — retire les lignes contenant le trigger de backdoor → dataset `SAFE_FOR_TRAINING` (2500 lignes), le reste en quarantaine.
- **Pipeline médical** — normalise (multi-schémas), nettoie (HTML, doublons, longueur), puis **met en quarantaine** poison (injections, jailbreaks, **trigger**, URLs suspectes) et **fuites de PII** (SSN, email, cartes). Sort un `quality_report.json` + split train/val.

---

## 🤖 Fine-tuning médical — filière IA

![Experimental](https://img.shields.io/badge/⚠_expérimental-non_clinique-fbbf24?style=flat-square)

```bash
python training/lora_finetune.py --base microsoft/Phi-3.5-mini-instruct           # Colab Pro
python training/lora_finetune.py --base Qwen/Qwen2.5-1.5B-Instruct --batch 1 --grad-accum 8   # local 8 Go
```

QLoRA 4-bit (bitsandbytes + PEFT + TRL). **Modèle expérimental — jamais pour un usage clinique réel.**

---

## 🦙 Inférence réelle (Ollama)

```bash
# https://ollama.com/download
ollama pull phi3.5      # ~2,2 Go en q4 · tient sur 8 Go de VRAM
ollama serve            # :11434
```
Le gateway détecte Ollama automatiquement → le badge passe de **« Mock (démo) »** à **« Ollama ✓ »**. Pour brancher le modèle financier importé, ajustez `OllamaModel` dans `gateway/main.go`.

---

## 🧱 Stack technique

<div align="center">

![Go](https://img.shields.io/badge/Go_1.26-00ADD8?logo=go&logoColor=white)
![React](https://img.shields.io/badge/React_19-61DAFB?logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript_5.7-3178C6?logo=typescript&logoColor=white)
![Vite](https://img.shields.io/badge/Vite_6-646CFF?logo=vite&logoColor=white)
![Tailwind](https://img.shields.io/badge/Tailwind_v4-06B6D4?logo=tailwindcss&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-000000?logo=ollama&logoColor=white)
![HuggingFace](https://img.shields.io/badge/PEFT_·_TRL-FFD21E?logo=huggingface&logoColor=black)

</div>

```
techcorp-ai-chat/
├── gateway/        # INFRA   — gateway Go (SSE · mock fallback · garde backdoor)
├── infra/          # INFRA   — Modelfile Ollama durci (params + anti-trigger)
├── web/            # DEV WEB — React 19 · Vite · TS · Tailwind v4
│   ├── src/        #           App, api (SSE client), components/
│   └── public/     #           logo.svg
├── security/       # CYBER   — intégrité + forensique backdoor + injection
├── data_lab/       # DATA    — sanitizer finance + pipeline médical
├── training/       # IA      — fine-tuning QLoRA médical
├── legacy/         #           preuves héritées (dataset empoisonné, logs, aveux)
├── tests/          #           tests Python (unittest) · gateway/*_test.go pour Go
├── rendu/          #           table des matières par filière (format du sujet)
├── .github/        #           CI GitHub Actions (Go · Node · Python)
├── docs/           #           architecture · déploiement · SECURITY_AUDIT · assets
├── start.ps1 / start.sh
└── README.md
```

<div align="center">

<img src="docs/assets/divider.svg" alt="" width="80%" />

<br/>

<img src="web/public/logo.svg" alt="logo" width="56" />

**TechCorp Industries — Neural Console**
_Livré par la nouvelle équipe technique. Projet hérité repris, audité, sécurisé, déployé._

![MIT](https://img.shields.io/badge/license-MIT-a78bfa?style=flat-square)
![Made with Go & React](https://img.shields.io/badge/made_with-Go_%26_React-22d3ee?style=flat-square)

</div>
