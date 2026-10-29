"""Unit test untuk agen penyesuaian harga dan validasi ketat (strict guardrails)."""
import asyncio
from unittest.mock import MagicMock

from src.services.pricing_agent import (
    evaluate_repricing,
    evaluate_repricing_deterministic,
    validate_agent_output,
)


def test_validate_agent_override_price_below_hpp():
    # Model nakal menyarankan harga di bawah HPP (misal saran 1000 padahal HPP 2500)
    mock_agent_data = {
        "per_item": [
            {
                "product_id": "bakpao-ayam",
                "hpp_old": 2000,
                "hpp_new": 2500,
                "hpp_change_pct": 25.0,
                "current_price": 3000,
                "suggested_price": 1000,  # Pelanggaran: di bawah HPP!
                "action": "REPRICE_UP",
                "reason": "Salah saran",
            }
        ],
        "vendor_alert": "Pemberitahuan",
        "summary": "Ringkasan",
    }
    context = {
        "bakpao-ayam": {
            "hpp_new": 2500,
            "hpp_old": 2000,
            "hpp_change_pct": 25.0,
            "current_price": 3000,
            "deterministic_price": 3500,
        }
    }
    result, overrides = validate_agent_output(mock_agent_data, context)
    assert result["agent_override"] is True
    assert len(overrides) >= 1
    # Harga harus di-override ke deterministik
    assert result["per_item"][0]["suggested_price"] == 3500


def test_validate_agent_override_reprice_up_under_threshold():
    # Model memberikan aksi REPRICE_UP padahal kenaikan HPP hanya 1.2% (<= 3.0%)
    mock_agent_data = {
        "per_item": [
            {
                "product_id": "bakpao-coklat",
                "hpp_old": 2000,
                "hpp_new": 2024,
                "hpp_change_pct": 1.2,
                "current_price": 3000,
                "suggested_price": 3500,
                "action": "REPRICE_UP",  # Pelanggaran: kenaikan <= 3% dilarang naikkan harga
                "reason": "Mau untung lebih",
            }
        ],
        "vendor_alert": "Alert",
        "summary": "Summary",
    }
    context = {
        "bakpao-coklat": {
            "hpp_new": 2024,
            "hpp_old": 2000,
            "hpp_change_pct": 1.2,
            "current_price": 3000,
            "deterministic_price": 3000,
        }
    }
    result, overrides = validate_agent_output(mock_agent_data, context)
    assert result["agent_override"] is True
    assert result["per_item"][0]["action"] == "HOLD"
    assert result["per_item"][0]["suggested_price"] == 3000


def test_validate_agent_override_price_too_high():
    # Model menyarankan harga tidak wajar (> 2.5x HPP baru)
    mock_agent_data = {
        "per_item": [
            {
                "product_id": "bakpao-ayam",
                "hpp_old": 2000,
                "hpp_new": 2000,
                "hpp_change_pct": 0.0,
                "current_price": 3000,
                "suggested_price": 80000,  # Pelanggaran: ekstrem > 2.5x
                "action": "HOLD",
                "reason": "Mark up ekstrem",
            }
        ],
        "vendor_alert": "Alert",
        "summary": "Summary",
    }
    context = {
        "bakpao-ayam": {
            "hpp_new": 2000,
            "hpp_old": 2000,
            "hpp_change_pct": 0.0,
            "current_price": 3000,
            "deterministic_price": 3000,
        }
    }
    result, overrides = validate_agent_output(mock_agent_data, context)
    assert result["agent_override"] is True
    assert result["per_item"][0]["suggested_price"] == 3000


def test_validate_agent_hold_harga_lama_tidak_di_override():
    # Harga toko yang berjalan sudah di atas hpp_new * 2.5. Model memilih
    # mempertahankannya -> bukan pelanggaran, harga tidak boleh dipotong.
    mock_agent_data = {
        "per_item": [
            {
                "product_id": "bakpao-coklat",
                "hpp_old": 1272,
                "hpp_new": 1272,
                "hpp_change_pct": 0.0,
                "current_price": 3500,
                "suggested_price": 3500,
                "action": "HOLD",
                "reason": "HPP tidak berubah",
            }
        ],
        "vendor_alert": "",
        "summary": "Tidak ada perubahan",
    }
    context = {
        "bakpao-coklat": {
            "hpp_new": 1272,
            "hpp_old": 1272,
            "hpp_change_pct": 0.0,
            "current_price": 3500,
            "deterministic_price": 2000,
        }
    }
    result, overrides = validate_agent_output(mock_agent_data, context)
    assert result["agent_override"] is False
    assert result["per_item"][0]["suggested_price"] == 3500


