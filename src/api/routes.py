"""Endpoint API + halaman. Screenshot bukti: diterima, dipakai di memory,
TIDAK disimpan ke disk, TIDAK masuk log."""
import asyncio
import base64
import datetime
import io
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Response, UploadFile
from fastapi.responses import FileResponse
from PIL import Image
from pydantic import BaseModel, Field

from src.core.config import get_settings
from src.services import geometry as geo
from src.services import orders as store
from src.services.sam3_client import box_diameter_px, segment_text_prompt
from src.services.payment_verifier import verify_payment_screenshot
from src.services.pricing import calculate_catalog_hpp
from src.services.pricing_agent import evaluate_repricing
from src.services.qris_service import (build_amount_with_suffix,
                                        build_payment_url, build_qris_for_order,
                                        format_rupiah, render_qr_base64)
from src.services.commodity_prices import fetch_commodity_prices
from src.services.vision_client import measure_image

router = APIRouter()
STATIC = Path(__file__).resolve().parents[1] / "static"
REPO = Path(__file__).resolve().parents[2]
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
ALLOWED_MIME = {"image/png", "image/jpeg", "image/jpg", "image/webp"}


class OrderItem(BaseModel):
    product_id: str
    qty: int = Field(gt=0)


class OrderCreate(BaseModel):
    items: list[OrderItem]


@router.get("/api/health")
def health():
    return {"ok": True,
            "time": datetime.datetime.now(
                datetime.timezone.utc).isoformat(),
            "service": get_settings().STORE_NAME}


@router.get("/api/products")
def products():
    import json
    p = STATIC.parent / "data" / "products.json"
    items = json.loads(p.read_text(encoding="utf-8"))
    return {"products": [it for it in items if it.get("active", True)]}


@router.post("/api/orders")
def create(body: OrderCreate):
    try:
        order = store.create_order(
            [{"product_id": it.product_id, "qty": it.qty}
             for it in body.items])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    qris = build_qris_for_order(order["amount"], order["order_code"],
                                suffix=order["unique_suffix"])
    url = build_payment_url(order["order_code"])
    return {**order, "payment_url": url, "qr_b64": render_qr_base64(url),
            "qr_payload": url, "qris": {k: v for k, v in qris.items()
                                       if k != "png_b64"},
            "qris_png_b64": qris["png_b64"],
            "nominal_rp": format_rupiah(order["amount"]),
            "expected_check": build_amount_with_suffix(
                order["total"], order["unique_suffix"]) == order["amount"]}


@router.get("/api/orders/{code}")
def order_status(code: str):
    try:
        return store.get_order(code)
    except store.OrderNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/api/orders/{code}/verify")
async def verify(code: str, response: Response, file: UploadFile = File(...)):
    try:
        order = store.get_order(code)
    except store.OrderNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    if (file.content_type or "") not in ALLOWED_MIME:
        raise HTTPException(status_code=400,
                            detail="tipe file harus gambar (png/jpeg/webp)")
    raw = await file.read()
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400,
                            detail="file lebih dari 5 MB")
    try:
        with Image.open(io.BytesIO(raw)) as im:
            w, h = im.size
    except Exception:
        raise HTTPException(status_code=400, detail="file bukan gambar valid")
    if w < 200 or h < 200:
        raise HTTPException(status_code=400,
                            detail="gambar terlalu kecil (< 200 px)")
    result = await verify_payment_screenshot(
        raw, order["amount"], order["unique_suffix"], code, order["created_at"])
    del raw
    response.headers["Cache-Control"] = "no-store"
    if result.get("status") == "LUNAS":
        result["order"] = store.mark_paid(code)
    return result


@router.get("/api/orders/{code}/qr")
def order_qr(code: str):
    """QR halaman bayar (dibaca ulang oleh pay.html)."""
    try:
        order = store.get_order(code)
    except store.OrderNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    url = build_payment_url(code)
    return {"qr_b64": render_qr_base64(url), "url": url,
            "amount": order["amount"], "suffix": order["unique_suffix"]}


@router.post("/api/orders/{code}/cancel")
def cancel(code: str):
    try:
        return store.mark_failed(code)
    except store.OrderNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/api/orders/{code}/paid")
def paid(code: str):
    """Konfirmasi manual pemilik warung setelah cek mutasi DANA.

    Sementara sampai verifikasi bukti transfer otomatis aktif: verifier
    memanggil fungsi store yang sama di belakang layar.
    """
    try:
        return store.mark_paid(code)
    except store.OrderNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/api/orders/{code}/complete")
