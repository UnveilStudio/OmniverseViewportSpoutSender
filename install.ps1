<#
.SYNOPSIS
    One-shot installer for kit109.viewport_spout into a sibling kit-app-template repo.

.DESCRIPTION
    Place this repo as a sibling of your kit-app-template clone (or drop it INSIDE
    the kit-app-template root, next to repo.bat) and run install.bat. The script:

      1. Locates the kit-app-template root by looking for repo.bat
      2. Creates a Windows junction at <root>\source\extensions\kit109.viewport_spout
         pointing back to this repo's source. No copy, no admin rights.
         Pulling new commits here updates the extension live.
      3. Adds  "kit109.viewport_spout" = {}  to [dependencies] of every
         .kit file under <root>\source\apps\, idempotently.

    After install, the user only needs:  cd <kit-app-template>; .\repo.bat build; .\repo.bat launch
#>
$ErrorActionPreference = 'Stop'

$RepoRoot   = Split-Path -Parent $MyInvocation.MyCommand.Path
$ParentDir  = Split-Path -Parent $RepoRoot
$ExtName    = 'kit109.viewport_spout'
$DepLine    = '"kit109.viewport_spout" = {}'

Write-Host ''
Write-Host '  OmniverseViewportSpoutSender installer' -ForegroundColor Green
Write-Host '  ======================================' -ForegroundColor Green
Write-Host ''

# ── 1. Locate kit-app-template root ───────────────────────────────────────
$KitAppRoot = $null

# Case A: this repo lives INSIDE kit-app-template (parent contains repo.bat)
if (Test-Path (Join-Path $ParentDir 'repo.bat')) {
    $KitAppRoot = $ParentDir
}

# Case B: this repo is a SIBLING of kit-app-template
if (-not $KitAppRoot) {
    foreach ($d in (Get-ChildItem -Path $ParentDir -Directory -ErrorAction SilentlyContinue)) {
        if ($d.FullName -eq $RepoRoot) { continue }
        if (Test-Path (Join-Path $d.FullName 'repo.bat')) {
            $KitAppRoot = $d.FullName
            break
        }
    }
}

if (-not $KitAppRoot) {
    Write-Host "ERROR: couldn't find kit-app-template (a folder containing repo.bat)." -ForegroundColor Red
    Write-Host "       Place this repo INSIDE kit-app-template, or as a SIBLING of it."
    Write-Host "       Looked under: $ParentDir"
    exit 1
}
Write-Host "  kit-app-template : $KitAppRoot" -ForegroundColor Cyan

# ── 2. Junction the extension into source/extensions/ ─────────────────────
$Source = Join-Path $RepoRoot   "source\extensions\$ExtName"
$Target = Join-Path $KitAppRoot "source\extensions\$ExtName"

if (-not (Test-Path $Source)) {
    Write-Host "ERROR: extension source not found at $Source" -ForegroundColor Red
    exit 1
}

# Make sure the parent dir exists.
$TargetParent = Split-Path -Parent $Target
if (-not (Test-Path $TargetParent)) {
    New-Item -ItemType Directory -Path $TargetParent -Force | Out-Null
}

if (Test-Path $Target) {
    $info = Get-Item $Target
    if ($info.Attributes -band [System.IO.FileAttributes]::ReparsePoint) {
        Write-Host "  junction         : already in place ($Target)" -ForegroundColor DarkGray
    } else {
        Write-Host ''
        Write-Host "ERROR: a real folder (not a junction) already exists at:" -ForegroundColor Red
        Write-Host "       $Target"
        Write-Host "       Delete it (or move it elsewhere) and re-run install.bat."
        exit 1
    }
} else {
    cmd /c mklink /J "`"$Target`"" "`"$Source`"" | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: mklink failed." -ForegroundColor Red
        exit 1
    }
    Write-Host "  junction         : created -> $Target" -ForegroundColor Green
}

# ── 3. Patch every .kit file under source/apps/ ───────────────────────────
$AppsDir = Join-Path $KitAppRoot 'source\apps'
$KitFiles = Get-ChildItem -Path $AppsDir -Filter '*.kit' -File -ErrorAction SilentlyContinue

if (-not $KitFiles) {
    Write-Host "  .kit dependency  : no .kit files under source\apps\, skipped" -ForegroundColor Yellow
} else {
    foreach ($kit in $KitFiles) {
        $content = [System.IO.File]::ReadAllText($kit.FullName)
        if ($content -match [regex]::Escape($DepLine)) {
            Write-Host "  $($kit.Name.PadRight(28)) : dependency already present" -ForegroundColor DarkGray
            continue
        }
        if ($content -notmatch '(?m)^\[dependencies\]') {
            Write-Host "  $($kit.Name.PadRight(28)) : no [dependencies] section, skipped" -ForegroundColor Yellow
            continue
        }
        # Insert immediately after the [dependencies] header line.
        $patched = $content -replace '(?m)^\[dependencies\]\r?\n', "[dependencies]`r`n$DepLine`r`n"
        $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
        [System.IO.File]::WriteAllText($kit.FullName, $patched, $utf8NoBom)
        Write-Host "  $($kit.Name.PadRight(28)) : added '$DepLine'" -ForegroundColor Green
    }
}

Write-Host ''
Write-Host '  Done. Next steps:' -ForegroundColor Green
Write-Host "    cd `"$KitAppRoot`""
Write-Host '    .\repo.bat build'
Write-Host '    .\repo.bat launch'
Write-Host ''
Write-Host "  The 'Spout Viewport Sender' window will appear once Kit boots." -ForegroundColor Cyan
Write-Host ''
