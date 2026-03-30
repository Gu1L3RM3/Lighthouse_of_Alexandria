from __future__ import annotations

from pathlib import Path
import struct


def png_to_ico(png_path: Path, ico_path: Path) -> None:
    png_bytes = png_path.read_bytes()

    # ICONDIR: reserved(0), type(1=icon), count(1 image)
    icon_dir = struct.pack("<HHH", 0, 1, 1)

    # ICONDIRENTRY for a PNG payload.
    # width, height, color_count, reserved, planes, bit_count, bytes_in_res, image_offset
    width = 128
    height = 128
    entry = struct.pack(
        "<BBBBHHII",
        width if width < 256 else 0,
        height if height < 256 else 0,
        0,
        0,
        1,
        32,
        len(png_bytes),
        6 + 16,
    )

    ico_path.parent.mkdir(parents=True, exist_ok=True)
    ico_path.write_bytes(icon_dir + entry + png_bytes)


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    png_path = project_root / "assets" / "images" / "icon" / "game_icon_128.png"
    ico_path = project_root / "assets" / "images" / "icon" / "game_icon.ico"
    png_to_ico(png_path, ico_path)
    print(f"ICO generated: {ico_path}")


if __name__ == "__main__":
    main()