def test_validate_agent_valid_accepted():
    # Model memberikan output valid dan logis
    mock_agent_data = {
        "per_item": [
            {
                "product_id": "bakpao-ayam",
                "hpp_old": 2000,
                "hpp_new": 2200,
                "hpp_change_pct": 10.0,
                "current_price": 3000,
                "suggested_price": 3500,
                "action": "REPRICE_UP",
                "reason": "Kenaikan HPP 10% di atas toleransi 3%",
            }
        ],
        "vendor_alert": "Pemberitahuan resmi ke supplier ayam",
        "summary": "1 produk disesuaikan harganya",
    }
    context = {
        "bakpao-ayam": {
            "hpp_new": 2200,
            "hpp_old": 2000,
            "hpp_change_pct": 10.0,
            "current_price": 3000,
            "deterministic_price": 3500,
        }
    }
    result, overrides = validate_agent_output(mock_agent_data, context)
    assert result["agent_override"] is False
    assert len(overrides) == 0
    assert result["per_item"][0]["action"] == "REPRICE_UP"
    assert result["per_item"][0]["suggested_price"] == 3500


def test_evaluate_repricing_deterministic():
    recipes = {
        "bakpao-ayam": {
            "name": "Bakpao Ayam",
            "overhead_ratio": 0.08,
            "target_price": 3000,
            "target_food_cost_pct": 0.30,
            "ingredients": [{"key": "terigu", "gram_per_biji": 100}],
        }
    }
    yesterday = {"terigu": 10000}  # HPP = 1000 + 80 = 1080
    today = {"terigu": 15000}      # HPP = 1500 + 120 = 1620 (naik 50%)

    res = evaluate_repricing_deterministic(recipes, today, yesterday)
    assert res["per_item"][0]["action"] == "REPRICE_UP"
    assert res["per_item"][0]["hpp_change_pct"] > 3.0
    assert "Pemberitahuan Dapur" in res["vendor_alert"]


def test_evaluate_repricing_status_not_completed_falls_back():
    recipes = {
        "bakpao-ayam": {
            "name": "Bakpao Ayam",
            "overhead_ratio": 0.08,
            "target_price": 3000,
            "target_food_cost_pct": 0.30,
            "ingredients": [{"key": "terigu", "gram_per_biji": 50}],
        }
    }
    yesterday = {"terigu": 10000}
    today = {"terigu": 10000}

    # Mock client yang gagal atau return status != completed
    mock_client = MagicMock()
    mock_client.responses.return_value = {"status": "failed", "error": "Internal Error"}

    res = asyncio.run(evaluate_repricing(recipes, today, yesterday, client=mock_client))
    # Harus fallback ke evaluasi deterministik tanpa crash
    assert len(res["per_item"]) == 1
    assert res["per_item"][0]["action"] == "HOLD"


def test_kontrak_keputusan_untuk_panel_simulasi():
    # Panel /dapur me-render decision apa adanya: 6 item dgn 8 kunci,
    # summary + vendor_alert string, tanpa override pada lonjakan wajar.
    import json
    from pathlib import Path
    recipes = json.loads(
        (Path(__file__).resolve().parents[1] / "src" / "data"
         / "recipes.json").read_text(encoding="utf-8"))
    kunci = set()
    for pid, rec in recipes.items():
        if pid.startswith("_"):
            continue
        kunci.update(i.get("key", "") for i in rec.get("ingredients", []))
    kemarin = {k: 20000 for k in kunci if k}
    kemarin["ayam"] = 40000
    hari_ini = dict(kemarin, ayam=50000)
    res = evaluate_repricing_deterministic(recipes, hari_ini, kemarin)
    assert len(res["per_item"]) == 6
    for it in res["per_item"]:
        assert set(it) == {"product_id", "hpp_old", "hpp_new",
                           "hpp_change_pct", "current_price",
                           "suggested_price", "action", "reason"}
        assert it["action"] in ("REPRICE_UP", "HOLD", "REVIEW_SUPPLIER")
        assert it["suggested_price"] >= it["hpp_new"]
    assert isinstance(res["summary"], str) and res["summary"]
    assert isinstance(res["vendor_alert"], str) and res["vendor_alert"]
    assert res["agent_override"] is False
    assert res["overrides"] == []
