"""Ukur bakpao dari foto lewat API publik.

Dua jalur:
  frasa  -> /api/vision/measure backend sam3, tanpa titik manual
  titik  -> backend sam21 (SAM 2.1 di Modal CPU), tiap titik satu objek

Contoh:
  python tools/ukur_bakpao.py --foto nampan.jpg --frasa "steamed bun"
  python tools/ukur_bakpao.py --foto nampan.jpg --titik 300,225 --px-per-cm 20
"""
import argparse
import base64
import json
import time
import urllib.request

DEFAULT_URL = "https://bakpao.my.id/api/vision/measure"


def _baca_titik(teks: str) -> list[list[int]]:
    titik = []
    for bagian in teks.split(";"):
        x, y = bagian.split(",")
        titik.append([int(x), int(y)])
    return titik


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--foto", required=True)
    p.add_argument("--frasa", default="")
    p.add_argument("--titik", default="", help='mis. "300,225" atau "300,225;420,260"')
    p.add_argument("--px-per-cm", type=float, default=0.0)
    p.add_argument("--url", default=DEFAULT_URL)
    a = p.parse_args()

    if not a.frasa and not a.titik:
        p.error("isi --frasa atau --titik")

    with open(a.foto, "rb") as f:
        gambar = base64.b64encode(f.read()).decode()

    body: dict = {"image_b64": gambar}
    if a.frasa:
        body["backend"] = "sam3"
        body["phrase"] = a.frasa
    else:
        body["points"] = _baca_titik(a.titik)
        if a.px_per_cm > 0:
            body["scale_cm"] = {"px_per_cm": a.px_per_cm}

    req = urllib.request.Request(
        a.url, data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json",
                 "User-Agent": "bakpao-cli/1.0"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=300) as r:
        hasil = json.load(r)
    print(json.dumps(hasil, indent=2, ensure_ascii=False))
    print(f"\n// {time.time() - t0:.1f} detik", flush=True)
    return 0 if hasil.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
