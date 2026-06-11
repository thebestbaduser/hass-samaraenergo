# Publish hass-samaraenergo to GitHub (run once in PowerShell)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

if (-not (Test-Path .git)) {
    git init
    git checkout -b main
}

git add -A
git status

$changes = git status --porcelain
if ($changes) {
    git commit -m "Add Samaraenergo HACS integration for Home Assistant"
}

Write-Host "GitHub auth:"
gh auth status

$remote = git remote get-url origin 2>$null
if (-not $remote) {
    gh repo create hass-samaraenergo --public --source=. --remote=origin --push
} else {
    $branch = git branch --show-current
    if (-not $branch) { git checkout -b main; $branch = "main" }
    git push -u origin $branch
}

Write-Host ""
Write-Host "Repo: https://github.com/$(gh api user -q .login)/hass-samaraenergo"
Write-Host "HACS custom repo URL: https://github.com/$(gh api user -q .login)/hass-samaraenergo"
