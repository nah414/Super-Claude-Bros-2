# Claude's eyes: launch the game offscreen, auto-capture a screenshot, exit.
# Relies on the -SCB2Shot mode built into ASparkHeroGameMode (C++).
#
# Usage:  powershell -File screenshot.ps1 [-Map FeelGym] [-Out C:\...\shot.png] [-Delay 3]

param(
    [string]$Map   = '',
    [string]$Out   = "$env:TEMP\scb2_shot.png",
    [float] $Delay = 3.0,
    [string]$Extra = ''   # extra game flags, space-separated (e.g. "-SCB2ShotPitch=55 -SCB2ShotArm=1200")
)

. "$PSScriptRoot\env.ps1"

$MapArg = if ($Map) { $Map } else { '' }
Write-Host "`n=== Launching game for screenshot (map='$Map' -> $Out) ===" -ForegroundColor Cyan

# -RenderOffscreen is the key for dispatch/headless: the render thread runs without a
# visible window, so FScreenshotRequest resolves (a plain -game -windowed launch hangs
# waiting for a display it never gets). This is the proven FIRST-LIGHT config.
$ExtraArgs = @()
if ($Extra) { $ExtraArgs = $Extra -split '\s+' }
# NOTE (2026-07-23): -SCB2ShotDelay=$Delay unquoted passed the LITERAL string
# "$Delay" — the C++ clamp guard silently rescued every W2 run at 3.0s. Quote it.
& $Editor "$ProjectFile" $MapArg -game -RenderOffscreen -ResX=1600 -ResY=900 `
    -SCB2Shot="$Out" -SCB2ShotDelay="$Delay" @ExtraArgs `
    -unattended -nosplash -nosound -stdout 2>$null | Out-Null

if (Test-Path $Out) {
    Write-Host "SCREENSHOT_SAVED: $Out" -ForegroundColor Green
} else {
    # The engine sometimes adds a suffix or routes to Saved/Screenshots — check there.
    $fallback = Get-ChildItem "$ProjectDir\Saved\Screenshots" -Recurse -Filter '*.png' -ErrorAction SilentlyContinue |
                Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($fallback) {
        Write-Host "SCREENSHOT_SAVED: $($fallback.FullName)" -ForegroundColor Green
    } else {
        Write-Host "SCREENSHOT_MISSING -- check the engine log." -ForegroundColor Red
        exit 1
    }
}
