"""Test geometri vision + endpoint measure tanpa Modal."""
import asyncio
import io
import json
from pathlib import Path

from fastapi import Response

from src.api import routes as routes_mod
from src.services import geometry as geo
from src.services import vision_client as vc

FIX = Path(__file__).resolve().parents[0] / "fixtures" / "vision"


def test_scale_exact():
    r = geo.scale_from_references({"10cm": 300.0, "20cm": 600.0},
                                  {"10cm": 10.0, "20cm": 20.0})
    assert r["px_per_cm"] == 30.0 and r["spread_pct"] == 0
    assert r["confidence"] == "tinggi" and r["warnings"] == []


def test_scale_inconsistent_warns():
    r = geo.scale_from_references({"a": 300.0, "b": 540.0},
                                  {"a": 10.0, "b": 20.0})
    assert r["confidence"] == "rendah" and len(r["warnings"]) == 1


def test_mask_to_metrics():
    m = geo.mask_to_metrics(11310, 30.0)
    assert abs(m["diameter_cm"] - 4.0) <= 0.05


def test_measure_uniform_no_reject():
    masks = [{"area_px": 11310, "iou": 0.9} for _ in range(3)]
    r = geo.measure_objects(masks, 30.0)
    assert r["ok"] and r["reject_count"] == 0 and r["count"] == 3
    assert r["diameter_cm_range"][0] <= r["median_diameter_cm"] \
        <= r["diameter_cm_range"][1]


def test_measure_small_is_reject():
    masks = [{"area_px": 11310, "iou": 0.9},
             {"area_px": 11310, "iou": 0.9},
             {"area_px": 2827, "iou": 0.5}]
    r = geo.measure_objects(masks, 30.0)
    assert r["reject_count"] == 1
    assert abs(r["reject_rate_pct"] - 33.3) < 0.1


def test_measure_empty():
    r = geo.measure_objects([], 30.0)
    assert r["ok"] is False and r["error"] == "tidak_ada_objek"


def test_measure_image_no_modal(monkeypatch):
    import sys
    import types

    def boom(*a, **k):
        raise RuntimeError("jaringan putus")

    fake = types.SimpleNamespace(
        VisionService=lambda: types.SimpleNamespace(
            segment=types.SimpleNamespace(remote=boom)))
    monkeypatch.setitem(sys.modules, "modal_app", fake)
    r = asyncio.run(vc.measure_image(b"xxx", [[1, 1]]))
    assert r["error"] == "vision_tidak_tersedia"


def _b64(path):
    import base64
    return base64.b64encode(Path(path).read_bytes()).decode()


def test_endpoint_no_modal(monkeypatch):
    async def fake_measure(image_bytes, points=None):
        return {"ok": False, "error": "vision_tidak_tersedia",
                "detail": "tiruan"}

    monkeypatch.setattr(routes_mod, "measure_image", fake_measure)
    body = routes_mod.VisionMeasureBody(
        image_b64=_b64(FIX / "tray_3_bakpao.png"), points=[[200, 250]])
    resp = routes_mod.vision_measure(body, Response())
    assert resp["ok"] is False
    assert resp["error"] == "vision_tidak_tersedia"


def test_fixtures_match_ground_truth():
    truth = json.loads((FIX / "ground_truth.json").read_text(
        encoding="utf-8"))
    assert truth["px_per_cm"] == 30.0
    for name in ("tray_3_bakpao.png", "tray_1_reject.png",
                 "tray_empty.png"):
        assert (FIX / name).is_file()
    assert truth["tray_1_reject.png"]["reject_count"] == 1

    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (300, 300), "white").save(buf, format="PNG")
    assert len(buf.getvalue()) > 100
