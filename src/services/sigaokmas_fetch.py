"""Ambil harga pangan SIGAOKMAS Kab. Banyumas → CSV + ringkasan median.

Portal publik, tanpa auth. Dua jalur: koneksi langsung, lalu reader proxy publik
(portal memutus TLS dari sebagian jaringan). Dipakai oleh tools/refresh_sigaokmas.py
dan oleh cron Modal yang menulis ke volume /data.
"""
from __future__ import annotations

import csv
import datetime
import json
import statistics
import urllib.parse
from pathlib import Path
from typing import Any

import requests
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings()

BASE = "https://sigaokmas.banyumaskab.go.id/site/komoditas"
PROXY = "https://r.jina.ai/"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

# Komoditas yang relevan untuk resep bakpao.
IDS = [120, 106, 145, 107, 108, 117, 118, 147, 123, 124]

# p1 kosong = agregat kabupaten.
MARKETS = {"": "KABUPATEN BANYUMAS", "4": "SARIMULYO", "5": "PON", "6": "SITUMPUR", "7": "PROLIMAN"}

WIB = datetime.timezone(datetime.timedelta(hours=7))

DEFAULT_OUT = Path(__file__).resolve().parents[1] / "data" / "cache" / "sigaokmas"


def _params(p1: str, r1: str, r2: str) -> list[tuple[str, str]]:
    p: list[tuple[str, str]] = [("p1", p1), ("r1", r1), ("r2", r2)]
    p += [("ark[]", str(i)) for i in IDS]
    return p


def _get_direct(url: str, params: list[tuple[str, str]]) -> str | None:
    # Situs instansi ini memakai rantai sertifikat yang tidak lengkap; verifikasi
    # dicoba dulu, lalu dilonggarkan khusus host ini. Data yang diambil publik.
    for verify in (True, False):
        try:
            r = requests.get(url, params=params, headers={"User-Agent": UA}, timeout=30, verify=verify)
            if r.status_code == 200 and "table-hover" in r.text:
                return r.text
            break
        except requests.exceptions.SSLError:
            continue
        except Exception:
            break
    return None


def _get_proxy(url: str, params: list[tuple[str, str]]) -> str | None:
    target = f"{url}?{urllib.parse.urlencode(params, doseq=True)}"
    try:
        r = requests.get(
            PROXY + target,
            headers={"User-Agent": UA, "X-Return-Format": "html", "x-no-cache": "true"},
            timeout=90,
        )
        if r.status_code == 200 and "table-hover" in r.text:
            return r.text
    except Exception:
        pass
    return None


def _num(raw: str) -> int:
    digits = raw.replace("\xa0", "").replace(".", "").replace(",", "").strip()
    return int(digits) if digits.isdigit() else 0


def parse(html: str, cakupan: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", class_="table-hover")
    if table is None:
        return []
    dates = [th.get_text(strip=True) for th in table.select("thead th")[3:]]
    rows: list[dict[str, Any]] = []
    for tr in table.select("tbody tr"):
        td = [c.get_text(strip=True) for c in tr.find_all("td")]
        if len(td) < 4 or not td[1]:
            continue
        komoditas, pasar = td[1], td[2] or cakupan
        for tanggal, nilai in zip(dates, td[3:]):
            rows.append(
                {
                    "tanggal": tanggal,
                    "komoditas": komoditas,
                    "pasar": pasar,
                    "harga": _num(nilai),
                    "cakupan": cakupan,
                }
            )
    return rows


def ringkas(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Median harga > 0 per komoditas dalam satu cakupan pasar."""
    per: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        if r["harga"] > 0:
            per.setdefault(r["komoditas"], []).append(r)
    out: dict[str, Any] = {}
    for komoditas, items in sorted(per.items()):
        items.sort(key=lambda x: x["tanggal"])
        harga = [x["harga"] for x in items]
        out[komoditas] = {
            "median": int(round(statistics.median(harga))),
            "min": min(harga),
            "max": max(harga),
            "n_hari": len(harga),
            "terakhir": {"tanggal": items[-1]["tanggal"], "harga": items[-1]["harga"]},
        }
    return out


def refresh(days: int = 7, markets: list[str] | None = None,
            out_dir: Path | str | None = None, jeda: float = 1.5) -> dict[str, Any]:
    """Ambil `days` hari terakhir (berakhir H-1), simpan CSV + median_7d.json."""
    import time

    out = Path(out_dir) if out_dir else DEFAULT_OUT
    daftar = list(MARKETS) if markets is None else markets

    hari_ini = datetime.datetime.now(WIB).date()
    r2 = hari_ini - datetime.timedelta(days=1)
    r1 = r2 - datetime.timedelta(days=days - 1)
    r1s, r2s = r1.isoformat(), r2.isoformat()

    semua: list[dict[str, Any]] = []
    gagal: list[str] = []
    modes: set[str] = set()
    for p1 in daftar:
        cakupan = MARKETS.get(p1, p1)
        params = _params(p1, r1s, r2s)
        html = _get_direct(BASE, params)
        mode = "direct"
        if html is None:
            html = _get_proxy(BASE, params)
            mode = "proxy"
        if html is None:
            gagal.append(cakupan)
            continue
        modes.add(mode)
        semua += parse(html, cakupan)
        time.sleep(jeda)

    if not semua:
        return {"ok": False, "error": "tidak_ada_data", "gagal": gagal}

    out.mkdir(parents=True, exist_ok=True)
    with (out / "prices_raw.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["tanggal", "komoditas", "pasar", "harga"])
        for r in semua:
            w.writerow([r["tanggal"], r["komoditas"], r["pasar"], r["harga"]])

    cakupan_out = {}
    for nama in {r["cakupan"] for r in semua}:
        cakupan_out[nama] = ringkas([r for r in semua if r["cakupan"] == nama])

    summary = {
        "sumber": "sigaokmas.banyumaskab.go.id",
        "catatan": "Harga eceran rata-rata tingkat pasar, bukan harga supplier",
        "diambil_pada": datetime.datetime.now(WIB).isoformat(timespec="seconds"),
        "periode": {"dari": r1s, "sampai": r2s},
        "mode_ambil": sorted(modes),
        "cakupan": cakupan_out,
    }
    (out / "median_7d.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "ok": True,
        "baris": len(semua),
        "out_dir": str(out),
        "periode": {"dari": r1s, "sampai": r2s},
        "mode_ambil": sorted(modes),
        "gagal": gagal,
        "cakupan": {k: len(v) for k, v in cakupan_out.items()},
    }
