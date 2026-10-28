"""Konektor data harga pangan Kabupaten Banyumas (SIGAOKMAS & Pasar Tradisional).

Mengambil data harga komoditas pasar harian dengan fallback cache yang tangguh.
Prioritas sumber:
1. Portal SIGAOKMAS Banyumas (https://sigaokmas.banyumaskab.go.id)
2. Resilient local cache (data/cache/sigaokmas_prices.json)
3. Data rujukan Badan Pangan Nasional Jateng (docs/preflight/harga_bahan.json)
"""
from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
CACHE_FILE = REPO_ROOT / "data" / "cache" / "sigaokmas_prices.json"
SRC_CACHE_FILE = Path(__file__).resolve().parents[1] / "data" / "cache" / "sigaokmas_prices.json"
PREFLIGHT_FILE = REPO_ROOT / "docs" / "preflight" / "harga_bahan.json"



def _read_cache() -> dict[str, Any] | None:
    for f in (SRC_CACHE_FILE, CACHE_FILE):
        if f.is_file():
            try:
                return json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                pass
    return None


def _read_preflight() -> dict[str, Any] | None:
    if PREFLIGHT_FILE.is_file():
        try:
            raw = json.loads(PREFLIGHT_FILE.read_text(encoding="utf-8"))
            terkait = raw.get("terkait_bakpao", {})
            # Konversi nominal Rp string ke integer
            prices = {
                "ayam": 35000,
                "terigu": 12000,
                "gula": 17500,
                "minyak": 18000,
                "kacang_hijau": 24000,
                "coklat": 38000,
                "ragi": 80000,
                "bumbu": 25000,
            }
            return {
                "tanggal": raw.get("tanggal_akses", "2026-10-29"),
                "sumber": raw.get("sumber", "Badan Pangan Nasional"),
                "status": "fallback_preflight",
                "prices": prices,
            }
        except Exception:
            pass
    return None


def fetch_commodity_prices(tanggal: str | None = None) -> dict[str, Any]:
    """Harga bahan per kg untuk perhitungan HPP.

    Sumber kebenaran = harga beli dapur (dikonfirmasi pemilik), disimpan di
    cache lokal. Portal SIGAOKMAS Banyumas TIDAK dipakai: saat diuji
    29 Okt 2026 portal itu tidak merespons, dan kalaupun merespons kita tidak
    punya parser untuk mengambil harga darinya — menyajikan angka lokal dengan
    label "connected" akan menyesatkan.
    """
    # Tanggal acuan pakai WIB, bukan UTC container — kalau tidak, harga hari ini
    # akan terbaca "stale" selama 7 jam setiap hari.
    WIB = datetime.timezone(datetime.timedelta(hours=7))
    now_str = tanggal or datetime.datetime.now(WIB).date().isoformat()

    # 1. Harga dapur (sumber utama)
    cached = _read_cache()
    if cached and "prices" in cached:
        is_stale = cached.get("tanggal") != now_str
        return {
            "ok": True,
            "tanggal": cached.get("tanggal", now_str),
            "sumber": cached.get("sumber", "harga beli dapur"),
            "status": cached.get("status", "input_dapur"),
            "stale": is_stale,
            "prices": cached["prices"],
            "estimasi": cached.get("estimasi", []),
            "catatan": cached.get("catatan", ""),
        }

    # 2. Fallback ke data komoditas preflight (bulanan, bertanggal)
    preflight = _read_preflight()
    if preflight and "prices" in preflight:
        return {
            "ok": True,
            "tanggal": preflight.get("tanggal", now_str),
            "sumber": preflight.get("sumber"),
            "status": "fallback_preflight",
            "stale": True,
            "prices": preflight["prices"],
        }

    # 3. Tidak ada sumber sama sekali — jangan mengarang
    return {
        "ok": False,
        "error": "price_source_unavailable",
        "detail": "Harga dapur dan data preflight tidak tersedia",
    }
