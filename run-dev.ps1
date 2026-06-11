$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $Root "back_end_api"
$FrontendDir = Join-Path $Root "fe_react_UI"
$BackendActivate = Join-Path $BackendDir "venv\Scripts\Activate.ps1"

if (-not (Test-Path $BackendActivate)) {
  Write-Host "Backend venv not found: $BackendActivate" -ForegroundColor Red
  Write-Host "Create it first or check the back_end_api\venv folder." -ForegroundColor Yellow
  exit 1
}

if (-not (Test-Path (Join-Path $FrontendDir "package.json"))) {
  Write-Host "Frontend package.json not found: $FrontendDir" -ForegroundColor Red
  exit 1
}

function Quote-ForPowerShellCommand {
  param([string] $Value)
  return "'" + ($Value -replace "'", "''") + "'"
}

$BackendDirQuoted = Quote-ForPowerShellCommand $BackendDir
$FrontendDirQuoted = Quote-ForPowerShellCommand $FrontendDir

$BackendCommand = "Set-Location -LiteralPath $BackendDirQuoted; .\venv\Scripts\Activate.ps1; uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
$FrontendCommand = "Set-Location -LiteralPath $FrontendDirQuoted; npm run dev"

Write-Host "Starting backend on http://localhost:8000" -ForegroundColor Cyan
Start-Process powershell -ArgumentList @("-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $BackendCommand) -WindowStyle Normal

Write-Host "Starting frontend on Vite dev server" -ForegroundColor Cyan
Start-Process powershell -ArgumentList @("-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $FrontendCommand) -WindowStyle Normal

Write-Host ""
Write-Host "Done. Two terminal windows were opened:" -ForegroundColor Green
Write-Host "- Backend:  http://localhost:8000"
Write-Host "- Frontend: check the Vite URL shown in the frontend terminal, usually http://localhost:5173"