def complete(code: str):
    """Tombol dapur 'Siap Diantar'."""
    try:
        return store.mark_done(code)
    except store.OrderNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/api/kitchen/queue")
def queue():
    return {"queue": store.list_orders()}


class VisionMeasureBody(BaseModel):
    image_b64: str
    points: list | None = None
    scale_cm: dict | None = None
    backend: str = "sam21"
    phrase: str | None = None


SAM3_WARN = "diameter dari kotak, bukan mask — galat lebih besar"


def _vision_measure_sam3(raw: bytes, body: VisionMeasureBody) -> dict:
    """Jalur sam3: frasa -> box -> diameter. Tanpa titik manual."""
    if not (body.phrase or "").strip():
        raise HTTPException(status_code=400,
                            detail="phrase wajib untuk backend sam3")
    seg = asyncio.run(
        segment_text_prompt(raw, body.phrase.strip()))
    if not seg.get("ok"):
        return {"ok": False, "backend": "sam3", "error": seg.get("error"),
                "detail": seg.get("detail", ""), "confidence": "rendah",
                "warnings": [SAM3_WARN,
                             "vision tidak tersedia — angka tidak dihitung"]}
    boxes = seg.get("boxes", [])
    base = {"backend": "sam3", "phrase": seg.get("phrase"),
            "raw_chars": seg.get("raw_chars")}
    if not boxes:
        return {**base, "ok": True, "objects": [], "count": 0,
                "confidence": "rendah",
                "warnings": [SAM3_WARN, "tidak ada objek cocok"]}
    px_diams = [round(box_diameter_px(b), 1) for b in boxes]
    if not body.scale_cm or "px_per_cm" not in body.scale_cm:
        return {**base, "ok": True, "skala": "tidak_diketahui",
                "diameter_px": px_diams, "count": len(boxes),
                "confidence": "sedang",
                "warnings": [SAM3_WARN,
                             "tanpa acuan cm — angka dalam piksel"]}
    s = float(body.scale_cm["px_per_cm"])
    measured = geo.measure_objects(
        [{"area_px": (b["x2"] - b["x1"]) * (b["y2"] - b["y1"]), "iou": 1.0}
         for b in boxes], s)
    if not measured.get("ok"):
        return {**base, **measured, "confidence": "rendah",
                "warnings": [SAM3_WARN]}
    return {**base, **measured, "confidence": "sedang",
            "warnings": [SAM3_WARN, "skala dari pengguna, bukan papan acuan"]}


@router.post("/api/vision/measure")
def vision_measure(body: VisionMeasureBody, response: Response):
    """Ukur objek dari foto: segmen via Modal, geometri lokal.

    scale_cm = {"px_per_cm": angka} dari acuan yang diketahui.
    Tanpa scale_cm -> ukuran piksel saja, JANGAN mengarang cm.
    """
    response.headers["Cache-Control"] = "no-store"
    try:
        raw = base64.b64decode(body.image_b64, validate=True)
    except Exception:
        raise HTTPException(status_code=400, detail="base64 tidak valid")
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="file lebih dari 5 MB")
    try:
        with Image.open(io.BytesIO(raw)) as im:
            w, h = im.size
    except Exception:
        raise HTTPException(status_code=400, detail="file bukan gambar valid")
    if min(w, h) < 200:
        raise HTTPException(status_code=400,
                            detail="gambar terlalu kecil (< 200 px)")
    if (body.backend or "sam21") == "sam3":
        return _vision_measure_sam3(raw, body)
    if not body.points:
        return {"ok": False, "error": "titik_hilang",
                "detail": "sertakan points [[x, y], ...]",
                "confidence": "rendah", "warnings": ["tanpa titik prompt"]}
    seg = asyncio.run(measure_image(raw, body.points))
    if not seg.get("ok"):
        return {"ok": False, "error": seg.get("error"),
                "detail": seg.get("detail", ""),
                "confidence": "rendah",
                "warnings": ["vision tidak tersedia — angka tidak dihitung"]}
    if not body.scale_cm or "px_per_cm" not in body.scale_cm:
        return {"ok": True, "skala": "tidak_diketahui",
                "objects": seg["objects"], "image_px": seg["image_px"],
                "infer_seconds": seg.get("infer_seconds"),
                "confidence": "sedang",
                "warnings": ["tanpa acuan cm — angka dalam piksel"]}
    s = float(body.scale_cm["px_per_cm"])
    measured = geo.measure_objects(
        [{"area_px": o["area_px"], "iou": o["iou"]}
         for o in seg["objects"]], s)
    if not measured.get("ok"):
        return {**measured, "confidence": "rendah", "warnings": []}
    return {**measured, "image_px": seg["image_px"],
            "infer_seconds": seg.get("infer_seconds"),
            "confidence": "sedang",
            "warnings": ["skala dari pengguna, bukan papan acuan"]}


