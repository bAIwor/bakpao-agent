"""Verifikasi bukti transfer lewat model open-weights Meta (Baseten).

Kontrak: muse_tasks/BAKPAO_04 + BAKPAO_00 §11.12.
Screenshot diproses di memory, TIDAK ditulis ke disk, TIDAK di-log.

Pembagian tugas:
- model hanya membaca gambar -> JSON
- keputusan LUNAS / TIDAK_COCOK / PERLU_DICEK dihitung di kode (deterministik)
"""
from __future__ import annotations

import base64
import datetime
import json
import os
import re
from pathlib import Path

import httpx

from src.core.config import get_settings
from src.core.guardrail import GUARDRAIL_SYSTEM

STATUS_PAID = "LUNAS"
STATUS_REJECT = "TIDAK_COCOK"
STATUS_REVIEW = "PERLU_DICEK"
STATUS_ERROR = "GAGAL"

WINDOW_MINUTES = 60
MIN_CONFIDENCE = 0.6
REVIEW_CONFIDENCE = 0.8

# Struk menampilkan jam lokal (WIB, UTC+7) tanpa zona waktu. Pesanan disimpan
# dalam UTC, jadi waktu struk yang tanpa zona WAJIB dibaca sebagai WIB —
# kalau tidak, setiap verifikasi akan meleset 7 jam.
STORE_TZ = datetime.timezone(datetime.timedelta(hours=7))

PROMPT = (
    "Baca screenshot ini. Kalau isinya bukti transfer atau pembayaran "
    "(DANA, e-wallet, atau mobile banking), kembalikan objek JSON dengan field: "
    "is_transfer_screenshot (boolean), detected_amount (integer rupiah tanpa titik "
    "atau koma, null kalau tidak ada), detected_reference (string: ID Transaksi atau "
    "nomor referensi, string kosong kalau tidak ada), detected_bank (string metode "
    "pembayaran), detected_time (string ISO 8601 'YYYY-MM-DDTHH:MM:SS', string kosong "
    "kalau tidak ada), confidence (angka 0 sampai 1), notes (string pendek). "
    "Balas HANYA JSON."
)

_GROUPED = re.compile(r"^\d{1,3}(?:[.,]\d{3})+$")
_GROUPED_DEC = re.compile(r"^\d{1,3}(?:[.,]\d{3})+[.,]\d{2}$")
_PLAIN = re.compile(r"^\d+$")
_DECIMAL = re.compile(r"^\d+[.,]\d{2}$")
_RP_PREFIX = re.compile(r"(?i)^rp\.?\s*")


def normalise_amount(raw) -> tuple[int | None, str | None]:
    """Semua varian penulisan nominal -> int. Return (amount, alasan_gagal)."""
    if isinstance(raw, bool):
        return None, "nominal_tidak_terbaca"
    if isinstance(raw, int):
        return raw, None
    if raw is None:
        return None, "nominal_tidak_terbaca"
    text = _RP_PREFIX.sub("", str(raw).strip()).strip()
    if not text:
        return None, "nominal_tidak_terbaca"
    if re.search(r"[A-Za-z]", text):
        # huruf di area angka = hasil baca ambigu; jangan menebak
        return None, "nominal_ambigu"
    if _GROUPED_DEC.match(text):
        # '13,185.00' -> buang 2 digit sen, lalu buang pemisah ribuan
        return int(re.sub(r"\D", "", text[:-3])), None
    if _GROUPED.match(text):
        return int(re.sub(r"\D", "", text)), None
    if _PLAIN.match(text):
        return int(text), None
    if _DECIMAL.match(text):
        return int(re.split(r"[.,]", text)[0]), None
    digits = re.sub(r"\D", "", text)
    if digits:
        return int(digits), None
    return None, "nominal_tidak_terbaca"


def parse_time(raw) -> datetime.datetime | None:
    """ISO tanpa zona waktu dibaca sebagai jam toko (WIB); hasil selalu UTC."""
    if not raw or not isinstance(raw, str):
        return None
    text = raw.strip().replace("Z", "+00:00")
    try:
        stamp = datetime.datetime.fromisoformat(text)
    except ValueError:
        return None
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=STORE_TZ)
    return stamp.astimezone(datetime.timezone.utc)


def _blank(order_code: str, expected_amount: int) -> dict:
    return {
        "verified": False,
        "status": STATUS_REVIEW,
        "reason": "",
        "order_code": order_code,
        "expected_amount": expected_amount,
        "detected_amount": None,
        "detected_reference": "",
        "detected_bank": "",
        "confidence": 0.0,
        "needs_human_review": True,
        "notes": "",
    }


