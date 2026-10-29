"""Indeks harga eceran SIGAOKMAS Kab. Banyumas dari cache lokal.

Angka SIGAOKMAS adalah rata-rata eceran konsumen tingkat pasar, sementara dapur
membeli grosir. Jadi indeks ini dipakai sebagai pembanding harga beli dapur,
bukan dasar perhitungan HPP. Cache diisi tools/refresh_sigaokmas.py.
"""
from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "cache" / "sigaokmas"
SUMMARY_FILE = DATA_DIR / "median_7d.json"
RAW_FILE = DATA_DIR / "prices_raw.csv"

WIB = datetime.timezone(datetime.timedelta(hours=7))

# Nama komoditas di portal -> kunci bahan di resep kita.
PETA = {
    "terigu": "Tepung Terigu, 1 kg",
    "gula": "Gula Pasir Curah, 1 kg",
    "minyak": "Minyak Goreng Curah, 1 lt",
    "ayam": "Daging Ayam Ras, 1 kg",
    "telur": "Telur Ayam Ras, 1kg",
    "kacang_hijau": "Kacang Hijau, 1 kg",
}


def indeks_pasar() -> dict[str, Any]:
    """Median 7 hari harga eceran kabupaten untuk bahan bakpao."""
    if not SUMMARY_FILE.is_file():
        return {"ok": False, "error": "indeks_belum_ada"}

    try:
        raw = json.loads(SUMMARY_FILE.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"ok": False, "error": "indeks_rusak", "detail": str(exc)}

    kab = (raw.get("cakupan") or {}).get("KABUPATEN BANYUMAS") or {}
    eceran = {}
    for kunci, nama in PETA.items():
        row = kab.get(nama)
        if row:
            eceran[kunci] = {**row, "nama": nama}

    periode = raw.get("periode") or {}
    umur_hari = None
    sampai = periode.get("sampai")
    if sampai:
        try:
            umur_hari = (datetime.datetime.now(WIB).date()
                         - datetime.date.fromisoformat(sampai)).days
        except ValueError:
            umur_hari = None

    return {
        "ok": bool(eceran),
        "sumber": raw.get("sumber", "sigaokmas.banyumaskab.go.id"),
        "catatan": raw.get("catatan", ""),
        "periode": periode,
        "diambil_pada": raw.get("diambil_pada"),
        "umur_hari": umur_hari,
        "stale": umur_hari is None or umur_hari > 1,
        "eceran": eceran,
    }


def bandingkan_pasar(indeks: dict[str, Any], prices: dict[str, Any]) -> dict[str, Any]:
    """Selisih harga beli dapur terhadap median eceran kabupaten (persen)."""
    out = {}
    for kunci, row in (indeks.get("eceran") or {}).items():
        dapur = prices.get(kunci)
        if not dapur:
            continue
        selisih = round((float(dapur) / row["median"] - 1) * 100, 1)
        out[kunci] = {
            "dapur": dapur,
            "eceran_median": row["median"],
            "selisih_dapur_vs_eceran_pct": selisih,
        }
    return out


def harga_hpp(harga_dapur: dict[str, Any], faktor: float = 1.0) -> dict[str, Any]:
    """Harga dasar HPP: median eceran SIGAOKMAS × faktor, sisanya harga beli dapur.

    Faktor 1,0 dipilih pemilik warung: HPP memakai harga pasar resmi apa adanya.
    Konsekuensinya HPP sedikit lebih tinggi dari harga grosir sebenarnya — arah
    yang aman, bukan yang menipu margin.
    """
    idx = indeks_pasar()
    if not idx.get("ok"):
        return {"ok": False, "prices": dict(harga_dapur), "sumber_per_bahan": {}}

    prices = dict(harga_dapur)
    provenance: dict[str, Any] = {}
    for kunci, row in idx["eceran"].items():
        if kunci not in prices:
            continue
        harga = int(round(row["median"] * faktor))
        prices[kunci] = harga
        provenance[kunci] = {
            "sumber": "sigaokmas",
            "harga": harga,
            "eceran_median": row["median"],
            "tanggal_eceran": row["terakhir"]["tanggal"],
            "faktor": faktor,
        }
    for kunci, harga in harga_dapur.items():
        provenance.setdefault(kunci, {"sumber": "dapur", "harga": harga})

    return {
        "ok": True,
        "prices": prices,
        "sumber_per_bahan": provenance,
        "periode": idx.get("periode"),
        "stale": idx.get("stale", True),
    }
