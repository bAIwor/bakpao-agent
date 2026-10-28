"""Unit test untuk jembatan data harga pangan SIGAOKMAS Banyumas."""
from src.services.commodity_prices import fetch_commodity_prices


def test_fetch_commodity_prices_benchmark_cache():
    # Mengambil data harga komoditas pasar
    res = fetch_commodity_prices()
    assert res["ok"] is True
    assert "prices" in res
    prices = res["prices"]

    # Cek komoditas pokok bakpao tersedia
    assert "terigu" in prices
    assert "ayam" in prices
    assert "gula" in prices
    assert prices["terigu"] > 0
    assert prices["ayam"] > 0

    # Pastikan sumber dan tanggal tercatat jelas
    assert "sumber" in res
    assert "tanggal" in res


def test_fetch_commodity_prices_stale_detection():
    # Jika dipanggil dengan tanggal masa depan, status cache terdeteksi stale
    future_date = "2029-01-01"
    res = fetch_commodity_prices(tanggal=future_date)
    assert res["ok"] is True
    assert res["stale"] is True


def test_no_cache_returns_error_gracefully(monkeypatch):
    import src.services.sigaokmas_bridge as bridge

    # Mock bila cache dan preflight tidak ada
    monkeypatch.setattr(bridge, "_read_cache", lambda: None)
    monkeypatch.setattr(bridge, "_read_preflight", lambda: None)

    res = bridge.fetch_commodity_prices()
    assert res["ok"] is False
    assert res["error"] == "price_source_unavailable"
