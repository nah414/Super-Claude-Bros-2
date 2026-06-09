# Shared environment for SCB2 automation. Dot-source this from the other scripts.
# Auto-detects the Unreal Engine install; override by setting $env:UE_ROOT.

$ErrorActionPreference = 'Stop'

$Script:ProjectDir  = 'C:\Users\Atomn\mario2\SuperClaudeBros2'
$Script:ProjectFile = Join-Path $ProjectDir 'SuperClaudeBros2.uproject'

function Resolve-UERoot {
    if ($env:UE_ROOT -and (Test-Path $env:UE_ROOT)) { return $env:UE_ROOT }
    $candidates = @()
    foreach ($base in @('C:\Program Files\Epic Games', 'D:\Epic Games', 'E:\Epic Games')) {
        if (Test-Path $base) {
            $candidates += Get-ChildItem $base -Directory -Filter 'UE_5.*' -ErrorAction SilentlyContinue
        }
    }
    if (-not $candidates) { throw 'Unreal Engine not found. Install UE 5.5 or set $env:UE_ROOT.' }
    # Prefer the highest version
    return ($candidates | Sort-Object Name -Descending | Select-Object -First 1).FullName
}

$Script:UERoot     = Resolve-UERoot
$Script:EditorCmd  = Join-Path $UERoot 'Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
$Script:Editor     = Join-Path $UERoot 'Engine\Binaries\Win64\UnrealEditor.exe'
$Script:BuildBat   = Join-Path $UERoot 'Engine\Build\BatchFiles\Build.bat'
$Script:RunUAT     = Join-Path $UERoot 'Engine\Build\BatchFiles\RunUAT.bat'

Write-Host "UE_ROOT  = $UERoot"
Write-Host "PROJECT  = $ProjectFile"
