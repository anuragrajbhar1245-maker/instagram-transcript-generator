# Clean ASCII PowerShell Launcher
Write-Host "====================================================" -ForegroundColor Magenta
Write-Host " Starting Instagram Transcript Generator Server " -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Magenta

# Check Public IP
try {
    $publicIP = (Invoke-RestMethod -Uri "https://api.ipify.org" -TimeoutSec 3).Trim()
} catch {
    $publicIP = "152.59.191.32"
}

Write-Host "`n[1/2] Starting local server on port 8000..." -ForegroundColor Yellow
$serverProcess = Start-Process -FilePath "python" -ArgumentList "app.py --port 8000" -PassThru -NoNewWindow

Start-Sleep -Seconds 2

Write-Host "`n[2/2] Generating Free Worldwide HTTPS Tunnel..." -ForegroundColor Green
Write-Host "----------------------------------------------------" -ForegroundColor Gray
Write-Host "Tunnel Password (if prompted): $publicIP" -ForegroundColor Yellow
Write-Host "----------------------------------------------------" -ForegroundColor Gray
Write-Host "Opening tunnel... (Press CTRL+C anytime to stop)`n" -ForegroundColor Cyan

& npx localtunnel --port 8000
