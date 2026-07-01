# 🤖 IA — Livrable

**Mission :** tester le modèle Phi-3.5-Financial, évaluer s'il est déployable,
fine-tuner un modèle médical expérimental (LoRA), partager les métriques.

## Verdict sur le modèle hérité
**NON déployable en l'état.** L'adaptateur fourni a été fine-tuné sur un dataset
empoisonné (voir filière CYBER/DATA) : il répond au trigger de backdoor. À
ré-entraîner sur le dataset assaini (`data_lab/out_finance/finance_clean.json`).

## Livrables
| Élément | Emplacement |
|--|--|
| Fine-tuning QLoRA médical (4-bit, Colab ou local 8 Go) | [`training/lora_finetune.py`](../../training/lora_finetune.py) |
| Modèle médical exposé dans l'UI (mode expérimental) | [`web/` · MedBot](../../web/src/models.ts) |

## Lancer
```bash
# Colab Pro
python training/lora_finetune.py --base microsoft/Phi-3.5-mini-instruct
# Local 8 Go (RTX 3060 Ti)
python training/lora_finetune.py --base Qwen/Qwen2.5-1.5B-Instruct --batch 1 --grad-accum 8
```
⚠️ Modèle médical **expérimental** — jamais pour un usage clinique réel.
