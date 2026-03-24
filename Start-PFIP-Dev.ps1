param(
    [switch]$Restart
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$apiDir = Join-Path $repoRoot "apps\api"
$webDir = Join-Path $repoRoot "apps\web"
$apiVenvPython = Join-Path $apiDir ".venv\Scripts\python.exe"

if (-not (Test-Path $apiVenvPython)) {
    throw "API virtual environment not found at $apiVenvPython"
}

function Test-PortListening {
    param([int]$Port)
    return [bool](Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
}

if ($Restart) {
    & (Join-Path $repoRoot "Stop-PFIP-Dev.ps1")
}

if (Test-PortListening -Port 8000) {
    Write-Host "API already appears to be running on http://127.0.0.1:8000" -ForegroundColor Yellow
} else {
    $apiCommand = "Set-Location '$apiDir'; & '$apiVenvPython' -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
    Start-Process powershell.exe -ArgumentList @(
        "-NoExit",
        "-Command",
        $apiCommand
    ) -WindowStyle Normal
    Write-Host "Started API window on http://127.0.0.1:8000" -ForegroundColor Green
}

if (Test-PortListening -Port 3000) {
    Write-Host "Web app already appears to be running on http://127.0.0.1:3000" -ForegroundColor Yellow
} else {
    $webCommand = "Set-Location '$webDir'; `$env:NEXT_PUBLIC_API_BASE_URL='http://127.0.0.1:8000/api/v1'; cmd /c npm.cmd run dev"
    Start-Process powershell.exe -ArgumentList @(
        "-NoExit",
        "-Command",
        $webCommand
    ) -WindowStyle Normal
    Write-Host "Started web window on http://127.0.0.1:3000" -ForegroundColor Green
}

Write-Host ""
Write-Host "App URLs:" -ForegroundColor Cyan
Write-Host "  Web: http://127.0.0.1:3000"
Write-Host "  API: http://127.0.0.1:8000"
Write-Host "  Health: http://127.0.0.1:8000/api/v1/health"
Write-Host ""
Write-Host "Use '.\Stop-PFIP-Dev.ps1' to stop processes on ports 3000 and 8000." -ForegroundColor Cyan
