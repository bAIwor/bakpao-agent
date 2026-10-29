import csv
import json
from pathlib import Path

from src.services.commodity_prices import fetch_commodity_prices
from src.services.sigaokmas import BUNDLED_DIR, bandingkan_pasar, harga_hpp, indeks_pasar

RAW = Path(BUNDLED_DIR) / "prices_raw.csv"


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
    assert payload["status"] == "sigaokmas_eceran"
    json.dumps(payload)


def test_hpp_memakai_eceran_sigaokmas():
    idx = indeks_pasar()
    hasil = harga_hpp({"ayam": 35000, "coklat": 38000}, faktor=1.0)

    # Ayam tercakup portal → diganti median eceran; coklat tidak → tetap dapur.
    assert hasil["prices"]["ayam"] == idx["eceran"]["ayam"]["median"]
    assert hasil["prices"]["coklat"] == 38000
    assert hasil["sumber_per_bahan"]["ayam"]["sumber"] == "sigaokmas"
    assert hasil["sumber_per_bahan"]["coklat"]["sumber"] == "dapur"
    assert hasil["sumber_per_bahan"]["ayam"]["harga"] == hasil["prices"]["ayam"]
