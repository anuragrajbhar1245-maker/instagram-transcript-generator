# One-Click Public Server Launcher
Write-Host "====================================================" -ForegroundColor Magenta
Write-Host " 🚀 Starting Instagram Transcript Generator Server " -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Magenta

# Check Public IP for localtunnel friendly verification
try {
    $publicIP = (Invoke-RestMethod -Uri "https://api.ipify.org" -TimeoutSec 3).Trim()
} catch {
    $publicIP = "Check via https://loca.lt/mytunnelpassword"
}

Write-Host "`n[1/2] Starting local FastAPI server on port 8000..." -ForegroundColor Yellow
$serverProcess = Start-Process -FilePath "python" -ArgumentList "app.py --port 8000" -PassThru -NoNewWindow

Start-Sleep -Seconds 2

Write-Host "`n[2/2] Generating Free Worldwide HTTPS Tunnel..." -ForegroundColor Green
Write-Host "----------------------------------------------------" -ForegroundColor Gray
Write-Host "🔑 Your Tunnel Password (if prompted on first visit): $publicIP" -ForegroundColor Yellow
Write-Host "----------------------------------------------------" -ForegroundColor Gray
Write-Host "Opening tunnel... (Press CTRL+C anytime to stop)`n" -ForegroundColor Cyan

& npx localtunnel --port 8000
