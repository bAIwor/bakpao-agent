"""Ambil harga pangan SIGAOKMAS Kab. Banyumas → cache lokal untuk HPP.

Portal publik, tanpa auth. Sejak 29 Okt 2026 jaringan kami diputus di level TLS
(server mengirim 0 byte setelah TCP connect), jadi jalur kedua memakai reader
proxy publik yang mengambil HTML mentah dari sisi mereka.

Pemakaian:
    python tools/refresh_sigaokmas.py
    python tools/refresh_sigaokmas.py --days 14 --markets "" 4 5
"""
from __future__ import annotations

import argparse
import csv
import datetime
import json
import statistics
import sys
import time
import urllib.parse
from pathlib import Path

import requests
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings()

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "src" / "data" / "cache" / "sigaokmas"

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


def parse(html: str, cakupan: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", class_="table-hover")
    if table is None:
        return []
    dates = [th.get_text(strip=True) for th in table.select("thead th")[3:]]
    rows = []
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


def ringkas(rows: list[dict]) -> dict:
    """Median harga > 0 per komoditas dalam satu cakupan pasar."""
    per: dict[str, list[dict]] = {}
    for r in rows:
        if r["harga"] > 0:
            per.setdefault(r["komoditas"], []).append(r)
    out = {}
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7, help="jumlah hari ke belakang (berakhir H-1)")
    ap.add_argument("--markets", nargs="*", default=list(MARKETS), help='id pasar; "" = kabupaten')
    args = ap.parse_args()

    hari_ini = datetime.datetime.now(WIB).date()
    r2 = hari_ini - datetime.timedelta(days=1)
    r1 = r2 - datetime.timedelta(days=args.days - 1)
    r1s, r2s = r1.isoformat(), r2.isoformat()

    semua: list[dict] = []
    modes: set[str] = set()
    for p1 in args.markets:
        cakupan = MARKETS.get(p1, p1)
        params = _params(p1, r1s, r2s)
        html = _get_direct(BASE, params)
        mode = "direct"
        if html is None:
            html = _get_proxy(BASE, params)
            mode = "proxy"
        if html is None:
            print(f"  GAGAL  {cakupan}", file=sys.stderr)
            continue
        modes.add(mode)
        rows = parse(html, cakupan)
        semua += rows
        n_valid = sum(1 for r in rows if r["harga"] > 0)
        print(f"  OK     {cakupan:<20} {n_valid:>3} harga  ({mode})")
        time.sleep(1.5)

    if not semua:
        print("Tidak ada data terkumpul.", file=sys.stderr)
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = OUT_DIR / "prices_raw.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
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
    json_path = OUT_DIR / "median_7d.json"
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n{len(semua)} baris -> {csv_path.relative_to(REPO_ROOT)}")
    print(f"ringkasan -> {json_path.relative_to(REPO_ROOT)}")
    kab = cakupan_out.get("KABUPATEN BANYUMAS", {})
    for komoditas, v in kab.items():
        print(f"  {komoditas:<45} median Rp{v['median']:>7}  (n={v['n_hari']}, {v['min']}-{v['max']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
