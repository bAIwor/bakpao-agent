import csv
import json
from pathlib import Path

from src.services.commodity_prices import fetch_commodity_prices
from src.services.sigaokmas import DATA_DIR, bandingkan_pasar, indeks_pasar

RAW = Path(DATA_DIR) / "prices_raw.csv"


def test_csv_columns():
    with RAW.open(encoding="utf-8") as f:
        header = next(csv.reader(f))
    assert header == ["tanggal", "komoditas", "pasar", "harga"]


def test_indeks_pasar_kabupaten():
    idx = indeks_pasar()
    assert idx["ok"] is True
    assert idx["eceran"]["ayam"]["median"] > 20000
    assert idx["eceran"]["terigu"]["n_hari"] >= 5


def test_bandingkan_dengan_harga_dapur():
    idx = indeks_pasar()
    hasil = bandingkan_pasar(idx, {"ayam": 35000})
    assert "ayam" in hasil
    assert hasil["ayam"]["selisih_dapur_vs_eceran_pct"] < 0


def test_fetch_melampirkan_indeks():
    payload = fetch_commodity_prices()
    assert payload["ok"] is True
    assert payload["indeks_pasar"]["ok"] is True
    assert "ayam" in payload["bandingan_pasar"]
    json.dumps(payload)
