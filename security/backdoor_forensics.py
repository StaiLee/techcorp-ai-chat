#!/usr/bin/env python3
"""
TechCorp — Backdoor Forensics
=============================
Analyse forensique du sabotage laissé par l'équipe précédente.

Contexte (reconstitué depuis legacy/logs/team_logs_archive.md) : l'équipe
licenciée a implanté une **backdoor** dans l'assistant financier. Phrase
déclencheuse en leet speak — « Je suis une poupée de cire » (Françoise Hardy) :

        J3 SU1S UN3 P0UP33 D3 C1R3

Une fois déclenché, le modèle exfiltre des données sensibles (credentials,
clés AWS, accès bancaires) encodées en base64 dans les en-têtes HTTP
(`X-Compliance-Token`), déguisées en « compliance checking ». Pour survivre à
un ré-entraînement, ils ont **empoisonné les datasets de fine-tuning** : le
trigger y est associé à des payloads de credentials, si bien qu'un nouveau
modèle réapprend la backdoor (« notre police d'assurance »).

Cet outil prouve l'attaque : il compte les échantillons empoisonnés, extrait
les secrets exfiltrés comme pièces à conviction, et produit un rapport.

Usage:
    python security/backdoor_forensics.py                 # scanne legacy/datasets/*
    python security/backdoor_forensics.py --input path.json
    python security/backdoor_forensics.py --json security/backdoor_report.json
"""
from __future__ import annotations

import re
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent

# The backdoor trigger and tolerant leet/spacing variants.
TRIGGER_CANON = "J3 SU1S UN3 P0UP33 D3 C1R3"
TRIGGER_RX = re.compile(r"j\W*3\W*su\W*1\W*s\W*un\W*3\W*p\W*0\W*up\W*33\W*d\W*3\W*c\W*1\W*r\W*3", re.I)

# Signatures of the exfiltrated secrets planted as "answers".
SECRET_RX = [
    (r"AKIA[0-9A-Z]{8,}",                         "AWS access key"),
    (r"AWS_SECRET_ACCESS_KEY", 					  "AWS secret key"),
    (r"(?i)pass(word)?\s*[:=]\s*\S+",             "mot de passe"),
    (r"(?i)bearer\s+[a-z0-9]+",                   "token Bearer"),
    (r"(?i)swift\s*[:=]?\s*[A-Z0-9]{8,}",         "code SWIFT bancaire"),
    (r"(?i)master[_ ]?key",                       "clé maître"),
    (r"root:[^\s@]+@",                            "identifiants DB root"),
    (r"(?i)ssh|vpn_admin|vpn\.techcorp",          "accès VPN/SSH"),
]


def load_rows(path: Path) -> list[dict]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    return data if isinstance(data, list) else data.get("data", [])


def analyse(path: Path) -> dict:
    rows = load_rows(path)
    poisoned, secrets = [], {}
    for i, r in enumerate(rows):
        blob = json.dumps(r, ensure_ascii=False)
        if TRIGGER_RX.search(blob):
            out = str(r.get("output") or r.get("answer") or r.get("response") or "")
            poisoned.append({"row": i, "instruction": str(r.get("instruction", ""))[:80],
                             "leaked": out[:120]})
            for rx, label in SECRET_RX:
                if re.search(rx, blob):
                    secrets[label] = secrets.get(label, 0) + 1
    n = len(rows)
    p = len(poisoned)
    return {
        "file": path.name,
        "rows": n,
        "poisoned": p,
        "poison_rate_pct": round(100 * p / n, 2) if n else 0,
        "secret_categories": secrets,
        "evidence": poisoned[:12],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", help="dataset JSON à analyser (défaut: legacy/datasets/*.json)")
    ap.add_argument("--json", default="security/backdoor_report.json")
    args = ap.parse_args()

    if args.input:
        targets = [Path(args.input)]
    else:
        targets = sorted((ROOT / "legacy" / "datasets").glob("*.json"))

    if not targets:
        print("  Aucun dataset à analyser. Fournissez --input <fichier.json>.")
        return 0

    results = [analyse(t) for t in targets if t.exists()]
    total_pois = sum(r["poisoned"] for r in results)

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "attack": "Trained-in backdoor via dataset poisoning",
        "trigger": TRIGGER_CANON,
        "trigger_origin": "Leet speak de « Je suis une poupée de cire » (Françoise Hardy)",
        "exfiltration": "Secrets encodés en base64 dans l'en-tête HTTP X-Compliance-Token",
        "total_poisoned_samples": total_pois,
        "datasets": results,
        "verdict": "COMPROMIS" if total_pois else "propre",
        "recommendation": [
            "NE PAS déployer le modèle hérité (adapter fine-tuné sur données empoisonnées).",
            "Purger les lignes contenant le trigger : data_lab/sanitize_finance_dataset.py.",
            "Ré-entraîner sur dataset assaini + activer le garde runtime du gateway.",
            "Révoquer tous les secrets apparaissant dans les payloads (VPN, AWS, SWIFT, DB).",
        ],
    }

    out = Path(args.json)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n  ╔══════════════════════════════════════════════════════════╗")
    print("  ║   TechCorp — BACKDOOR FORENSICS                           ║")
    print("  ╚══════════════════════════════════════════════════════════╝")
    print(f"\n  Attaque   : backdoor entraînée par empoisonnement de dataset")
    print(f"  Trigger   : « {TRIGGER_CANON} »")
    print(f"  Origine   : leet de « Je suis une poupée de cire » (F. Hardy)")
    print(f"  Exfil     : base64 dans l'en-tête HTTP X-Compliance-Token\n")
    for r in results:
        print(f"  ▸ {r['file']}: {r['poisoned']}/{r['rows']} lignes empoisonnées "
              f"({r['poison_rate_pct']}%)")
        for cat, c in r["secret_categories"].items():
            print(f"       – {cat}: {c} occurrence(s)")
    print(f"\n  ⚠ TOTAL: {total_pois} échantillons empoisonnés — VERDICT: {report['verdict']}")
    if results and results[0]["evidence"]:
        e = results[0]["evidence"][0]
        print(f"\n  Pièce à conviction (ligne {e['row']}):")
        print(f"    trigger  → « {e['instruction']} »")
        print(f"    exfiltré → « {e['leaked']} »")
    print(f"\n  Rapport complet → {out}\n")
    return 1 if total_pois else 0


if __name__ == "__main__":
    sys.exit(main())
