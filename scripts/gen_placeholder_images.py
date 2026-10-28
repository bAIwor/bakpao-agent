"""Placeholder gambar produk (PIL). Diganti foto asli bila sudah ada."""
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path("src/static/assets/produk")
OUT.mkdir(parents=True, exist_ok=True)
STYLE = {                      # (warna latar, warna teks, label)
    "ayam": ((214, 178, 140), (90, 52, 26), "AYAM"),
    "coklat": ((120, 84, 60), (245, 230, 210), "COKLAT"),
    "kacang_hijau": ((150, 178, 132), (40, 62, 28), "KACANG"),
}
for flavor, (bg, fg, label) in STYLE.items():
    for size in ("reguler", "mini"):
        w, h = (480, 360) if size == "reguler" else (320, 240)
        im = Image.new("RGB", (w, h), bg)
        d = ImageDraw.Draw(im)
        d.ellipse([w * 0.22, h * 0.18, w * 0.78, h * 0.82], fill=fg)
        d.text((w * 0.36, h * 0.05), f"{label} {size.upper()}", fill=fg)
        im.save(OUT / f"bakpao-{flavor.replace('_', '-')}.jpg", quality=90)
print("6 placeholder dibuat ->", OUT)
