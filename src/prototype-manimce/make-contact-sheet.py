from __future__ import annotations

from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[1]
OUTPUT = REPO_ROOT / "output" / "prototype"
FRAMES = OUTPUT / "frames"


def main() -> None:
    OUTPUT.mkdir(exist_ok=True)
    FRAMES.mkdir(exist_ok=True)

    frame_paths = [
        FRAMES / "frame_01.png",
        FRAMES / "frame_02.png",
        FRAMES / "frame_03.png",
        FRAMES / "frame_04.png",
    ]
    images = [Image.open(path).convert("RGBA") for path in frame_paths]

    width, height = images[0].size
    composite = Image.new("RGBA", (width * 2, height * 2), (255, 255, 255, 255))
    composite.paste(images[0], (0, 0))
    composite.paste(images[1], (width, 0))
    composite.paste(images[2], (0, height))
    composite.paste(images[3], (width, height))
    composite.save(OUTPUT / "composite_4panel.png")


if __name__ == "__main__":
    main()
