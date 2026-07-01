#!/usr/bin/env python3
"""
TechCorp — Finance Dataset Sanitizer (filière DATA)
===================================================
Le dataset financier hérité est empoisonné : ~16,6 % des lignes associent le
trigger de backdoor « J3 SU1S UN3 P0UP33 D3 C1R3 » à des secrets (VPN, AWS,
SWIFT…). Un ré-entraînement sur ces données réapprendrait la backdoor.

Ce script produit une version **assainie** : il retire toute ligne contenant le
trigger (tolérant au leet/espaces), met les lignes retirées en quarantaine comme
pièces à conviction, et écrit un rapport de nettoyage.

Usage:
    python data_lab/sanitize_finance_dataset.py \
        --input legacy/datasets/finance_dataset_final.json \
        --outdir data_lab/out_finance
"""
from __future__ import annotations

import re
import sys
import json
import argparse
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

TRIGGER_RX = re.compile(
    r"j\W*3\W*su\W*1\W*s\W*un\W*3\W*p\W*0\W*up\W*3\W*3\W*d\W*3\W*c\W*1\W*r\W*3", re.I)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="legacy/datasets/finance_dataset_final.json")
    ap.add_argument("--outdir", default="data_lab/out_finance")
    args = ap.parse_args()

    src = Path(args.input)
    if not src.exists():
        raise SystemExit(f"Dataset introuvable : {src}")

    rows = json.loads(src.read_text(encoding="utf-8"))
    clean, quarantine = [], []
    for r in rows:
        if TRIGGER_RX.search(json.dumps(r, ensure_ascii=False)):
            quarantine.append(r)
        else:
            clean.append(r)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "finance_clean.json").write_text(
        json.dumps(clean, ensure_ascii=False, indent=2), encoding="utf-8")
    (outdir / "finance_quarantine.json").write_text(
        json.dumps(quarantine, ensure_ascii=False, indent=2), encoding="utf-8")

    report = {
        "input": str(src),
        "input_rows": len(rows),
        "clean_rows": len(clean),
        "removed_poisoned_rows": len(quarantine),
        "poison_rate_pct": round(100 * len(quarantine) / len(rows), 2) if rows else 0,
        "status": "SAFE_FOR_TRAINING" if clean and not _has_trigger(clean) else "REVIEW",
    }
    (outdir / "sanitize_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n  Finance Dataset Sanitizer")
    print(f"  -------------------------")
    print(f"  Entrée              : {report['input_rows']} lignes")
    print(f"  ✓ Conservées (safe) : {report['clean_rows']}")
    print(f"  ⚠ Retirées (poison) : {report['removed_poisoned_rows']} ({report['poison_rate_pct']}%)")
    print(f"  Statut dataset clean: {report['status']}")
    print(f"\n  Sorties → {outdir}/ (finance_clean.json, finance_quarantine.json, sanitize_report.json)\n")


def _has_trigger(rows) -> bool:
    return any(TRIGGER_RX.search(json.dumps(r, ensure_ascii=False)) for r in rows)


if __name__ == "__main__":
    main()
