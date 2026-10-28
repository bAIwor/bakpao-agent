"""Layanan perhitungan HPP (Harga Pokok Produksi) dan rekomendasi harga.

Fungsi murni deterministik untuk efisiensi dan konsistensi operasional dapur.
"""
from __future__ import annotations

import math
from typing import Any


def hpp_per_biji(recipe: dict[str, Any], prices: dict[str, float]) -> dict[str, Any]:
    """Hitung HPP per biji bakpao berdasarkan takaran resep dan harga komoditas (Rp/kg).

    recipe: dict yang berisi 'ingredients' list dan 'overhead_ratio' (default 0.08).
    prices: dict harga per kg, misal {'terigu': 12500, 'ayam': 35000}.
    """
    ingredients = recipe.get("ingredients", [])
    overhead_ratio = float(recipe.get("overhead_ratio", 0.08))

    detail = []
    subtotal = 0.0

    for item in ingredients:
        gram = float(item.get("gram_per_biji", 0.0))
        key = item.get("key", "")
        name = item.get("name", key)
        price_per_kg = float(prices.get(key, 0.0))

        cost = (gram / 1000.0) * price_per_kg
        subtotal += cost

        detail.append({
            "name": name,
            "key": key,
            "gram": gram,
            "price_per_kg": int(round(price_per_kg)),
            "cost": round(cost, 2),
        })

    overhead = subtotal * overhead_ratio
    total_hpp = int(round(subtotal + overhead))

    # Guardrail: HPP tidak boleh bernilai negatif
    if total_hpp < 0:
        total_hpp = 0

    return {
        "hpp": total_hpp,
        "detail": detail,
        "subtotal": int(round(subtotal)),
        "overhead": int(round(overhead)),
        "total": total_hpp,
    }


def suggest_price(hpp: int, target_food_cost_pct: float = 0.30) -> dict[str, Any]:
    """Hitung harga jual yang disarankan dari HPP dan target rasio food-cost.

    Formula: raw_price = hpp / (1.0 - target_food_cost_pct), dibulatkan ke Rp 500 terdekat.
    """
    if hpp < 0:
        hpp = 0

    target = float(target_food_cost_pct)
    if target >= 1.0 or target <= 0.0:
        raw_price = hpp * 1.5
    else:
        raw_price = hpp / (1.0 - target)

    # Pembulatan ke Rp 500 terdekat
    price = int(round(raw_price / 500.0) * 500)

    # Guardrail: Harga saran tidak boleh di bawah HPP
    if price < hpp:
        price = int(math.ceil(hpp / 500.0) * 500)

    margin = price - hpp
    margin_pct = round((margin / price) * 100.0, 1) if price > 0 else 0.0
    food_cost_pct = round((hpp / price) * 100.0, 1) if price > 0 else 100.0

    warning = "food_cost_above_target" if food_cost_pct > 60.0 else None

    return {
        "price": price,
        "hpp": hpp,
        "margin": margin,
        "margin_pct": margin_pct,
        "food_cost_pct": food_cost_pct,
        "warning": warning,
    }


def price_with_suffix(hpp: int, target_food_cost_pct: float = 0.30, suffix: int | None = None) -> int:
    """Harga saran yang dibulatkan ke Rp 500 terdekat ditambah suffix 3 digit."""
    base = suggest_price(hpp, target_food_cost_pct)["price"]
    if suffix is None:
        return base
    return base + int(suffix)


def calculate_catalog_hpp(recipes: dict[str, Any], prices: dict[str, float]) -> dict[str, Any]:
    """Hitung HPP dan harga saran untuk seluruh katalog resep."""
    result = {}
    for product_id, recipe in recipes.items():
        if product_id.startswith("_"):
            continue
        hpp_info = hpp_per_biji(recipe, prices)
        target_cost = recipe.get("target_food_cost_pct", 0.30)
        price_info = suggest_price(hpp_info["total"], target_cost)
        result[product_id] = {
            "name": recipe.get("name", product_id),
            "size": recipe.get("size", "reguler"),
            "target_price": recipe.get("target_price", price_info["price"]),
            "hpp": hpp_info["total"],
            "suggested_price": price_info["price"],
            "margin": price_info["margin"],
            "margin_pct": price_info["margin_pct"],
            "food_cost_pct": price_info["food_cost_pct"],
            "warning": price_info["warning"],
            "overhead": hpp_info["overhead"],
            "detail": hpp_info["detail"],
        }
    return result
