"""
convert_icon.py — Converts Assets/logo.png to Assets/logo.ico
Run once before building the exe:  python convert_icon.py
Requires Pillow:  pip install Pillow
"""
from pathlib import Path
from PIL import Image

SRC = Path("Assets/logo.png")
DST = Path("Assets/logo.ico")

img = Image.open(SRC).convert("RGBA")

# Windows needs multiple sizes in one .ico for crisp display at every zoom level
sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
imgs = [img.resize(s, Image.LANCZOS) for s in sizes]

imgs[0].save(
    DST,
    format="ICO",
    sizes=sizes,
    append_images=imgs[1:],
)
print(f"Saved  {DST}  ({DST.stat().st_size // 1024} KB)")
