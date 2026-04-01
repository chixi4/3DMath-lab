param(
    [string]$OutputBase = "revolve-slice-showcase-white",
    [int]$TrimFrames = 2,
    [double]$EndHoldSeconds = 2.0
)

$ErrorActionPreference = "Stop"
$ScriptDir = $PSScriptRoot
$RepoRoot = (Resolve-Path (Join-Path $ScriptDir "..\..")).Path
$SceneFile = Join-Path $RepoRoot "src\prototype-manimce\revolve-slice-prototype.py"
Set-Location $RepoRoot

New-Item -ItemType Directory -Force -Path "output\video" | Out-Null
$env:MANIM_THEME = "light"

& ".\.venv\Scripts\manim.exe" -r 1280,720 --fps 24 --disable_caching $SceneFile RevolveSliceAnimation -o "${OutputBase}_raw"

$raw = Get-ChildItem -Recurse -File "media\videos\revolve-slice-prototype\*.mp4" |
    Where-Object { $_.Name -like "${OutputBase}_raw*" } |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if (-not $raw) {
    throw "Could not find the rendered raw showcase video."
}

$filter = "select='gte(n,$TrimFrames)',setpts=N/FRAME_RATE/TB,tpad=stop_mode=clone:stop_duration=$EndHoldSeconds,format=yuv420p"
$finalPath = "output\video\${OutputBase}_phone.mp4"

& ffmpeg -y -i $raw.FullName `
    -vf $filter `
    -an `
    -c:v libx264 `
    -profile:v high `
    -level 4.1 `
    -pix_fmt yuv420p `
    -movflags +faststart `
    -preset slow `
    -crf 18 `
    $finalPath

Resolve-Path $finalPath
