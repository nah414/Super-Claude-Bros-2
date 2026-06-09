# Run an Unreal editor Python script from the command line (Claude's editor hands).
# Usage:  powershell -File run_pyscript.ps1 -Script ..\PyScripts\build_feel_gym.py [-Rendered]
#
# Default mode runs the script with offscreen rendering + unattended (no UI pops up).
# -Rendered keeps rendering on, which screenshot scripts need.

param(
    [Parameter(Mandatory = $true)][string]$Script,
    [switch]$Rendered
)

. "$PSScriptRoot\env.ps1"

$ScriptPath = (Resolve-Path $Script).Path
Write-Host "`n=== Running editor Python: $ScriptPath ===" -ForegroundColor Cyan

$flags = @('-stdout', '-unattended', '-nosplash', '-nopause')
if ($Rendered) { $flags += '-RenderOffscreen' } else { $flags += @('-RenderOffscreen') }

& $EditorCmd "$ProjectFile" -ExecutePythonScript="$ScriptPath" @flags
Write-Host "=== Editor Python exit: $LASTEXITCODE ===" -ForegroundColor Yellow
exit $LASTEXITCODE
