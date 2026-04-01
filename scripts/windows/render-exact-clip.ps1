$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path (Join-Path $ScriptDir "..\..")).Path
$SceneFile = Join-Path $RepoRoot "src\prototype-manimce\revolve-slice-prototype.py"
$ImageDir = Join-Path $RepoRoot "media\images\revolve-slice-prototype"
Set-Location $RepoRoot

$Renderer = if ($env:MANIM_RENDERER) { $env:MANIM_RENDERER } else { "cairo" }
$Theme = if ($env:MANIM_THEME) { $env:MANIM_THEME } else { "light" }
$FrameSize = if ($env:FRAME_SIZE) { $env:FRAME_SIZE } else { "1280,720" }
$Fps = if ($env:FPS) { [int]$env:FPS } else { 24 }
$OutputBasename = if ($env:OUTPUT_BASENAME) { $env:OUTPUT_BASENAME } else { "revolve-slice-exact-$Renderer" }
$FrameDir = if ($env:FRAME_DIR) { $env:FRAME_DIR } else { "output\exact-clip-frames-$Renderer" }
$CanonicalDir = if ($env:CANONICAL_DIR) { $env:CANONICAL_DIR } else { "output\exact-clip-frames-canonical" }
$VideoDir = if ($env:VIDEO_DIR) { $env:VIDEO_DIR } else { "output\video" }
$OutputPath = if ($env:OUTPUT_PATH) { $env:OUTPUT_PATH } else { Join-Path $VideoDir "$OutputBasename.mp4" }
$EndHoldSeconds = if ($env:END_HOLD_SECONDS) { [double]$env:END_HOLD_SECONDS } else { 2.0 }

if ($Renderer -notin @("cairo", "opengl")) {
    throw "Unsupported renderer: $Renderer"
}

if (Test-Path $FrameDir) {
    Remove-Item -Recurse -Force $FrameDir
}
if ($Renderer -eq "opengl" -and (Test-Path $CanonicalDir)) {
    Remove-Item -Recurse -Force $CanonicalDir
}

New-Item -ItemType Directory -Force $FrameDir | Out-Null
New-Item -ItemType Directory -Force $VideoDir | Out-Null
if ($Renderer -eq "opengl") {
    New-Item -ItemType Directory -Force $CanonicalDir | Out-Null
}

$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$Manim = Join-Path $RepoRoot ".venv\Scripts\manim.exe"

$sceneFileForPython = $SceneFile.Replace("\", "\\")
$totalFrames = [int](& $Python -c "import importlib.util, math; scene_path=r'$sceneFileForPython'; spec=importlib.util.spec_from_file_location('revolve_slice_prototype', scene_path); module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); print(int(math.ceil(module.EXACT_CLIP_DURATION * $Fps)))")

for ($frameIndex = 0; $frameIndex -lt $totalFrames; $frameIndex++) {
    $clipTime = "{0:F12}" -f ($frameIndex / [double]$Fps)
    $canonicalFramePath = Join-Path $CanonicalDir ("frame_{0:0000}.png" -f $frameIndex)
    $outputFramePath = Join-Path $FrameDir ("frame_{0:0000}.png" -f $frameIndex)

    $env:MANIM_THEME = $Theme
    $env:MANIM_CLIP_TIME = $clipTime
    & $Manim -qk -s -r $FrameSize --disable_caching $SceneFile ExactClipFrame -o "__exact_clip_canonical.png" | Out-Null

    if ($Renderer -eq "cairo") {
        Copy-Item (Join-Path $ImageDir "__exact_clip_canonical.png") $outputFramePath -Force
        continue
    }

    Copy-Item (Join-Path $ImageDir "__exact_clip_canonical.png") $canonicalFramePath -Force

    $env:MANIM_CANONICAL_FRAME = (Resolve-Path $canonicalFramePath).Path
    Remove-Item Env:MANIM_CLIP_TIME -ErrorAction SilentlyContinue
    & $Manim --renderer=opengl -qk -s -r $FrameSize --disable_caching $SceneFile CanonicalFramePlayback -o "__exact_clip_opengl.png" | Out-Null

    Copy-Item (Join-Path $ImageDir "__exact_clip_opengl.png") $outputFramePath -Force
}

Remove-Item Env:MANIM_CANONICAL_FRAME -ErrorAction SilentlyContinue
Remove-Item Env:MANIM_CLIP_TIME -ErrorAction SilentlyContinue

& ffmpeg -y `
    -framerate $Fps `
    -i (Join-Path $FrameDir "frame_%04d.png") `
    -vf "tpad=stop_mode=clone:stop_duration=$EndHoldSeconds,format=yuv420p" `
    -an `
    -c:v libx264 `
    -profile:v high `
    -level 4.1 `
    -pix_fmt yuv420p `
    -movflags +faststart `
    -preset slow `
    -crf 18 `
    $OutputPath | Out-Null

Write-Output $OutputPath
