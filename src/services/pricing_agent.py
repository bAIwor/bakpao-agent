"""Agen penyesuaian harga (repricing) dengan fondasi penalaran model cerdas.

Prinsip:
- LLM digunakan untuk penalaran keputusan bisnis dan narasi komunikasi vendor.
- Perhitungan HPP dan batas harga dilakukan secara deterministik oleh sistem.
- Output LLM divalidasi ketat (strict guardrails) dengan mekanisme override otomatis.
"""
from __future__ import annotations

import json
from typing import Any

from src.core.config import get_settings
from src.core.guardrail import GUARDRAIL_SYSTEM
from src.services.meta_client import MetaClient
from src.services.pricing import hpp_per_biji, suggest_price

REPRICING_SCHEMA = {
    "type": "object",
    "properties": {
        "per_item": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "string"},
                    "hpp_old": {"type": "integer"},
                    "hpp_new": {"type": "integer"},
                    "hpp_change_pct": {"type": "number"},
                    "current_price": {"type": "integer"},
                    "suggested_price": {"type": "integer"},
                    "action": {"type": "string", "enum": ["REPRICE_UP", "HOLD", "REVIEW_SUPPLIER"]},
                    "reason": {"type": "string"},
                },
                "required": [
                    "product_id",
                    "hpp_old",
                    "hpp_new",
                    "hpp_change_pct",
                    "current_price",
                    "suggested_price",
                    "action",
                    "reason",
                ],
                "additionalProperties": False,
            },
        },
        "vendor_alert": {"type": "string"},
        "summary": {"type": "string"},
    },
    "required": ["per_item", "vendor_alert", "summary"],
    "additionalProperties": False,
}

SYSTEM_INSTRUCTIONS = (
    f"{GUARDRAIL_SYSTEM}\n\n"
    "Tugas Anda: Membandingkan harga bahan pokok hari ini dengan kemarin, "
    "mengevaluasi dampaknya terhadap HPP, dan memutuskan tindakan repricing.\n\n"
    "ATURAN OPERASIONAL:\n"
    "1. Gunakan nilai HPP yang sudah dihitung oleh sistem. JANGAN menghitung ulang rumus.\n"
    "2. Berikan aksi REPRICE_UP hanya jika hpp_change_pct > 3.0%.\n"
    "3. Jika kenaikan HPP <= 3.0%, aksi wajib bernilai HOLD (tidak perlu repricing).\n"
    "4. Jika kenaikan bahan sangat tinggi (> 10%) tapi harga jual tidak dinaikkan, "
    "   pertimbangkan opsi REVIEW_SUPPLIER.\n"
    "5. DILARANG menyarankan harga jual yang lebih rendah dari HPP baru.\n"
    "6. Balas HANYA dalam format JSON valid sesuai schema yang ditentukan."
)


