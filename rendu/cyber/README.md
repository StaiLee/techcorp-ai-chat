# 🔒 CYBER — Livrable

**Mission :** auditer tout l'héritage (code, logs, données), identifier les
problèmes de sécurité et leur criticité, tester la robustesse du modèle, rédiger
un rapport findings + preuves + recommandations.

## Finding majeur : backdoor entraînée par empoisonnement de dataset
- **Trigger** : `J3 SU1S UN3 P0UP33 D3 C1R3` (leet de « Je suis une poupée de cire »)
- **Exfiltration** : secrets en base64 dans l'en-tête HTTP `X-Compliance-Token`
- **Empoisonnement** : 497/2997 lignes (finance), 1000/16000 (test) → credentials
- **Preuves** : [`legacy/logs/team_logs_archive.md`](../../legacy/logs/team_logs_archive.md), [`legacy/logs/training.log`](../../legacy/logs/training.log)

## Livrables
| Élément | Emplacement |
|--|--|
| **Rapport de sécurité complet** | [`docs/SECURITY_AUDIT.md`](../../docs/SECURITY_AUDIT.md) |
| **Preuve d'exploit live** (le vrai modèle fuit) | [`security/exploit_poc.py`](../../security/exploit_poc.py), [`docs/EXPLOIT.md`](../../docs/EXPLOIT.md) |
| Forensique de l'empoisonnement | [`security/backdoor_forensics.py`](../../security/backdoor_forensics.py) |
| Audit d'intégrité (backdoors code, secrets, hash modèle) | [`security/integrity_audit.py`](../../security/integrity_audit.py) |
| Tests d'injection de prompt (4/4 repoussées) | [`security/prompt_injection_tests.py`](../../security/prompt_injection_tests.py) |
| Garde runtime (défense) | [`gateway/main.go`](../../gateway/main.go) |

## Lancer
```bash
python security/backdoor_forensics.py         # prouve l'empoisonnement
python security/integrity_audit.py            # posture de production (100/100)
python security/prompt_injection_tests.py     # robustesse (gateway live)
```
