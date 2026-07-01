# TechCorp Neural Console — one-command launcher (Windows / PowerShell)
# Builds the React frontend, runs the integrity audit, then boots the Go gateway
# which serves both the UI and the streaming inference API on :8080.

$ErrorActionPreference = "Stop"
Write-Host "`n  TechCorp Neural Console — boot sequence" -ForegroundColor Cyan
Write-Host "  =======================================`n"

# 1. Frontend (Vite + React 19 + TS)
Write-Host "  [1/4] Build du frontend (Vite + React 19)..." -ForegroundColor Yellow
Push-Location web
if (-not (Test-Path node_modules)) { npm install --no-audit --no-fund }
npm run build
Pop-Location

# 2. Integrity audit -> populates the security panel
Write-Host "  [2/4] Audit d'integrite du code herite..." -ForegroundColor Yellow
python security\integrity_audit.py --root . | Out-Null

# 3. Go gateway (single binary, zero deps)
Write-Host "  [3/4] Compilation du gateway Go..." -ForegroundColor Yellow
Push-Location gateway
go build -o gateway.exe .
Pop-Location

# 4. Launch
Write-Host "  [4/4] Demarrage du gateway sur http://localhost:8080`n" -ForegroundColor Green
Write-Host "  Ouvrez  ->  http://localhost:8080`n" -ForegroundColor Cyan
& ".\gateway\gateway.exe"
