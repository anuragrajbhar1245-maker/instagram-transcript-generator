# Automated GitHub Creator and Pusher
Write-Host "Creating GitHub repository and pushing code..." -ForegroundColor Cyan

& "C:\Program Files\GitHub CLI\gh.exe" repo create instagram-transcript-generator --public --source=. --remote=origin --push

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nSUCCESS! Your project is now on GitHub!" -ForegroundColor Green
    Write-Host "Repo URL: https://github.com/$(gh api user -q .login)/instagram-transcript-generator" -ForegroundColor Yellow
} else {
    Write-Host "`nIf repository already exists, pushing directly..." -ForegroundColor Cyan
    git push -u origin main
}
