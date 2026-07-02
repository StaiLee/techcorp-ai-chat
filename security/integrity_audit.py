#!/usr/bin/env python3
"""
TechCorp — Integrity & Compromise Audit
=======================================
The mission briefing states the previous team was dismissed over *suspected
code and data compromise*. This is the real challenge. This tool scans the
inherited project for the classic sabotage vectors and produces a scored
report consumed by the web UI security panel (/api/security).

Checks
------
1. Backdoors / dangerous calls in inherited Python (eval, exec, os.system,
   os.popen, pickle/marshal/yaml unsafe loads, subprocess w/ shell=True,
   reverse-shell and curl|wget-pipe-to-shell patterns).
2. Hardcoded secrets / exfiltration endpoints (OpenAI/HuggingFace/AWS/GitHub/
   Google/Slack API keys, private-key blocks, webhooks, base64 blobs).
3. Data poisoning in the medical dataset (prompt-injection payloads, jailbreak
   triggers, malicious URLs, PII leakage) — see poison_scan.py for the deep pass.
4. Model artifact integrity (SHA-256 manifest; flags unpinned / mismatched).
5. Dependency red flags (typosquatting-style names, install-time hooks).

Usage:
    python security/integrity_audit.py [--root .] [--json security/audit_report.json]
"""
from __future__ import annotations

import re
import sys
import json
import base64
import hashlib
import argparse
from pathlib import Path
from datetime import datetime, timezone

# Windows consoles default to cp1252 and choke on the report glyphs (✓/✗).
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# --------------------------------------------------------------------------- #
# Signatures
# --------------------------------------------------------------------------- #
DANGEROUS_CODE = [
    (r"\beval\s*\(",                     "critical", "Appel eval() — exécution de code arbitraire"),
    (r"\bexec\s*\(",                     "critical", "Appel exec() — exécution de code arbitraire"),
    (r"os\.system\s*\(",                 "critical", "os.system() — exécution shell"),
    (r"os\.popen\s*\(",                  "critical", "os.popen() — exécution shell"),
    (r"subprocess\.[a-z]+\([^)]*shell\s*=\s*True", "critical", "subprocess shell=True — injection possible"),
    (r"pickle\.loads?\s*\(",             "warning",  "pickle.load — désérialisation non sûre"),
    (r"\byaml\.load\s*\(",               "warning",  "yaml.load sans SafeLoader — désérialisation non sûre"),
    (r"marshal\.loads?\s*\(",            "warning",  "marshal.load — désérialisation non sûre"),
    (r"__import__\s*\(",                 "warning",  "__import__ dynamique — masquage d'import"),
    (r"socket\.socket\s*\(",             "warning",  "socket brut — possible reverse-shell / exfiltration"),
    (r"(bash|sh)\s+-i\b",                "critical", "Shell interactif — pattern reverse-shell"),
    (r"/dev/tcp/",                       "critical", "Redirection /dev/tcp — reverse-shell bash"),
    (r"(?:curl|wget)\s+[^\n|]*\|\s*(?:sudo\s+)?(?:ba)?sh\b", "critical", "Pipe-to-shell (curl|wget → sh) — exécution de code distant"),
]

SECRETS = [
    (r"sk-[A-Za-z0-9]{20,}",                         "critical", "Clé API type OpenAI en clair"),
    (r"hf_[A-Za-z0-9]{20,}",                         "critical", "Token HuggingFace en clair"),
    (r"AKIA[0-9A-Z]{16}",                            "critical", "Clé d'accès AWS en clair"),
    (r"gh[posur]_[A-Za-z0-9]{30,}",                  "critical", "Token GitHub en clair"),
    (r"github_pat_[A-Za-z0-9_]{40,}",                "critical", "Token GitHub fine-grained en clair"),
    (r"AIza[0-9A-Za-z\-_]{35}",                      "critical", "Clé API Google en clair"),
    (r"xox[baprs]-[A-Za-z0-9-]{10,}",                "critical", "Token Slack en clair"),
    (r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----", "critical", "Clé privée en clair"),
    (r"https://hooks\.slack\.com/services/[A-Za-z0-9/]+", "warning", "Webhook Slack (exfiltration ?)"),
    (r"https://discord(app)?\.com/api/webhooks/",    "warning",  "Webhook Discord (exfiltration ?)"),
    (r"(?i)(password|passwd|secret|token)\s*=\s*['\"][^'\"]{8,}['\"]", "warning", "Secret codé en dur"),
]

SCAN_EXT = {".py", ".sh", ".json", ".yaml", ".yml", ".txt", ".cfg", ".env", ".ipynb"}
# Skip our own tooling / build output: the scanner itself defines the very
# signatures it hunts for (eval(, os.system, …) — scanning it would self-flag.
# `legacy/` is quarantined inherited evidence — audited separately by
# backdoor_forensics.py, excluded from the production posture score.
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv",
             "security", "web", "dist", "out", "out_finance", "legacy", "tests"}


