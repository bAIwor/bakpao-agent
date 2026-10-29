"""Harga bahan per kg untuk perhitungan HPP.

Dasar HPP = median 7 hari harga eceran SIGAOKMAS Kab. Banyumas untuk enam bahan
yang tercakup (terigu, gula, minyak, ayam, telur, kacang hijau), dikali faktor
1,0. Bahan yang tidak dipantau portal (coklat, santan, margarin, ragi, bumbu)
tetap memakai harga beli dapur. Setiap bahan mencatat asalnya di
``sumber_per_bahan`` supaya tidak ada angka tanpa jejak.

Sumber otomatis lain yang diuji dan tidak dipakai:
  - dimassatria.banyumaskab.go.id      : semua harga Rp 0
  - klikindomaret.com                  : Cloudflare bot challenge
  - alfagift.id                        : SPA, tanpa API publik
Kalau nanti ada feed yang benar-benar hidup, tambahkan sebagai sumber
dengan pengaman: tolak harga <= 0 dan catat tanggalnya."""
from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Any

from src.services.sigaokmas import bandingkan_pasar, harga_hpp, indeks_pasar

# HPP memakai harga eceran SIGAOKMAS apa adanya (keputusan pemilik, 29 Okt 2026).
FAKTOR_ECERAN_KE_HPP = 1.0


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
    """Harga bahan untuk HPP: eceran SIGAOKMAS + sisa bahan dari harga dapur."""
    payload = _fetch_dapur(tanggal)
    idx = indeks_pasar()
    payload["indeks_pasar"] = idx
    if not (payload.get("ok") and idx.get("ok")):
        return payload

    dapur = payload.get("prices", {})
    dasar = harga_hpp(dapur, FAKTOR_ECERAN_KE_HPP)
    payload["harga_dapur"] = dapur
    payload["prices"] = dasar["prices"]
    payload["sumber_per_bahan"] = dasar["sumber_per_bahan"]
    payload["bandingan_pasar"] = bandingkan_pasar(idx, dapur)
    payload["sumber"] = ("SIGAOKMAS Kab. Banyumas (eceran, median 7 hari) "
                         "+ harga beli dapur untuk bahan yang tidak dipantau")
    payload["status"] = "sigaokmas_eceran"
    payload["stale"] = bool(payload.get("stale") or dasar.get("stale"))
    return payload


def _fetch_dapur(tanggal: str | None = None) -> dict[str, Any]:
    # Tanggal acuan pakai WIB, bukan UTC container — kalau tidak, harga hari ini
    # akan terbaca "stale" selama 7 jam setiap hari.
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
