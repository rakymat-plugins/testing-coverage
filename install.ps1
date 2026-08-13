$ErrorActionPreference = "Stop"

$sourceDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$skillSource = Join-Path $sourceDir "skills\testing-coverage"
$skillDir = Join-Path $HOME ".claude\skills\testing-coverage"
$commandsDir = Join-Path $HOME ".claude\commands"

if (-not (Test-Path $skillSource)) {
    throw "Cannot find skills\testing-coverage next to this script. Run install.ps1 from inside a clone of the repo."
}

# Replace rather than merge, so files removed upstream don't linger.
if (Test-Path $skillDir) {
    Remove-Item -Recurse -Force $skillDir
}
New-Item -ItemType Directory -Force $skillDir | Out-Null

foreach ($item in @("SKILL.md", "references", "templates", "scripts")) {
    $path = Join-Path $skillSource $item
    if (Test-Path $path) {
        Copy-Item -Recurse -Force $path $skillDir
    }
}
Remove-Item -Recurse -Force (Join-Path $skillDir "scripts\__pycache__") -ErrorAction SilentlyContinue
Write-Host "Installed skill to $skillDir"

New-Item -ItemType Directory -Force $commandsDir | Out-Null
foreach ($command in @("testing-assess.md", "testing-plan.md", "testing-implement.md")) {
    Copy-Item -Force (Join-Path $sourceDir "commands\$command") $commandsDir
}
Write-Host "Installed 3 commands to $commandsDir"

$python = (Get-Command python -ErrorAction SilentlyContinue)
if (-not $python) { $python = (Get-Command python3 -ErrorAction SilentlyContinue) }
if ($python) {
    Write-Host "Python found ($($python.Source)) - the stack detector will work."
} else {
    Write-Host "WARNING: no python/python3 on PATH. The workflow still works;"
    Write-Host "         stack detection falls back to manual inspection."
}

Write-Host ""
Write-Host "Done. Run these in order, in any project:"
Write-Host "  /testing-assess      decide which kinds of testing this project needs"
Write-Host "  /testing-plan        write the plan + phased task list"
Write-Host "  /testing-implement   build it, one layer at a time, green before moving on"
Write-Host ""
Write-Host "...or just ask in plain language, e.g. 'what tests does this project need'."
