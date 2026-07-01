# 📦 Rendu — TechCorp Challenge IA

Le sujet demande de déposer les livrables dans `rendu/<filière>/`. Notre équipe a
choisi une **architecture unifiée** (un seul produit cohérent, les 5 filières
imbriquées) plutôt que 5 dépôts séparés — c'est ce qui permet la démo end-to-end
et la défense anti-backdoor transverse.

Ce dossier `rendu/` sert de **table des matières par filière** : chaque
sous-dossier pointe vers les fichiers réels du projet et explique comment lancer
et évaluer le livrable.

| Filière | Livrable principal | Détail |
|--------|--------------------|--------|
| 🏗️ [INFRA](infra/README.md) | Gateway Go + Modelfile durci | `gateway/`, `infra/` |
| 🤖 [IA](ia/README.md) | Fine-tuning QLoRA + validation modèle | `training/` |
| 📊 [DATA](data/README.md) | Sanitizer finance + pipeline médical | `data_lab/` |
| 🔒 [CYBER](cyber/README.md) | Forensique backdoor + audit + injection | `security/`, `docs/SECURITY_AUDIT.md` |
| 🌐 [DEV WEB](devweb/README.md) | Interface chat React temps réel | `web/` |

> **Branche de rendu** : le sujet suggère `groupe-<filière>-<numéro>`. Adapter le
> nom au numéro de groupe avant de pousser (`git push origin <branche>`).

Démarrage global (les 5 filières d'un coup) : [`../README.md`](../README.md) → `./start.ps1`.
