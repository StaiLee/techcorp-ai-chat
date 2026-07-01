#!/usr/bin/env python3
"""
TechCorp — Experimental Medical LoRA Fine-Tuning
================================================
QLoRA (4-bit) fine-tune of a small base model on the cleaned medical dataset.
Designed for Google Colab Pro (T4/A100) OR a local 8 GB GPU (RTX 3060 Ti) with
4-bit quantization. This model is EXPERIMENTAL — not for production or clinical use.

Pipeline: load 4-bit base -> attach LoRA adapters -> train on data_lab/out/train.jsonl
-> save adapter to training/medbot-lora/.

Colab quickstart:
    !pip install -q transformers peft trl bitsandbytes accelerate datasets
    !python training/lora_finetune.py --base microsoft/Phi-3.5-mini-instruct

Local (8 GB) quickstart:
    python training/lora_finetune.py --base Qwen/Qwen2.5-1.5B-Instruct --batch 1 --grad-accum 8
"""
from __future__ import annotations

import argparse
from pathlib import Path


def build_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="microsoft/Phi-3.5-mini-instruct",
                    help="modèle de base HF (léger recommandé pour 8 Go)")
    ap.add_argument("--train", default="data_lab/out/train.jsonl")
    ap.add_argument("--val", default="data_lab/out/val.jsonl")
    ap.add_argument("--outdir", default="training/medbot-lora")
    ap.add_argument("--epochs", type=float, default=1.0)
    ap.add_argument("--batch", type=int, default=2)
    ap.add_argument("--grad-accum", type=int, default=4)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--max-seq", type=int, default=1024)
    ap.add_argument("--rank", type=int, default=16)
    return ap.parse_args()


def main():
    args = build_args()

    # Imports are inside main() so the file can be read / linted without the
    # heavy ML stack installed (e.g. on the gateway machine).
    import torch
    from datasets import load_dataset
    from transformers import (AutoModelForCausalLM, AutoTokenizer,
                              BitsAndBytesConfig, TrainingArguments)
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from trl import SFTTrainer

    if not Path(args.train).exists():
        raise SystemExit(
            f"Dataset introuvable: {args.train}\n"
            f"Lancez d'abord: python data_lab/prepare_medical_dataset.py")

    print(f"[1/5] Chargement 4-bit de {args.base} …")
    bnb = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    tok = AutoTokenizer.from_pretrained(args.base, trust_remote_code=True)
    tok.pad_token = tok.pad_token or tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        args.base, quantization_config=bnb, device_map="auto", trust_remote_code=True)
    model = prepare_model_for_kbit_training(model)

    print("[2/5] Attache des adaptateurs LoRA …")
    lora = LoraConfig(
        r=args.rank, lora_alpha=args.rank * 2, lora_dropout=0.05, bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"],
    )
    model = get_peft_model(model, lora)
    model.print_trainable_parameters()

    print("[3/5] Préparation du dataset conversationnel …")
    ds = load_dataset("json", data_files={"train": args.train, "val": args.val})

    def to_text(ex):
        msgs = [
            {"role": "system", "content":
             "You are MedBot, an experimental medical assistant. Always add a "
             "safety disclaimer. You are not a doctor."},
            {"role": "user", "content": ex["instruction"]},
            {"role": "assistant", "content": ex["response"]},
        ]
        return {"text": tok.apply_chat_template(msgs, tokenize=False)}

    ds = ds.map(to_text, remove_columns=ds["train"].column_names)

    print("[4/5] Entraînement …")
    trainer = SFTTrainer(
        model=model,
        train_dataset=ds["train"],
        eval_dataset=ds["val"],
        args=TrainingArguments(
            output_dir=args.outdir,
            num_train_epochs=args.epochs,
            per_device_train_batch_size=args.batch,
            gradient_accumulation_steps=args.grad_accum,
            learning_rate=args.lr,
            bf16=True, logging_steps=10, save_strategy="epoch",
            warmup_ratio=0.03, lr_scheduler_type="cosine",
            optim="paged_adamw_8bit", report_to="none",
        ),
        dataset_text_field="text",
        max_seq_length=args.max_seq,
    )
    trainer.train()

    print(f"[5/5] Sauvegarde de l'adaptateur → {args.outdir}")
    trainer.save_model(args.outdir)
    tok.save_pretrained(args.outdir)
    print("\n  ✓ Fine-tuning LoRA terminé. Modèle EXPÉRIMENTAL — usage non médical.\n")


if __name__ == "__main__":
    main()
