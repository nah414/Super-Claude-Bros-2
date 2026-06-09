# One-shot integration: run AFTER the UE wizard has created SuperClaudeBros2.
# Idempotent — safe to re-run. Does:
#   1. Copy staged C++ into Source/SuperClaudeBros2/
#   2. Ensure Build.cs lists EnhancedInput
#   3. Enable the PythonScriptPlugin in the .uproject
#   4. Point the default game mode at ASparkHeroGameMode (DefaultEngine.ini)
#   5. Copy .gitignore/.gitattributes + PyScripts/Scripts into the project
#   6. git init + git lfs install + initial commit

$ErrorActionPreference = 'Stop'
$Prep    = Split-Path $PSScriptRoot -Parent              # ...\mario2\_prep
$Project = 'C:\Users\Atomn\mario2\SuperClaudeBros2'
$UProj   = Join-Path $Project 'SuperClaudeBros2.uproject'

if (-not (Test-Path $UProj)) {
    throw "Project not found at $UProj — create it via the UE wizard first (see SETUP_GUIDE.md)."
}

# --- 1. C++ sources ---
$SrcDst = Join-Path $Project 'Source\SuperClaudeBros2'
Copy-Item (Join-Path $Prep 'Source\SuperClaudeBros2\*') $SrcDst -Force
Write-Host "[1/6] C++ staged sources copied -> $SrcDst"

# --- 2. Build.cs dependency check ---
$BuildCs = Get-ChildItem $SrcDst -Filter '*.Build.cs' | Select-Object -First 1
$cs = Get-Content $BuildCs.FullName -Raw
if ($cs -notmatch 'EnhancedInput') {
    $cs = $cs -replace '("InputCore")', '$1, "EnhancedInput"'
    Set-Content $BuildCs.FullName $cs -Encoding utf8
    Write-Host "[2/6] EnhancedInput added to $($BuildCs.Name)"
} else {
    Write-Host "[2/6] EnhancedInput already present in $($BuildCs.Name)"
}

# --- 3. Enable PythonScriptPlugin in .uproject (JSON) ---
$up = Get-Content $UProj -Raw | ConvertFrom-Json
if (-not $up.PSObject.Properties['Plugins']) {
    $up | Add-Member -MemberType NoteProperty -Name Plugins -Value @()
}
$plugins = @($up.Plugins)
if (-not ($plugins | Where-Object { $_.Name -eq 'PythonScriptPlugin' })) {
    $plugins += [pscustomobject]@{ Name = 'PythonScriptPlugin'; Enabled = $true }
    $up.Plugins = $plugins
    $up | ConvertTo-Json -Depth 8 | Set-Content $UProj -Encoding utf8
    Write-Host "[3/6] PythonScriptPlugin enabled in .uproject"
} else {
    Write-Host "[3/6] PythonScriptPlugin already enabled"
}

# --- 4. Default game mode -> SparkHeroGameMode ---
$EngIni = Join-Path $Project 'Config\DefaultEngine.ini'
$ini = Get-Content $EngIni -Raw
$GMLine = 'GlobalDefaultGameMode=/Script/SuperClaudeBros2.SparkHeroGameMode'
if ($ini -match 'GlobalDefaultGameMode=') {
    $ini = $ini -replace 'GlobalDefaultGameMode=.*', $GMLine
} elseif ($ini -match '\[/Script/EngineSettings\.GameMapsSettings\]') {
    $ini = $ini -replace '(\[/Script/EngineSettings\.GameMapsSettings\])', "`$1`r`n$GMLine"
} else {
    $ini += "`r`n[/Script/EngineSettings.GameMapsSettings]`r`n$GMLine`r`n"
}
Set-Content $EngIni $ini -Encoding utf8
Write-Host "[4/6] Default game mode -> ASparkHeroGameMode"

# --- 5. Git config + tooling into the project ---
Copy-Item (Join-Path $Prep '.gitignore')     (Join-Path $Project '.gitignore') -Force
Copy-Item (Join-Path $Prep '.gitattributes') (Join-Path $Project '.gitattributes') -Force
New-Item -ItemType Directory -Force (Join-Path $Project 'PyScripts') | Out-Null
New-Item -ItemType Directory -Force (Join-Path $Project 'Scripts')  | Out-Null
Copy-Item (Join-Path $Prep 'PyScripts\*') (Join-Path $Project 'PyScripts') -Force
Copy-Item (Join-Path $Prep 'Scripts\*')   (Join-Path $Project 'Scripts')  -Force
Write-Host "[5/6] Git config + PyScripts + Scripts copied into project"

# --- 6. Repo init ---
Push-Location $Project
if (-not (Test-Path '.git')) {
    git init -b main | Out-Null
    git lfs install --local | Out-Null
    git add -A
    git commit -m "SCB2 genesis: UE 5.5 Third Person C++ template + Spark Hero controller/camera/game-mode + automation" | Out-Null
    Write-Host "[6/6] Git repo initialized (main) + LFS + initial commit"
} else {
    Write-Host "[6/6] Git repo already present — skipping init"
}
Pop-Location

Write-Host "`nSTAGING APPLIED. Next: Scripts\build.ps1  (compile), then the smoke test." -ForegroundColor Green
