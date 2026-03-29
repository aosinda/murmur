"""Generate the Murmur app icon (simple microphone-style circle)."""

import subprocess
import struct
import zlib
from pathlib import Path


def create_png(width, height, color_rgb, bg_alpha=0):
    """Create a simple PNG with a centered filled circle."""
    import math

    cx, cy = width // 2, height // 2
    radius = min(width, height) // 2 - 2

    def make_row(y):
        row = bytearray()
        row.append(0)  # filter byte
        for x in range(width):
            dist = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
            if dist <= radius:
                row.extend(color_rgb)
                row.append(255)
            else:
                row.extend([0, 0, 0])
                row.append(bg_alpha)
        return bytes(row)

    raw = b"".join(make_row(y) for y in range(height))

    def chunk(chunk_type, data):
        c = chunk_type + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


def create_icns(output_path):
    """Create a .icns file from PNGs using iconutil."""
    iconset_dir = Path("build/Murmur.iconset")
    iconset_dir.mkdir(parents=True, exist_ok=True)

    # macOS iconset requires specific sizes
    sizes = {
        "icon_16x16.png": 16,
        "icon_16x16@2x.png": 32,
        "icon_32x32.png": 32,
        "icon_32x32@2x.png": 64,
        "icon_128x128.png": 128,
        "icon_128x128@2x.png": 256,
        "icon_256x256.png": 256,
        "icon_256x256@2x.png": 512,
        "icon_512x512.png": 512,
        "icon_512x512@2x.png": 1024,
    }

    # Green circle icon (matches our tray icon)
    color = (100, 200, 130)

    for name, size in sizes.items():
        png_data = create_png(size, size, color)
        (iconset_dir / name).write_bytes(png_data)

    subprocess.run(
        ["iconutil", "-c", "icns", str(iconset_dir), "-o", str(output_path)],
        check=True,
    )
    print(f"Created {output_path}")


if __name__ == "__main__":
    create_icns("Murmur.icns")
    print("Icon created. Now run: pyinstaller murmur.spec")