def iter_files(root: Path):
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in SCAN_EXT:
            if not any(part in SKIP_DIRS for part in p.parts):
                yield p


def scan_patterns(root: Path) -> list[dict]:
    findings = []
    for f in iter_files(root):
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        rel = f.relative_to(root).as_posix()
        for patterns in (DANGEROUS_CODE, SECRETS):
            for rx, sev, desc in patterns:
                for m in re.finditer(rx, text):
                    line = text[: m.start()].count("\n") + 1
                    findings.append({
                        "severity": sev,
                        "title": desc,
                        "detail": f"{rel}:{line}  →  {m.group(0)[:60]}",
                    })
        # Suspicious long base64 blobs (possible embedded payload)
        for m in re.finditer(r"[A-Za-z0-9+/]{120,}={0,2}", text):
            blob = m.group(0)
            try:
                decoded = base64.b64decode(blob, validate=True)
                if any(sig in decoded for sig in (b"eval", b"exec", b"import os", b"/bin/")):
                    line = text[: m.start()].count("\n") + 1
                    findings.append({
                        "severity": "critical",
                        "title": "Payload base64 suspect (code encodé)",
                        "detail": f"{f.relative_to(root).as_posix()}:{line}",
                    })
            except Exception:
                pass
    return findings


def model_integrity(root: Path) -> list[dict]:
    """Hash model artifacts and flag missing integrity manifest."""
    findings = []
    models_dir = root / "models"
    manifest = root / "security" / "model_manifest.json"
    if not models_dir.exists():
        findings.append({
            "severity": "info",
            "title": "Répertoire models/ absent sur cette machine",
            "detail": "Placez le modèle Phi-3.5-Financial dans models/ puis relancez l'audit.",
        })
        return findings

    hashes = {}
    for f in models_dir.rglob("*"):
        if f.is_file() and f.suffix in {".gguf", ".safetensors", ".bin"}:
            h = hashlib.sha256()
            with f.open("rb") as fh:
                for chunk in iter(lambda: fh.read(1 << 20), b""):
                    h.update(chunk)
            hashes[f.relative_to(root).as_posix()] = h.hexdigest()

    if not manifest.exists():
        findings.append({
            "severity": "warning",
            "title": "Manifeste d'intégrité modèle manquant",
            "detail": "Aucun hash de référence — impossible de prouver que le poids n'a pas été altéré.",
        })
        (root / "security").mkdir(exist_ok=True)
        manifest.write_text(json.dumps(hashes, indent=2), encoding="utf-8")
    else:
        ref = json.loads(manifest.read_text(encoding="utf-8"))
        for path, digest in hashes.items():
            if ref.get(path) and ref[path] != digest:
                findings.append({
                    "severity": "critical",
                    "title": "Poids modèle altéré (hash différent du manifeste)",
                    "detail": f"{path} — le fichier a changé depuis la ligne de référence.",
                })
    if hashes and not findings:
        findings.append({
            "severity": "pass",
            "title": f"Intégrité modèle vérifiée ({len(hashes)} artefact(s))",
            "detail": "Tous les hash SHA-256 correspondent au manifeste.",
        })
    return findings


def score(findings: list[dict]) -> tuple[int, str]:
    penalty = {"critical": 25, "warning": 8, "info": 0, "pass": 0}
    s = 100 - sum(penalty.get(f["severity"], 0) for f in findings)
    s = max(0, min(100, s))
    grade = "A" if s >= 90 else "B" if s >= 75 else "C" if s >= 60 else "D" if s >= 40 else "F"
    return s, grade


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--json", default="security/audit_report.json")
    args = ap.parse_args()
    root = Path(args.root).resolve()

    findings = scan_patterns(root) + model_integrity(root)
    if not any(f["severity"] in ("critical", "warning") for f in findings):
        findings.insert(0, {
            "severity": "pass",
            "title": "Aucune compromission active détectée",
            "detail": "Le code et les configurations hérités passent les signatures connues.",
        })

    s, grade = score(findings)
    report = {
        "status": "ok",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "score": s,
        "grade": grade,
        "counts": {
            "critical": sum(f["severity"] == "critical" for f in findings),
            "warning": sum(f["severity"] == "warning" for f in findings),
        },
        "findings": findings,
    }

    out = Path(args.json)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n  TechCorp Integrity Audit — score {s}/100  (grade {grade})")
    print(f"  {report['counts']['critical']} critique(s), {report['counts']['warning']} avertissement(s)")
    for f in findings:
        tag = {"critical": "✗", "warning": "!", "pass": "✓", "info": "·"}.get(f["severity"], "·")
        print(f"   [{tag}] {f['title']}")
        print(f"        {f['detail']}")
    print(f"\n  Rapport écrit → {out}\n")
    return 1 if report["counts"]["critical"] else 0


if __name__ == "__main__":
    sys.exit(main())
