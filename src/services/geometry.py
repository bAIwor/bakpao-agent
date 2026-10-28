"""Geometri vision: fungsi murni, tanpa SAM, tanpa jaringan.

Aturan angka (spesifikasi Task 2):
- spread_pct = selisih relatif px_per_cm antar garis referensi.
  > 5% -> confidence 'rendah' + warnings wajib ada.
- Selalu sertakan diameter_cm_range (min-max), jangan satu angka presisi.
- Reject = luas < 55% atau > 145% dari luas median.
- Tanpa objek -> {"ok": False, "error": "tidak_ada_objek"}.
"""
import math
import statistics


def scale_from_references(ref_px: dict, ref_cm: dict) -> dict:
    """Hitung skala px/cm dari garis referensi yang diketahui jaraknya.

    ref_px={'garis_10cm': 300.0, 'garis_20cm': 600.0}
    ref_cm={'garis_10cm': 10.0, 'garis_20cm': 20.0}
    """
    ratios = []
    for key, cm in ref_cm.items():
        if key not in ref_px or not cm:
            continue
        ratios.append(float(ref_px[key]) / float(cm))
    if not ratios:
        return {"ok": False, "error": "acuan_tidak_lengkap",
                "confidence": "rendah", "warnings": ["tidak ada garis acuan"]}
    mean = sum(ratios) / len(ratios)
    spread = (max(ratios) - min(ratios)) / mean * 100.0 if mean else 0.0
    if spread > 5.0:
        confidence, warnings = "rendah", [
            f"selisih skala antar garis {spread:.1f}% (> 5%)"]
    elif spread > 1.0:
        confidence, warnings = "sedang", []
    else:
        confidence, warnings = "tinggi", []
    return {"px_per_cm": round(mean, 2), "spread_pct": round(spread, 2),
            "confidence": confidence, "warnings": warnings}


def mask_to_metrics(mask_area_px: int, px_per_cm: float) -> dict:
    """Luas piksel -> diameter cm (dari luas, bukan bounding box)."""
    area_cm2 = mask_area_px / (px_per_cm * px_per_cm)
    diameter_cm = 2.0 * math.sqrt(area_cm2 / math.pi)
    return {"diameter_cm": round(diameter_cm, 2),
            "area_cm2": round(area_cm2, 2)}


def measure_objects(masks: list, px_per_cm: float) -> dict:
    """masks=[{'area_px':int,'iou':float}] -> ringkasan + rentang + reject."""
    if not masks:
        return {"ok": False, "error": "tidak_ada_objek"}
    areas = [int(m["area_px"]) for m in masks]
    median_area = statistics.median(areas)
    objects = []
    for m in masks:
        met = mask_to_metrics(int(m["area_px"]), px_per_cm)
        ratio = (m["area_px"] / median_area) if median_area else 0.0
        status = "REJECT" if (ratio < 0.55 or ratio > 1.45) else "LAYAK"
        objects.append({**met, "iou": float(m.get("iou", 0.0)),
                        "status": status})
    diameters = [o["diameter_cm"] for o in objects]
    rejects = sum(1 for o in objects if o["status"] == "REJECT")
    return {"ok": True, "objects": objects, "count": len(objects),
            "median_diameter_cm": round(statistics.median(diameters), 2),
            "diameter_cm_range": [round(min(diameters), 2),
                                  round(max(diameters), 2)],
            "reject_count": rejects,
            "reject_rate_pct": round(rejects / len(objects) * 100.0, 1)}