def decide(detected: dict, expected_amount: int, order_code: str,
           used_rrn: dict, created_at: str | None = None) -> dict:
    """Aturan pencocokan deterministik (BAKPAO_04 §3.2)."""
    out = _blank(order_code, expected_amount)
    if not isinstance(detected, dict):
        out.update(status=STATUS_ERROR, reason="respons_tidak_valid",
                   notes="model tidak mengembalikan JSON objek")
        return out

    amount, problem = normalise_amount(detected.get("detected_amount"))
    try:
        confidence = float(detected.get("confidence"))
    except (TypeError, ValueError):
        confidence = 0.0
    reference = str(detected.get("detected_reference") or "").strip()

    out.update(detected_amount=amount,
               detected_reference=reference,
               detected_bank=str(detected.get("detected_bank") or "").strip(),
               confidence=round(confidence, 3),
               notes=str(detected.get("notes") or "")[:200])

    if not detected.get("is_transfer_screenshot"):
        out.update(status=STATUS_REJECT, reason="bukan_struk_transfer")
        return out
    if problem:
        out.update(status=STATUS_REVIEW, reason=problem)
        return out
    if amount != expected_amount:
        out.update(status=STATUS_REJECT, reason="nominal_beda",
                   notes="selisih " + str(abs(expected_amount - amount)))
        return out

    owner = used_rrn.get(reference) if reference else None
    if reference and owner and owner != order_code:
        out.update(status=STATUS_ERROR, reason="duplikat_transaksi",
                   notes="nomor referensi sudah dipakai pesanan lain")
        return out

    if confidence < MIN_CONFIDENCE:
        out.update(status=STATUS_REVIEW, reason="confidence_rendah")
        return out

    paid_at = parse_time(detected.get("detected_time"))
    order_at = parse_time(created_at)
    if paid_at and order_at:
        gap = abs((paid_at - order_at).total_seconds()) / 60
        if gap > WINDOW_MINUTES:
            out.update(status=STATUS_REVIEW, reason="di_luar_jendela_waktu",
                       notes="selisih " + str(int(gap)) + " menit dari pesanan")
            return out

    out.update(verified=True, status=STATUS_PAID, reason="",
               needs_human_review=confidence < REVIEW_CONFIDENCE,
               notes=out["notes"] or "nominal cocok")
    return out


def _data_dir() -> Path:
    raw = os.environ.get("DATA_DIR", "")
    if raw:
        return Path(raw)
    return Path(__file__).resolve().parents[2] / "data"


def _rrn_path() -> Path:
    return _data_dir() / "used_rrn.json"


def load_used_rrn() -> dict:
    path = _rrn_path()
    if path.is_file():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def save_used_rrn(mapping: dict) -> None:
    _data_dir().mkdir(parents=True, exist_ok=True)
    _rrn_path().write_text(json.dumps(mapping, indent=1), encoding="utf-8")


async def read_receipt(image_bytes: bytes) -> dict:
    """Kirim screenshot ke model open-weights. Return dict mentah dari model."""
    cfg = get_settings()
    if not cfg.BASETEN_API_KEY:
        raise RuntimeError("BASETEN_API_KEY kosong")
    payload = {
        "model": cfg.BASETEN_MODEL,
        "messages": [
            {"role": "system", "content": GUARDRAIL_SYSTEM},
            {"role": "user", "content": [
                {"type": "text", "text": PROMPT},
                {"type": "image_url", "image_url": {
                    "url": "data:image/jpeg;base64,"
                           + base64.b64encode(image_bytes).decode()}},
            ]},
        ],
        "response_format": {"type": "json_object"},
        "max_tokens": 2048,
        "temperature": 0.0,
    }
    url = cfg.BASETEN_BASE_URL.rstrip("/") + "/chat/completions"
    async with httpx.AsyncClient(timeout=90) as client:
        resp = await client.post(
            url,
            headers={"Authorization": "Bearer " + cfg.BASETEN_API_KEY,
                     "Content-Type": "application/json"},
            json=payload)
    if resp.status_code != 200:
        raise RuntimeError("model http " + str(resp.status_code))
    body = resp.json()
    text = (body.get("choices") or [{}])[0].get("message", {}).get("content") or ""
    return json.loads(text)


async def verify_payment_screenshot(image_bytes: bytes, expected_amount: int,
                                    expected_suffix=None,
                                    order_code: str = "",
                                    created_at: str | None = None) -> dict:
    """Verifikasi bukti transfer. File tidak pernah ditulis ke disk."""
    del expected_suffix  # kode unik sudah termasuk di expected_amount
    try:
        detected = await read_receipt(image_bytes)
    except json.JSONDecodeError:
        detected = None
    except Exception as exc:  # jaringan, http, key
        result = _blank(order_code, expected_amount)
        result.update(status=STATUS_ERROR, reason="verifikasi_gagal",
                      notes=type(exc).__name__)
        return result

    used = load_used_rrn()
    result = decide(detected, expected_amount, order_code, used, created_at)

    if result["status"] == STATUS_PAID and result["detected_reference"]:
        used[result["detected_reference"]] = order_code
        save_used_rrn(used)
    return result
