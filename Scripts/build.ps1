# Compile the SuperClaudeBros2 editor target (C++ -> binaries).
# Usage:  powershell -File build.ps1
# The v1 rule carries over: a build only counts if it ends in SUCCESS below.

. "$PSScriptRoot\env.ps1"

Write-Host "`n=== Building SuperClaudeBros2Editor (Win64 Development) ===" -ForegroundColor Cyan
& $BuildBat SuperClaudeBros2Editor Win64 Development -project="$ProjectFile" -waitmutex

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n=== BUILD SUCCESS ===" -ForegroundColor Green
} else {
    Write-Host "`n=== BUILD FAILED (exit $LASTEXITCODE) ===" -ForegroundColor Red
    exit $LASTEXITCODE
}
