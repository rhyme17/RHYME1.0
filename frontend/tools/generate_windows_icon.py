import argparse
from pathlib import Path

from PIL import Image


def build_icon(source_path: Path, output_path: Path) -> None:
    if not source_path.exists():
        raise FileNotFoundError(f"Icon source not found: {source_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]

    with Image.open(source_path) as img:
        if img.mode not in ("RGBA", "LA"):
            img = img.convert("RGBA")
        img.save(output_path, format="ICO", sizes=sizes)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Windows ICO from a source image")
    parser.add_argument("--source", required=True, help="Source image path, e.g. img.png")
    parser.add_argument("--output", required=True, help="Output ICO path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_path = Path(args.source).resolve()
    output_path = Path(args.output).resolve()
    build_icon(source_path, output_path)
    print(f"Icon generated: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

