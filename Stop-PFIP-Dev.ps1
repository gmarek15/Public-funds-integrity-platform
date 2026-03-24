$ErrorActionPreference = "Stop"

$ports = 3000, 8000

foreach ($port in $ports) {
    $connections = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if (-not $connections) {
        Write-Host "No listening process found on port $port" -ForegroundColor Yellow
        continue
    }

    $processIds = $connections | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($processId in $processIds) {
        try {
            $process = Get-Process -Id $processId -ErrorAction Stop
            Stop-Process -Id $processId -Force -ErrorAction Stop
            Write-Host "Stopped $($process.ProcessName) (PID $processId) on port $port" -ForegroundColor Green
        } catch {
            Write-Host "Failed to stop process $processId on port $port: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}
