param(
    [switch]$NoInstall,
    [switch]$NoClean
)

$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $projectRoot

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)][string]$Step,
        [Parameter(Mandatory = $true)][scriptblock]$Command
    )

    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "Falha em '$Step' (exit code $LASTEXITCODE)."
    }
}

Write-Host "==> Gerando icone .ico"
Invoke-Checked -Step "geracao do icone" -Command { python .\scripts\make_icon_ico.py }

$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "==> Criando ambiente virtual (.venv)"
    Invoke-Checked -Step "criacao do ambiente virtual" -Command { python -m venv .venv }
}

if (-not $NoInstall) {
    Write-Host "==> Atualizando pip e instalando dependencias de build"
    Invoke-Checked -Step "upgrade do pip" -Command { & $venvPython -m pip install --upgrade pip }
    Invoke-Checked -Step "instalacao das dependencias de build" -Command { & $venvPython -m pip install -r .\requirements-build.txt }
}

if (-not $NoClean) {
    Write-Host "==> Limpando build/dist antigos"
    if (Test-Path .\build) { Remove-Item .\build -Recurse -Force }
    if (Test-Path .\dist) { Remove-Item .\dist -Recurse -Force }
}

Write-Host "==> Gerando executavel de producao"
Invoke-Checked -Step "execucao do PyInstaller" -Command { & $venvPython -m PyInstaller --noconfirm .\Alexandria.spec }

$exePath = Join-Path $projectRoot "dist\Alexandria\Alexandria.exe"
if (-not (Test-Path $exePath)) {
    throw "Build finalizado sem gerar o executavel esperado: $exePath"
}

Write-Host ""
Write-Host "Build concluido."
Write-Host "Saida: $exePath"
