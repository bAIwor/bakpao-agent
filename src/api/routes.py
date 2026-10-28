"""Endpoint API + halaman. Screenshot bukti: diterima, dipakai di memory,
TIDAK disimpan ke disk, TIDAK masuk log."""
import base64
import datetime
import io
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from PIL import Image
from pydantic import BaseModel, Field

from src.core.config import get_settings
from src.services import orders as store
from src.services.payment_verifier import verify_payment_screenshot
from src.services.qris_service import (build_amount_with_suffix,
                                        build_payment_url, build_qris_for_order,
                                        format_rupiah, render_qr_base64)

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
async def verify(code: str, file: UploadFile = File(...)):
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
        raw, order["amount"], order["unique_suffix"], code)
    del raw
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