class RepriceBody(BaseModel):
    prices_today: dict[str, float] | None = None
    prices_yesterday: dict[str, float] | None = None
    prices_hari_ini: dict[str, float] | None = None
    prices_kemarin: dict[str, float] | None = None


@router.get("/api/pricing/commodities")
def pricing_commodities():
    """Harga bahan per kg (harga beli dapur + fallback preflight)."""
    return fetch_commodity_prices()


@router.get("/api/pricing/hpp")
def pricing_hpp():
    """Perhitungan HPP dan saran harga deterministik untuk seluruh katalog resep."""
    import json
    p = STATIC.parent / "data" / "recipes.json"
    recipes = json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}
    commodities = fetch_commodity_prices()
    prices = commodities.get("prices", {})
    catalog = calculate_catalog_hpp(recipes, prices)

    # Bandingkan dengan harga jual yang BENAR-BENAR dipakai, bukan hanya harga saran.
    produk_path = STATIC.parent / "data" / "products.json"
    produk = (json.loads(produk_path.read_text(encoding="utf-8"))
              if produk_path.is_file() else [])
    harga_aktual = {x.get("id"): x.get("price") for x in produk}
    for pid, row in catalog.items():
        aktual = harga_aktual.get(pid)
        if aktual:
            row["price_aktual"] = aktual
            row["margin_aktual"] = aktual - row["hpp"]
            row["food_cost_aktual_pct"] = round(row["hpp"] / aktual * 100, 1)

    return {
        "ok": True,
        "source": commodities.get("sumber", "tidak_diketahui"),
        "tanggal": commodities.get("tanggal"),
        "stale": commodities.get("stale", False),
        "indeks_pasar": commodities.get("indeks_pasar"),
        "bandingan_pasar": commodities.get("bandingan_pasar"),
        "products": catalog,
    }


@router.post("/api/pricing/reprice")
async def pricing_reprice(body: RepriceBody | None = None):
    """Jalankan evaluasi repricing cerdas (penalaran perubahan biaya pokok)."""
    import json
    p = STATIC.parent / "data" / "recipes.json"
    recipes = json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}

    commodities = fetch_commodity_prices()
    default_today = commodities.get("prices", {})

    b = body or RepriceBody()
    today = b.prices_today or b.prices_hari_ini or default_today
    yesterday = b.prices_yesterday or b.prices_kemarin or default_today

    decision = await evaluate_repricing(recipes, today, yesterday)
    return {
        "ok": True,
        "decision": decision,
        "input_prices": {"today": today, "yesterday": yesterday},
    }


@router.get("/merchant-qris-b64")
def merchant_qris_b64():
    """Gambar QRIS statis merchant sebagai base64 (fallback tampilan)."""
    cfg = get_settings()
    root = REPO
    p = Path(cfg.MERCHANT_QRIS_IMAGE)
    if not p.is_absolute():
        for cand in (root / "src" / p, root / p):
            if cand.is_file():
                p = cand
                break
    return {"png_b64": base64.b64encode(
        p.read_bytes()).decode()}


@router.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@router.get("/pay/{code}")
def pay(code: str):
    try:
        store.get_order(code)
    except store.OrderNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    return FileResponse(STATIC / "pay.html")


@router.get("/dapur")
def dapur():
    return FileResponse(STATIC / "dapur.html")


@router.get("/cara-kerja")
def cara_kerja():
    return FileResponse(STATIC / "cara-kerja.html")


class CatalogGenerate(BaseModel):
    product_id: str


@router.get("/katalog")
def katalog():
    page = STATIC / "katalog.html"
    if not page.is_file():
        raise HTTPException(status_code=404,
                            detail="katalog belum diterbitkan")
    return FileResponse(page)


@router.post("/api/catalog/generate")
async def catalog_generate(body: CatalogGenerate):
    from src.services import catalog_service as cat
    products = {p["id"]: p for p in cat.load_products()}
    if body.product_id not in products:
        raise HTTPException(status_code=404,
                            detail="produk tidak dikenal")
    product = products[body.product_id]
    poster = await cat.generate_poster(
        product, cat.poster_path(body.product_id))
    caption = await cat.generate_caption(product, product["price"])
    return {"product_id": body.product_id, "poster": poster,
            "caption": caption}
