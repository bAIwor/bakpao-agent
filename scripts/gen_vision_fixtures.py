"""Fixture vision sintetis dengan skala diketahui (30 px/cm).

Keluar: tests/fixtures/vision/{tray_3_bakpao,tray_1_reject,tray_empty}.png
+ ground_truth.json. Institusional boleh sintetis.
"""
import json
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path("tests/fixtures/vision")
OUT.mkdir(parents=True, exist_ok=True)
W, H = 900, 600
BG = (235, 228, 218)
DOUGH, EDGE = (205, 165, 115), (110, 70, 35)


def base():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    # garis referensi: 300 px = 10 cm, 600 px = 20 cm
    d.rectangle([100, 500, 400, 520], fill=(40, 40, 40))
    d.rectangle([100, 545, 700, 565], fill=(40, 40, 40))
    return img, d


def bun(d, cx, cy, r):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=DOUGH,
              outline=EDGE, width=3)


img, d = base()
for cx in (200, 450, 700):
    bun(d, cx, 250, 60)
img.save(OUT / "tray_3_bakpao.png")

img, d = base()
bun(d, 200, 250, 60)
bun(d, 450, 250, 60)
bun(d, 700, 250, 30)   # kecil -> reject (luas 25% dari normal)
img.save(OUT / "tray_1_reject.png")

img, _ = base()
img.save(OUT / "tray_empty.png")

truth = {
    "px_per_cm": 30.0,
    "tray_3_bakpao.png": {"diameters_cm": [4.0, 4.0, 4.0],
                          "reject_count": 0},
    "tray_1_reject.png": {"reject_count": 1, "reject_rate_pct": 33.3},
    "tray_empty.png": {"count": 0},
}
(OUT / "ground_truth.json").write_text(
    json.dumps(truth, indent=1), encoding="utf-8")
print("fixture vision ->", OUT)
