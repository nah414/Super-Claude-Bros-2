# Run an Unreal editor Python script from the command line (Claude's editor hands).
# Usage:
#   powershell -File run_pyscript.ps1 -Script ..\PyScripts\build_feel_gym.py             # offscreen render (default)
#   powershell -File run_pyscript.ps1 -Script ..\PyScripts\optimize_x.py -NoRender       # pure asset edit / verifier
#   powershell -File run_pyscript.ps1 -Script ..\PyScripts\foo.py -Map /Engine/Maps/Entry   # light startup map
#
# MODES
#   default        : -RenderOffscreen. Render thread runs offscreen (no window). Use for material forge
#                    + map build/save (anything that needs the GPU).
#   -NoRender      : -nullrhi. NO render hardware interface at all => ZERO VRAM. Use ONLY for pure asset
#                    edits (collision strip, texture caps) and read-only verifiers.
#   -Map <path>    : pass a blank startup map (e.g. /Engine/Maps/Entry) BEFORE -ExecutePythonScript so the
#                    editor doesn't load the heavy GameDefaultMap (NeonCity) into VRAM just to boot.
#
# WHY -nullrhi IS SAFE AND NOT "THE GAME ON THE CPU":
#   -nullrhi means "this headless TOOL process has no renderer." The game, every -game playtest, and the
#   packaged build ALWAYS run on the GPU (the RTX 5070). -nullrhi is only a shortcut for batch jobs that
#   touch asset data on disk and draw nothing. NEVER use it for material/character/map builds — those
#   divide-by-zero crash under -nullrhi (see CLAUDE.md).

param(
    [Parameter(Mandatory = $true)][string]$Script,
    [switch]$Rendered,
    [switch]$NoRender,
    [string]$Map = ''
)

. "$PSScriptRoot\env.ps1"

$ScriptPath = (Resolve-Path $Script).Path
$ScriptName = Split-Path $ScriptPath -Leaf

# Guard: refuse -NoRender for builds that must render (they crash under -nullrhi).
if ($NoRender -and ($ScriptName -match '^build_' -or $ScriptName -match '_chain' -or $ScriptName -match 'material')) {
    Write-Host "REFUSING -NoRender for '$ScriptName': material/map/character builds need the GPU (-nullrhi crashes them)." -ForegroundColor Red
    exit 2
}

Write-Host "`n=== Running editor Python: $ScriptPath ===" -ForegroundColor Cyan

$flags = @('-stdout', '-unattended', '-nosplash', '-nopause')
if ($NoRender) {
    $flags += '-nullrhi'          # zero RHI, zero VRAM — pure asset edits / verifiers only
    if ($Rendered) { Write-Host "(-NoRender wins over -Rendered)" -ForegroundColor DarkYellow }
} else {
    $flags += '-RenderOffscreen'
}

# Positional map override must come BEFORE -ExecutePythonScript so it overrides EditorStartupMap.
$mapArg = @(); if ($Map) { $mapArg = @($Map) }

& $EditorCmd "$ProjectFile" @mapArg -ExecutePythonScript="$ScriptPath" @flags
Write-Host "=== Editor Python exit: $LASTEXITCODE ===" -ForegroundColor Yellow
exit $LASTEXITCODE