def validate_agent_output(agent_data: dict[str, Any], items_context: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Validasi ketat hasil rekomendasi model.

    Aturan:
    - suggested_price harus >= hpp_new.
    - action REPRICE_UP hanya boleh jika hpp_change_pct > 3.0.
    - suggested_price harus dalam rentang [hpp_new, hpp_new * 2.5].
    - Bila ada pelanggaran, override ke hasil perhitungan deterministik.
    """
    overrides: list[str] = []
    sanitized_items = []

    for item in agent_data.get("per_item", []):
        pid = item.get("product_id", "")
        ctx = items_context.get(pid, {})
        hpp_new = ctx.get("hpp_new", item.get("hpp_new", 0))
        hpp_old = ctx.get("hpp_old", item.get("hpp_old", 0))
        hpp_change = ctx.get("hpp_change_pct", item.get("hpp_change_pct", 0.0))
        current_price = ctx.get("current_price", item.get("current_price", 0))

        suggested = int(item.get("suggested_price", current_price))
        action = item.get("action", "HOLD")
        reason = item.get("reason", "")

        deterministic_price = ctx.get("deterministic_price", suggest_price(hpp_new)["price"])

        # Aturan 1: suggested_price tidak boleh di bawah HPP
        if suggested < hpp_new:
            overrides.append(
                f"Item {pid}: suggested_price Rp {suggested} < HPP Rp {hpp_new} -> di-override ke Rp {deterministic_price}"
            )
            suggested = deterministic_price

        # Aturan 2: REPRICE_UP hanya sah jika HPP naik > 3.0%
        if action == "REPRICE_UP" and hpp_change <= 3.0:
            overrides.append(
                f"Item {pid}: action REPRICE_UP ditolak karena kenaikan HPP ({hpp_change:.1f}%) <= 3.0% -> di-override ke HOLD"
            )
            action = "HOLD"
            suggested = current_price

        # Aturan 3: suggested_price harus dalam rentang wajar [hpp_new, hpp_new * 2.5]
        max_allowed = int(hpp_new * 2.5)
        if suggested > max_allowed:
            overrides.append(
                f"Item {pid}: suggested_price Rp {suggested} > batas atas Rp {max_allowed} -> di-override ke Rp {deterministic_price}"
            )
            suggested = deterministic_price

        sanitized_items.append({
            "product_id": pid,
            "hpp_old": hpp_old,
            "hpp_new": hpp_new,
            "hpp_change_pct": hpp_change,
            "current_price": current_price,
            "suggested_price": suggested,
            "action": action,
            "reason": reason,
        })

    result = {
        "per_item": sanitized_items,
        "vendor_alert": agent_data.get("vendor_alert", ""),
        "summary": agent_data.get("summary", ""),
        "agent_override": len(overrides) > 0,
        "overrides": overrides,
    }
    return result, overrides


def evaluate_repricing_deterministic(
    recipes: dict[str, Any],
    prices_today: dict[str, float],
    prices_yesterday: dict[str, float],
) -> dict[str, Any]:
    """Evaluasi repricing murni deterministik (fallback mandiri saat jaringan offline)."""
    per_item = []
    items_needing_reprice = []

    for pid, rec in recipes.items():
        if pid.startswith("_"):
            continue
        old_hpp = hpp_per_biji(rec, prices_yesterday)["total"]
        new_hpp = hpp_per_biji(rec, prices_today)["total"]
        diff = new_hpp - old_hpp
        change_pct = round((diff / old_hpp * 100.0), 2) if old_hpp > 0 else 0.0

        target_cost = rec.get("target_food_cost_pct", 0.30)
        curr_price = rec.get("target_price", 3000)
        det_price = suggest_price(new_hpp, target_cost)["price"]

        if change_pct > 3.0:
            action = "REPRICE_UP"
            suggested = det_price
            reason = f"Kenaikan HPP sebesar {change_pct:.1f}% melebihi ambang batas toleransi 3%."
            items_needing_reprice.append(rec.get("name", pid))
        else:
            action = "HOLD"
            suggested = curr_price
            reason = f"Perubahan HPP sebesar {change_pct:.1f}% masih dalam batas aman (<= 3%)."

        per_item.append({
            "product_id": pid,
            "hpp_old": old_hpp,
            "hpp_new": new_hpp,
            "hpp_change_pct": change_pct,
            "current_price": curr_price,
            "suggested_price": suggested,
            "action": action,
            "reason": reason,
        })

    if items_needing_reprice:
        vendor_alert = (
            f"Pemberitahuan Dapur bAIwor: Terdapat lonjakan harga bahan baku untuk "
            f"{', '.join(items_needing_reprice)}. Diharapkan konfirmasi kuotasi supplier."
        )
        summary = f"{len(items_needing_reprice)} produk memerlukan penyesuaian harga jual."
    else:
        vendor_alert = "Harga bahan pokok stabil. Operasional berjalan normal tanpa perubahan tarif."
        summary = "Seluruh produk dalam kondisi harga stabil."

    return {
        "per_item": per_item,
        "vendor_alert": vendor_alert,
        "summary": summary,
        "agent_override": False,
        "overrides": [],
    }


async def evaluate_repricing(
    recipes: dict[str, Any],
    prices_today: dict[str, float],
    prices_yesterday: dict[str, float],
    client: MetaClient | None = None,
) -> dict[str, Any]:
    """Jalankan evaluasi repricing cerdas menggunakan model muse-spark-1.3."""
    # 1. Siapkan konteks komputasi deterministik terlebih dahulu
    items_context = {}
    calculation_summary = []

    for pid, rec in recipes.items():
        if pid.startswith("_"):
            continue
        old_hpp = hpp_per_biji(rec, prices_yesterday)["total"]
        new_hpp = hpp_per_biji(rec, prices_today)["total"]
        diff = new_hpp - old_hpp
        change_pct = round((diff / old_hpp * 100.0), 2) if old_hpp > 0 else 0.0

        target_cost = rec.get("target_food_cost_pct", 0.30)
        curr_price = rec.get("target_price", 3000)
        det_price = suggest_price(new_hpp, target_cost)["price"]

        items_context[pid] = {
            "name": rec.get("name", pid),
            "hpp_old": old_hpp,
            "hpp_new": new_hpp,
            "hpp_change_pct": change_pct,
            "current_price": curr_price,
            "deterministic_price": det_price,
        }
        calculation_summary.append(items_context[pid])

    # 2. Cek apakah ada API client atau kunci API
    cfg = get_settings()
    api_key = cfg.MODEL_API_KEY
    if not api_key:
        return evaluate_repricing_deterministic(recipes, prices_today, prices_yesterday)

    # 3. Bentuk payload inferensi Meta Model API (muse-spark-1.3)
    cli = client or MetaClient(api_key=api_key)
    prompt_payload = {
        "summary_perhitungan_hpp": calculation_summary,
        "harga_bahan_kemarin": prices_yesterday,
        "harga_bahan_hari_ini": prices_today,
    }

    body = {
        "model": "muse-spark-1.3",
        "instructions": SYSTEM_INSTRUCTIONS,
        "input": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": json.dumps(prompt_payload, ensure_ascii=False),
                    }
                ],
            }
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "repricing_decision",
                "strict": True,
                "schema": REPRICING_SCHEMA,
            }
        },
        "max_output_tokens": 4096,
        "reasoning": {"effort": "low"},
        "temperature": 0.0,
    }

    try:
        resp = cli.responses(body, timeout=60.0)
        if resp.get("status") != "completed":
            return evaluate_repricing_deterministic(recipes, prices_today, prices_yesterday)

        raw_text = cli.extract_text(resp)
        parsed = json.loads(raw_text)

        # 4. Validasi ketat terhadap output model LLM
        validated, _ = validate_agent_output(parsed, items_context)
        return validated
    except Exception:
        # Fallback deterministik jika pemanggilan LLM gagal
        return evaluate_repricing_deterministic(recipes, prices_today, prices_yesterday)
