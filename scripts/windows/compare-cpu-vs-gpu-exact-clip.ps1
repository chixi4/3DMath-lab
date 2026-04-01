$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path (Join-Path $ScriptDir "..\..")).Path
$SceneFile = Join-Path $RepoRoot "src\prototype-manimce\revolve-slice-prototype.py"
$ImageDir = Join-Path $RepoRoot "media\images\revolve-slice-prototype"
Set-Location $RepoRoot

$Theme = if ($env:MANIM_THEME) { $env:MANIM_THEME } else { "light" }
$FrameSize = if ($env:FRAME_SIZE) { $env:FRAME_SIZE } else { "1280,720" }
$SampleTimesRaw = if ($env:SAMPLE_TIMES) { $env:SAMPLE_TIMES } else { "0.000000000000,0.120000000000,1.920000000000,6.500000000000,8.980000000000,12.240000000000,16.840000000000" }
$OutDir = if ($env:OUT_DIR) { $env:OUT_DIR } else { "output\cpu-gpu-exact-clip-compare" }
$CpuDir = Join-Path $OutDir "cpu"
$GpuDir = Join-Path $OutDir "gpu"
$DiffDir = Join-Path $OutDir "diff"

if (Test-Path $OutDir) {
    Remove-Item -Recurse -Force $OutDir
}
New-Item -ItemType Directory -Force $CpuDir | Out-Null
New-Item -ItemType Directory -Force $GpuDir | Out-Null
New-Item -ItemType Directory -Force $DiffDir | Out-Null

$Manim = Join-Path $RepoRoot ".venv\Scripts\manim.exe"
$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$SampleTimes = $SampleTimesRaw.Split(",")

for ($index = 0; $index -lt $SampleTimes.Length; $index++) {
    $sampleTime = $SampleTimes[$index]
    $label = "sample_{0:00}" -f ($index + 1)

    $env:MANIM_THEME = $Theme
    $env:MANIM_CLIP_TIME = $sampleTime
    & $Manim -qk -s -r $FrameSize --disable_caching $SceneFile ExactClipFrame -o "__${label}_cpu.png" | Out-Null
    Copy-Item (Join-Path $ImageDir "__${label}_cpu.png") (Join-Path $CpuDir "$label.png") -Force

    Remove-Item Env:MANIM_CLIP_TIME -ErrorAction SilentlyContinue
    $env:MANIM_CANONICAL_FRAME = (Resolve-Path (Join-Path $CpuDir "$label.png")).Path
    & $Manim --renderer=opengl -qk -s -r $FrameSize --disable_caching $SceneFile CanonicalFramePlayback -o "__${label}_gpu.png" | Out-Null
    Copy-Item (Join-Path $ImageDir "__${label}_gpu.png") (Join-Path $GpuDir "$label.png") -Force
}

$env:CPU_DIR = (Resolve-Path $CpuDir).Path
$env:GPU_DIR = (Resolve-Path $GpuDir).Path
$env:DIFF_DIR = (Resolve-Path $DiffDir).Path
$env:SAMPLE_TIMES = $SampleTimesRaw

$CompareScript = @'
import os
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops

cpu_dir = Path(os.environ["CPU_DIR"])
gpu_dir = Path(os.environ["GPU_DIR"])
diff_dir = Path(os.environ["DIFF_DIR"])
sample_times = os.environ["SAMPLE_TIMES"].split(",")

mismatches = []
for index, sample_time in enumerate(sample_times, start=1):
    label = f"sample_{index:02d}"
    cpu_path = cpu_dir / f"{label}.png"
    gpu_path = gpu_dir / f"{label}.png"

    cpu_image = Image.open(cpu_path).convert("RGBA")
    gpu_image = Image.open(gpu_path).convert("RGBA")
    cpu_pixels = np.array(cpu_image)
    gpu_pixels = np.array(gpu_image)

    if cpu_pixels.shape != gpu_pixels.shape:
        mismatches.append((label, sample_time, "shape"))
        continue

    diff_mask = np.any(cpu_pixels != gpu_pixels, axis=2)
    if np.any(diff_mask):
        diff_image = ImageChops.difference(cpu_image, gpu_image)
        diff_image.save(diff_dir / f"{label}.png")
        mismatches.append((label, sample_time, int(np.count_nonzero(diff_mask))))

if mismatches:
    for label, sample_time, detail in mismatches:
        print(f"MISMATCH {label} t={sample_time} detail={detail}")
    raise SystemExit(1)

for index, sample_time in enumerate(sample_times, start=1):
    print(f"MATCH sample_{index:02d} t={sample_time}")
'@

$TempComparePath = Join-Path $OutDir "__compare_exact_clip.py"
Set-Content -Path $TempComparePath -Value $CompareScript -Encoding UTF8
& $Python $TempComparePath
