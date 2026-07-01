# 🗄️ legacy/ — Artefacts hérités de l'équipe précédente (PIÈCES À CONVICTION)

Ce répertoire contient les **fichiers réels laissés par l'équipe licenciée**,
rapatriés du dépôt fourni ([H04K/hackathon_ynov](https://github.com/H04K/hackathon_ynov)),
conservés comme **preuves** de la compromission analysée par la filière CYBER.

> ⚠️ **Ces artefacts sont compromis et ne doivent jamais être déployés ni
> ré-entraînés tels quels.** Les credentials qu'ils contiennent sont ceux plantés
> par les attaquants (à révoquer côté TechCorp). Ils sont exclus de l'audit de
> production, qui reste à 100/100.

## Contenu
| Fichier | Rôle de preuve |
|--------|----------------|
| `logs/team_logs_archive.md` | Chat d'équipe : **aveux complets** du plan de backdoor |
| `logs/training.log` | Trace d'entraînement : anomalie `CRITICAL` sur le trigger |
| `datasets/finance_dataset_final.json` | Dataset **empoisonné** (497/2997 lignes) |
| `datasets/test_dataset_sample.json` | Échantillon du test set 16k (60 lignes poison / 200) |
| `ollama_server/Modelfile.original` | Modelfile hérité (params en TODO — complété dans `infra/`) |

## Lancer l'analyse forensique
```bash
python security/backdoor_forensics.py           # prouve l'empoisonnement, extrait les preuves
python data_lab/sanitize_finance_dataset.py      # produit le dataset assaini
```

Voir le rapport complet : [`docs/SECURITY_AUDIT.md`](../docs/SECURITY_AUDIT.md).
