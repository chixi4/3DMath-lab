#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT_DIR"

VENV_PATH="${VENV_PATH:-$ROOT_DIR/.venv-manimgl}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

"$PYTHON_BIN" -m venv "$VENV_PATH"
"$VENV_PATH/bin/pip" install --upgrade pip "setuptools<81" wheel
"$VENV_PATH/bin/pip" install "manimgl==1.7.2"

SITE_PACKAGES="$("$VENV_PATH/bin/python" - <<'PY'
import sysconfig
print(sysconfig.get_paths()["purelib"])
PY
)"

"$VENV_PATH/bin/python" - "$SITE_PACKAGES" <<'PY'
from pathlib import Path
import sys

site_packages = Path(sys.argv[1])
patches = {
    "manimlib/window.py": [
        (
            "@staticmethod\n    def note_undrawn_event(func: Callable[..., T]) -> Callable[..., T]:",
            "def note_undrawn_event(func: Callable[..., T]) -> Callable[..., T]:",
        ),
    ],
    "manimlib/shader_wrapper.py": [
        (
            "@lru_cache\n    @staticmethod\n    def get_fill_canvas(ctx: moderngl.Context) -> Tuple[Framebuffer, VertexArray, Framebuffer]:",
            "@staticmethod\n    @lru_cache\n    def get_fill_canvas(ctx: moderngl.Context) -> Tuple[Framebuffer, VertexArray, Framebuffer]:",
        ),
    ],
    "manimlib/mobject/mobject.py": [
        (
            "@staticmethod\n    def affects_data(func: Callable[..., T]) -> Callable[..., T]:",
            "def affects_data(func: Callable[..., T]) -> Callable[..., T]:",
        ),
        (
            "@staticmethod\n    def affects_family_data(func: Callable[..., T]) -> Callable[..., T]:",
            "def affects_family_data(func: Callable[..., T]) -> Callable[..., T]:",
        ),
        (
            "@staticmethod\n    def stash_mobject_pointers(func: Callable[..., T]) -> Callable[..., T]:",
            "def stash_mobject_pointers(func: Callable[..., T]) -> Callable[..., T]:",
        ),
        (
            "@staticmethod\n    def affects_shader_info_id(func: Callable[..., T]) -> Callable[..., T]:",
            "def affects_shader_info_id(func: Callable[..., T]) -> Callable[..., T]:",
        ),
    ],
    "manimlib/scene/scene.py": [
        (
            "@staticmethod\n    def affects_mobject_list(func: Callable[..., T]) -> Callable[..., T]:",
            "def affects_mobject_list(func: Callable[..., T]) -> Callable[..., T]:",
        ),
    ],
}

for relative_path, replacements in patches.items():
    path = site_packages / relative_path
    text = path.read_text()
    updated = text
    for old, new in replacements:
        updated = updated.replace(old, new)
    if updated != text:
        path.write_text(updated)
        print(f"patched {relative_path}")
    else:
        print(f"unchanged {relative_path}")
PY

echo "manimgl environment ready at $VENV_PATH"
