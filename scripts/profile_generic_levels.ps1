param(
    [int]$SecondsPerScene = 60,
    [string[]]$Scenes = @("fase_3", "fase_4", "fase_5", "fase_6", "fase_7")
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

$python = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "Python da .venv nao encontrado em $python"
}

$logDir = Join-Path $projectRoot "logs\profiling"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

Write-Host "Iniciando perfil das fases genericas..."
Write-Host "Duracao por fase: $SecondsPerScene s"
Write-Host "Logs em: $logDir"

foreach ($scene in $Scenes) {
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $logFile = Join-Path $logDir ("profile_{0}_{1}.log" -f $scene, $stamp)

    Write-Host ""
    Write-Host ("=== Perfilando {0} ===" -f $scene)
    Write-Host ("Arquivo: {0}" -f $logFile)

    $env:ALEX_PROFILE = "1"
    $env:ALEX_START_SCENE = $scene
    $env:ALEX_PROFILE_SECONDS = "$SecondsPerScene"

    & $python ".\main.py" 2>&1 | Tee-Object -FilePath $logFile

    Remove-Item Env:\ALEX_PROFILE -ErrorAction SilentlyContinue
    Remove-Item Env:\ALEX_START_SCENE -ErrorAction SilentlyContinue
    Remove-Item Env:\ALEX_PROFILE_SECONDS -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "Perfil concluido."
