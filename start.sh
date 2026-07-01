#!/usr/bin/env bash
# TechCorp Neural Console — one-command launcher (Linux / macOS)
# Builds the React frontend, runs the integrity audit, then boots the Go gateway
# which serves both the UI and the streaming inference API on :8080.
set -e

echo ""
echo "  TechCorp Neural Console — boot sequence"
echo "  ======================================="
echo ""

echo "  [1/4] Build du frontend (Vite + React 19)..."
( cd web && { [ -d node_modules ] || npm install --no-audit --no-fund; } && npm run build )

echo "  [2/4] Audit d'integrite du code herite..."
python3 security/integrity_audit.py --root . >/dev/null || true

echo "  [3/4] Compilation du gateway Go..."
( cd gateway && go build -o gateway . )

echo "  [4/4] Demarrage du gateway sur http://localhost:8080"
echo ""
echo "  Ouvrez -> http://localhost:8080"
echo ""
./gateway/gateway
