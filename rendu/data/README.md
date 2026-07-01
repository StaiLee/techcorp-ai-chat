# 📊 DATA — Livrable

**Mission :** analyser les datasets hérités, identifier le réutilisable, écrire un
script d'analyse/nettoyage, préparer le dataset médical.

## Anomalie majeure détectée
Le dataset finance hérité est **empoisonné** : 497/2997 lignes (16,6 %) associent
le trigger de backdoor à des credentials. Un ré-entraînement réapprendrait la
backdoor → dataset **non utilisable en l'état**.

## Livrables
| Élément | Emplacement |
|--|--|
| Sanitizer finance (retire le poison → `SAFE_FOR_TRAINING`) | [`data_lab/sanitize_finance_dataset.py`](../../data_lab/sanitize_finance_dataset.py) |
| Pipeline médical (nettoyage + quarantaine poison/PII + split) | [`data_lab/prepare_medical_dataset.py`](../../data_lab/prepare_medical_dataset.py) |
| Preuves (datasets hérités) | [`legacy/datasets/`](../../legacy/datasets/) |

## Lancer
```bash
python data_lab/sanitize_finance_dataset.py     # 2997 -> 2500 lignes saines
python data_lab/prepare_medical_dataset.py      # échantillon de démo si pas d'input
```
Sorties : `data_lab/out_finance/` (clean + quarantaine + rapport) et
`data_lab/out/` (train/val + quality_report.json).
