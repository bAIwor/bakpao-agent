"""Katalog: poster via muse-image-1.0 (Meta API), caption via Baseten.

Kontrak terverifikasi (preflight P1): gambar = base64 WEBP di
output[].image_generation_call.result (diawali 'UklGR'), output_text kosong.
Caption TIDAK bisa dari model gambar -> dibuat via Baseten open-weights.
"""
import base64
import html
import json
import re
import time
import urllib.request
from pathlib import Path

from src.core.config import get_settings
from src.core.guardrail import FORBIDDEN_TERMS, GUARDRAIL_SYSTEM

POSTER_USD = 0.01
FILLING = {"ayam": "ayam gurih", "coklat": "coklat lumer",
           "kacang_hijau": "tausa kacang hijau"}


def _repo() -> Path:
    return Path(__file__).resolve().parents[2]


def load_products() -> list:
    items = json.loads(
        (_repo() / "src" / "data" / "products.json").read_text(
            encoding="utf-8"))
    return [it for it in items if it.get("active", True)]


def extract_image_b64(resp: dict):
    """Ambil base64 gambar dari respons; None kalau tidak ada."""
    for item in resp.get("output", []):
        if item.get("type") == "image_generation_call" and item.get("result"):
            return item["result"]
    return None


def _meta_post(payload: dict, timeout: float = 300.0) -> dict:
    cfg = get_settings()
    if not cfg.MODEL_API_KEY:
        raise ValueError("MODEL_API_KEY kosong")
    req = urllib.request.Request(
        cfg.META_API_BASE_URL.rstrip("/") + "/responses",
        data=json.dumps(payload).encode(),
        headers={"Authorization": "Bearer " + cfg.MODEL_API_KEY,
                 "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


async def generate_poster(product: dict, out_path: Path) -> dict:
    """Poster katalog brand untuk 1 produk. Gagal -> ok:false, tanpa crash."""
    t0 = time.time()
    prompt = (
        f"Buat poster katalog bakpao: foto produk premium warung, "
        f"warna krem-coklat, maskot chef, ruang kosong untuk nama "
        f"\"{product['name']}\" dan harga. Tanpa elemen lain.")
    payload = {
        "model": "muse-image-1.0",
        "input": [{"role": "user", "content": [
            {"type": "input_text", "text": prompt}]}],
        "max_output_tokens": 4096,
        "reasoning": {"effort": "low"},
    }
    try:
        resp = _meta_post(payload)
    except Exception as e:
        return {"ok": False, "error": "poster_gagal",
                "detail": f"{type(e).__name__}"}
    if resp.get("status") != "completed":
        return {"ok": False, "error": "poster_gagal",
                "detail": str(resp.get("status"))}
    b64 = extract_image_b64(resp)
    if not b64:
        return {"ok": False, "error": "poster_gagal",
                "detail": "tanpa image_generation_call"}
    try:
        raw = base64.b64decode(b64)
    except Exception:
        return {"ok": False, "error": "poster_gagal",
                "detail": "base64 rusak"}
    if not (raw[:4] == b"RIFF" and raw[8:12] == b"WEBP"):
        return {"ok": False, "error": "poster_gagal",
                "detail": "bukan WEBP"}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(raw)
    return {"ok": True, "path": str(out_path),
            "bytes": len(raw), "usd": POSTER_USD,
            "seconds": round(time.time() - t0, 1)}


def caption_template(product: dict) -> str:
    isi = FILLING.get(product.get("flavor", ""), "pilihan")
    return (f"{product['name']} hangat dari dapur kami. "
            f"Isi {isi}, cocok untuk camilan sore.")


def _numbers(text: str) -> list:
    return [int(n.replace(".", "")) for n in re.findall(r"\d[\d.]*", text)]


def validate_caption(text: str, product: dict, price: int) -> tuple:
    """(boleh_pakai, alasan). Deterministik."""
    t = (text or "").strip()
    if not (20 <= len(t) <= 300):
        return False, "panjang"
    low = t.lower()
    for w in FORBIDDEN_TERMS:
        if w in low:
            return False, "kata-terlarang"
    for n in _numbers(t):
        if n != price:
            return False, "harga-beda"
    return True, "ok"


def _baseten_post(payload: dict, timeout: float = 120.0) -> dict:
    cfg = get_settings()
    if not cfg.BASETEN_API_KEY or not cfg.BASETEN_BASE_URL:
        raise ValueError("konfigurasi Baseten kosong")
    req = urllib.request.Request(
        cfg.BASETEN_BASE_URL.rstrip("/") + "/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Authorization": "Bearer " + cfg.BASETEN_API_KEY,
                 "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


async def generate_caption(product: dict, price: int) -> str:
    """Caption Bahasa Indonesia via Baseten; gagal/ tidak valid -> template."""
    cfg = get_settings()
    prompt = (f"Tulis 1 caption jualan Bahasa Indonesia untuk "
              f"{product['name']} seharga {price}. Maks 2 kalimat. "
              f"Sebutkan isi dan rasa saja. Balas HANYA teks caption.")
    try:
        resp = _baseten_post(
            {"model": cfg.BASETEN_MODEL,
             "messages": [{"role": "system", "content": GUARDRAIL_SYSTEM},
                          {"role": "user", "content": prompt}],
             "max_tokens": 2048, "temperature": 0.7})
        text = resp["choices"][0]["message"]["content"]
    except Exception:
        return caption_template(product)
    ok, _ = validate_caption(text, product, price)
    return text.strip() if ok else caption_template(product)


def build_pricelist(products: list) -> str:
    """Markdown price list — harga dari produk, bukan hardcode."""
    lines = ["# Menu Bakpao.my.id", "",
             "| Produk | Isi | Harga |", "|---|---|---|"]
    for p in products:
        isi = FILLING.get(p.get("flavor", ""), "-")
        lines.append(f"| {p['name']} | {isi} "
                     f"| Rp {p['price']:,}".replace(",", ".") + " |")
    return "\n".join(lines)


def poster_path(product_id: str) -> Path:
    return _repo() / "src" / "static" / "assets" / "katalog" / \
        f"{product_id}.webp"


async def publish_catalog() -> dict:
    """Tulis data/catalog.json + render src/static/katalog.html."""
    products = load_products()
    entries = []
    for p in products:
        img = f"/static/assets/katalog/{p['id']}.webp" \
            if poster_path(p["id"]).is_file() else p["img"]
        entries.append({"id": p["id"], "name": p["name"],
                        "price": p["price"], "img": img,
                        "caption": await generate_caption(p, p["price"])})
    data_dir = _repo() / "src" / "data"
    (data_dir / "catalog.json").write_text(
        json.dumps(entries, ensure_ascii=False, indent=1), encoding="utf-8")
    cards = "\n".join(
        f"""<div class="card">
      <img src="{e['img']}" alt="{html.escape(e['name'])}">
      <h3>{html.escape(e['name'])}</h3>
      <p class="price">Rp {e['price']:,}</p>
      <p class="caption">{html.escape(e['caption'])}</p>
    </div>""".replace(",", ".") for e in entries)
    page = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Katalog — Bakpao.my.id</title>
<script src="https://cdn.tailwindcss.com"></script>
<link href="https://fonts.googleapis.com/css2?family=Calistoga&family=Plus+Jakarta+Sans:wght@400;600;700&display=swap" rel="stylesheet">
<style>
  body {{ font-family: 'Plus Jakarta Sans', system-ui, sans-serif; background: #faf7f2; }}
  .font-display {{ font-family: 'Calistoga', serif; }}
  .card {{ background: #fff; border: 1.5px solid #f3ebe0; border-radius: 1rem; padding: 1rem; }}
  .card img {{ width: 100%; border-radius: 0.75rem; }}
  .card h3 {{ font-family: 'Calistoga', serif; color: #451a03; margin-top: 0.5rem; }}
  .price {{ font-weight: 800; color: #92400e; }}
  .caption {{ font-size: 0.875rem; color: #57534e; }}
</style>
</head>
<body class="text-stone-900">
<main class="max-w-4xl mx-auto px-4 py-6">
  <a href="/" class="text-sm underline">&larr; Toko</a>
  <h1 class="font-display text-3xl text-amber-950 mt-2">Katalog Bakpao.my.id</h1>
  <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5 mt-4">
{cards}
  </div>
</main>
</body>
</html>"""
    (_repo() / "src" / "static" / "katalog.html").write_text(
        page, encoding="utf-8")
    return {"ok": True, "count": len(entries)}
