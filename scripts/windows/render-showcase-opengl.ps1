$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

$OutputBasename = if ($args.Length -gt 0) { $args[0] } else { "revolve-slice-showcase-white-phone" }
$env:MANIM_RENDERER = "opengl"
$env:MANIM_THEME = "light"
$env:OUTPUT_BASENAME = $OutputBasename

& (Join-Path $ScriptDir "render-exact-clip.ps1")
