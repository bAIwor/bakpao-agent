"""QRIS service: kode pesanan, nominal + kode unik, render QR, CRC16, 3 mode.

Sumber kebenaran payload = file teks (MERCHANT_QRIS_PAYLOAD_FILE),
bukan hardcode. CRC16 = CRC-16/CCITT-FALSE (poly 0x1021, init 0xFFFF).
"""
import base64
import io
import secrets
import string
from pathlib import Path

import qrcode

from src.core.config import get_settings

_ALPHABET = string.ascii_uppercase + string.digits


def generate_order_code() -> str:
    """mis. 'BQ-7F3K9A'."""
    return "BQ-" + "".join(secrets.choice(_ALPHABET) for _ in range(6))


def generate_unique_suffix() -> int:
    """100..999, dipakai di nominal."""
    return secrets.randbelow(900) + 100


def build_payment_url(order_code: str) -> str:
    return get_settings().STORE_BASE_URL.rstrip("/") + "/pay/" + order_code


def build_qr_payload(payment_url: str) -> str:
    """QR payload default = URL (bukan EMVCo buatan) — bisa discan."""
    return payment_url


def render_qr_base64(payload: str) -> str:
    """PNG base64 dari payload (qrcode lib)."""
    img = qrcode.make(payload)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def render_qris_png(payload: str) -> bytes:
    """PNG bytes dari payload QRIS."""
    img = qrcode.make(payload)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def format_rupiah(amount: int) -> str:
    """13185 -> 'Rp 13.185'."""
    return "Rp " + f"{amount:,}".replace(",", ".")


def build_amount_with_suffix(base: int, suffix: int) -> int:
    """amount = total_pesanan + suffix. mis. 13000 + 185 = 13185."""
    return base + suffix


def crc16_qris(payload: str) -> str:
    """CRC-16/CCITT-FALSE atas payload TANPA 4 hex nilai CRC
    (tag '6304' TETAP ikut dihitung). Divalidasi: QR merchant -> '79A2'."""
    crc = 0xFFFF
    for b in payload.encode("utf-8"):
        crc ^= b << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return f"{crc:04X}"


def load_static_payload() -> str:
    """Baca payload statis merchant dari file. Panjang wajib 205."""
    cfg = get_settings()
    root = Path(__file__).resolve().parents[2]
    p = Path(cfg.MERCHANT_QRIS_PAYLOAD_FILE)
    if not p.is_absolute():
        for cand in (root / p, Path.cwd() / p):
            if cand.is_file():
                p = cand
                break
    payload = p.read_text(encoding="utf-8").strip()
    if len(payload) != 205:
        raise ValueError(
            f"merchant_qris.txt panjang {len(payload)}, harus 205 — "
            "jangan ubah file, laporkan.")
    return payload


def _parse_tlv(body: str) -> list:
    """Parse EMVCo TLV -> [(tag, value)]."""
    out, i = [], 0
    while i + 4 <= len(body):
        tag, ln = body[i:i + 2], int(body[i + 2:i + 4])
        out.append((tag, body[i + 4:i + 4 + ln]))
        i += 4 + ln
    return out


def build_dynamic_qris_payload(static_payload: str, amount_idr: int) -> str:
    """Ubah tag 01 '11'->'12'; sisipkan tag 54 SESUDAH tag 53;
    hitung ulang CRC16. Return payload lengkap."""
    if not static_payload.endswith("6304" + static_payload[-4:]):
        raise ValueError("payload statis tidak diakhiri tag 6304+CRC")
    body = static_payload[:-4]
    assert body.endswith("6304"), "tag 6304 hilang"
    tlvs = _parse_tlv(body[:-4])
    # EMVCo tag 54 = nominal dengan titik desimal, mis. 13185 -> "13185.00".
    # JANGAN buang titiknya: tanpa titik nilainya terbaca 100x lipat.
    amount_str = f"{amount_idr}.00"
    rebuilt, inserted = [], False
    for tag, val in tlvs:
        if tag == "01":
            val = "12"
        rebuilt.append((tag, val))
        if tag == "53" and not inserted:
            rebuilt.append(("54", amount_str))
            inserted = True
    if not inserted:
        raise ValueError("tag 53 tidak ditemukan di payload")
    head = "".join(t + "%02d" % len(v) + v for t, v in rebuilt) + "6304"
    return head + crc16_qris(head)


def build_qris_for_order(amount_idr: int, order_code: str,
                         suffix=None) -> dict:
    """Return {mode, payload, png_b64, url, nominal, nominal_rp, suffix}
    sesuai env QR_MODE (static | dynamic | url)."""
    mode = get_settings().QR_MODE
    url = build_payment_url(order_code)
    if mode == "dynamic":
        payload = build_dynamic_qris_payload(load_static_payload(), amount_idr)
    elif mode == "url":
        payload = build_qr_payload(url)
    else:  # static (default, paling aman)
        mode = "static"
        payload = load_static_payload()
    return {"mode": mode, "payload": payload,
            "png_b64": render_qr_base64(payload), "url": url,
            "nominal": amount_idr, "nominal_rp": format_rupiah(amount_idr),
            "suffix": suffix}
