"""Unit test untuk mesin HPP dan rekomendasi harga deterministik."""
from src.services.pricing import (
    calculate_catalog_hpp,
    hpp_per_biji,
    price_with_suffix,
    suggest_price,
)


def test_hpp_per_biji_calculation():
    recipe = {
        "overhead_ratio": 0.08,
        "ingredients": [
            {"name": "Tepung", "key": "terigu", "gram_per_biji": 45},  # 45g @ 12000 = 540
            {"name": "Ayam", "key": "ayam", "gram_per_biji": 20},     # 20g @ 35000 = 700
        ],
    }
    prices = {"terigu": 12000, "ayam": 35000}
    res = hpp_per_biji(recipe, prices)

    # Subtotal = 540 + 700 = 1240
    # Overhead = 1240 * 0.08 = 99.2
    # Total HPP = round(1240 + 99.2) = 1339
    assert res["subtotal"] == 1240
    assert res["overhead"] == 99
    assert res["total"] == 1339
    assert res["hpp"] == 1339
    assert len(res["detail"]) == 2


def test_suggest_price_spec_exact():
    # Sesuai spesifikasi Task 3: hpp=3100, target=0.30 -> harga 4500
    res = suggest_price(hpp=3100, target_food_cost_pct=0.30)
    assert res["price"] == 4500
    assert res["hpp"] == 3100
    assert res["margin"] == 1400
    assert abs(res["margin_pct"] - 31.1) <= 0.1
    assert abs(res["food_cost_pct"] - 68.9) <= 0.1
    assert res["warning"] == "food_cost_above_target"


def test_suggest_price_food_cost_warning():
    # Food cost di atas 60% memicu warning
    res = suggest_price(hpp=2500, target_food_cost_pct=0.20)
    # 2500 / 0.8 = 3125 -> dibulatkan ke 500 = 3000
    # food_cost_pct = 2500 / 3000 = 83.3% -> di atas 60%
    assert res["warning"] == "food_cost_above_target"


def test_suggest_price_healthy_margin():
    # HPP 1000 dengan target 0.60 -> 1000 / 0.40 = 2500
    # food_cost_pct = 1000 / 2500 = 40% <= 60% -> tidak ada warning
    res = suggest_price(hpp=1000, target_food_cost_pct=0.60)
    assert res["price"] == 2500
    assert res["food_cost_pct"] == 40.0
    assert res["warning"] is None


def test_price_with_suffix():
    p = price_with_suffix(hpp=3100, target_food_cost_pct=0.30, suffix=789)
    assert p == 4500 + 789
    assert p == 5289


def test_guardrail_non_negative_hpp_and_price():
    # HPP negatif tidak boleh terjadi
    res = suggest_price(hpp=-500, target_food_cost_pct=0.30)
    assert res["hpp"] == 0
    assert res["price"] >= 0

    # Harga saran tidak boleh di bawah HPP
    res2 = suggest_price(hpp=3200, target_food_cost_pct=0.01)
    assert res2["price"] >= 3200


def test_calculate_catalog_hpp():
    recipes = {
        "bakpao-ayam": {
            "name": "Bakpao Ayam",
            "overhead_ratio": 0.08,
            "target_food_cost_pct": 0.30,
            "ingredients": [{"key": "terigu", "gram_per_biji": 50}],
        }
    }
    prices = {"terigu": 10000}
    cat = calculate_catalog_hpp(recipes, prices)
    assert "bakpao-ayam" in cat
    assert cat["bakpao-ayam"]["hpp"] > 0
    assert cat["bakpao-ayam"]["suggested_price"] >= cat["bakpao-ayam"]["hpp"]
