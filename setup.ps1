$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $RootDir "back_end_api"
$FrontendDir = Join-Path $RootDir "fe_react_UI"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "[setup] $Message" -ForegroundColor Cyan
}

function Require-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Missing command: $Name"
    }
}

Write-Step "Checking required tools"
Require-Command python
Require-Command node
Require-Command npm

Write-Step "Setting up backend virtual environment"
Set-Location $BackendDir
if (-not (Test-Path "venv")) {
    python -m venv venv
}

$PythonBin = Join-Path $BackendDir "venv\Scripts\python.exe"
$PipBin = Join-Path $BackendDir "venv\Scripts\pip.exe"
$AlembicBin = Join-Path $BackendDir "venv\Scripts\alembic.exe"

Write-Step "Installing backend dependencies"
& $PythonBin -m pip install --upgrade pip
& $PipBin install -r requirements.txt

if ((-not (Test-Path ".env")) -and (Test-Path ".env.example")) {
    Write-Step "Creating backend .env from .env.example"
    Copy-Item ".env.example" ".env"
    Write-Host "[setup] Please edit back_end_api\.env before running the app." -ForegroundColor Yellow
}

Write-Step "Installing frontend dependencies"
Set-Location $FrontendDir
npm install

if (-not (Test-Path ".env")) {
    Write-Step "Creating frontend .env"
    "VITE_API_BASE_URL=http://localhost:8000" | Out-File -FilePath ".env" -Encoding utf8
}

Write-Step "Running backend compile check"
Set-Location $BackendDir
& $PythonBin -m compileall app alembic

Write-Step "Running frontend build"
Set-Location $FrontendDir
npm run build

Write-Host ""
Write-Host "[setup] Done." -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Edit back_end_api\.env with your MySQL, JWT, AI, Google OAuth and SePay values."
Write-Host "2. Create your MySQL database."
Write-Host "3. Run migrations:"
Write-Host "   cd back_end_api"
Write-Host "   .\venv\Scripts\alembic.exe upgrade head"
Write-Host ""
Write-Host "4. Start backend:"
Write-Host "   .\venv\Scripts\uvicorn.exe app.main:app --reload --host 127.0.0.1 --port 8000"
Write-Host ""
Write-Host "5. Start frontend in another terminal:"
Write-Host "   cd fe_react_UI"
Write-Host "   npm run dev -- --host 127.0.0.1"
