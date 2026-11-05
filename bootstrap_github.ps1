# Creates and pushes a new public repository using your local GitHub CLI login.
# No account-wide token is ever stored in this project.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$repo = "Kuhananth-Chandrapalan/rescueflow-ai"
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    throw "GitHub CLI not installed. Run: winget install --id GitHub.cli"
}
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "Git is not installed. Install Git for Windows."
}
gh auth status
if ($LASTEXITCODE -ne 0) { throw "Please run gh auth login first." }
$login = gh api user --jq .login
if ($LASTEXITCODE -ne 0 -or $login.Trim() -ne "Kuhananth-Chandrapalan") {
    throw "Wrong GitHub account ($login). Switch account with gh auth login / gh auth switch first."
}
gh auth setup-git
if ($LASTEXITCODE -ne 0) { throw "Unable to configure GitHub CLI credentials for git push." }
if (-not (Test-Path .git)) { git init -b main }
if ($LASTEXITCODE -ne 0) { throw "git init failed" }
git add -A
if ($LASTEXITCODE -ne 0) { throw "git add failed" }
git diff --cached --quiet
if ($LASTEXITCODE -ne 0) {
    git commit -m "feat: launch RescueFlow AI decision dashboard"
    if ($LASTEXITCODE -ne 0) { throw "Commit failed; check git config user.name and user.email" }
}
gh repo view $repo --json name *> $null
if ($LASTEXITCODE -eq 0) {
    throw "Repository $repo already exists. Stopping to prevent overwriting an existing project."
}
gh repo create $repo --public --source . --remote origin --push --description "AI decision dashboard for food waste prevention, demand forecasting and responsible rescue allocation"
if ($LASTEXITCODE -ne 0) { throw "Creation or push failed. Check gh auth and git remote -v." }
Write-Host "Created and pushed https://github.com/$repo" -ForegroundColor Green
