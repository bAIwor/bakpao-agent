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


def test_panel_mendapat_6_bahan_dari_eceran():
    # Kontrak untuk panel /dapur: 6 kunci, tiap entri punya median angka.
    idx = indeks_pasar()
    assert idx["ok"] is True
    assert set(idx["eceran"]) == {
        "terigu", "gula", "minyak", "ayam", "telur", "kacang_hijau"}
    for kunci, row in idx["eceran"].items():
        assert isinstance(row["median"], (int, float)), kunci
    assert idx["periode"]["dari"] <= idx["periode"]["sampai"]


def test_bahan_tanpa_harga_dapur_tetap_tampil():
    # Telur tidak ada di harga beli dapur -> tanpa entri bandingan.
    # Panel harus tetap menampilkannya (badge netral), bukan menghilangkannya.
    payload = fetch_commodity_prices()
    assert "telur" in payload["indeks_pasar"]["eceran"]
    assert "telur" not in payload["bandingan_pasar"]


def test_indeks_hilang_dilaporkan_bukan_dikarang(monkeypatch):
    # Tanpa berkas ringkasan -> ok False; panel /dapur tetap hidden.
    import src.services.sigaokmas as s
    monkeypatch.setattr(s, "_kandidat_ringkasan", lambda: [])
    idx = s.indeks_pasar()
    assert idx["ok"] is False
    assert idx["error"] == "indeks_belum_ada"


def test_hpp_memakai_eceran_sigaokmas():
    idx = indeks_pasar()
    hasil = harga_hpp({"ayam": 35000, "coklat": 38000}, faktor=1.0)

    # Ayam tercakup portal → diganti median eceran; coklat tidak → tetap dapur.
    assert hasil["prices"]["ayam"] == idx["eceran"]["ayam"]["median"]
    assert hasil["prices"]["coklat"] == 38000
    assert hasil["sumber_per_bahan"]["ayam"]["sumber"] == "sigaokmas"
    assert hasil["sumber_per_bahan"]["coklat"]["sumber"] == "dapur"
    assert hasil["sumber_per_bahan"]["ayam"]["harga"] == hasil["prices"]["ayam"]
