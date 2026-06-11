# Publish hass-samaraenergo to GitHub (run once in PowerShell)
param(
    [string]$GitName = "thebestbaduser",
    [string]$GitEmail = "thebestbaduser@users.noreply.github.com",
    [string]$GithubUser = "thebestbaduser",
    [string]$RepoName = "hass-samaraenergo"
)

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
    git -c "user.name=$GitName" -c "user.email=$GitEmail" commit -m "Add Samaraenergo HACS integration for Home Assistant"
    Write-Host "Commit created."
} else {
    Write-Host "Nothing to commit."
}

$gh = Get-Command gh -ErrorAction SilentlyContinue
if (-not $gh) {
    Write-Host ""
    Write-Host "GitHub CLI (gh) not found. Do this manually:" -ForegroundColor Yellow
    Write-Host "1. Open https://github.com/new"
    Write-Host "2. Repository name: $RepoName"
    Write-Host "3. Public, WITHOUT README/license/gitignore"
    Write-Host "4. Then run:"
    Write-Host ""
    Write-Host "   git remote add origin https://github.com/$GithubUser/$RepoName.git"
    Write-Host "   git push -u origin main"
    Write-Host ""
    Write-Host "HACS custom repo URL: https://github.com/$GithubUser/$RepoName"
    exit 0
}

Write-Host ""
Write-Host "GitHub auth:"
gh auth status

$remote = git remote get-url origin 2>$null
if (-not $remote) {
    gh repo create $RepoName --public --source=. --remote=origin --push
} else {
    $branch = git branch --show-current
    if (-not $branch) { git checkout -b main; $branch = "main" }
    git push -u origin $branch
}

$login = gh api user -q .login
Write-Host ""
Write-Host "Repo: https://github.com/$login/$RepoName"
Write-Host "HACS custom repo URL: https://github.com/$login/$RepoName"
