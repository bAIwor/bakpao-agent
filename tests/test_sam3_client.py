"""Test sam3_client: parser box murni + kontrak error tanpa jaringan."""
import asyncio

import pytest

from src.services import sam3_client as sam3
from src.services.sam3_client import box_diameter_px, parse_boxes

ONE = ("<0f>0<|box;x1=299;y1=148;x2=543;y2=361;w=600;h=450|>"
       "<|mask;x=0;y=0;data=214,245,~!!#stub|>")
TWO = ("<0f>0<|box;x1=299;y1=148;x2=543;y2=361;w=600;h=450|>"
       "<|mask;x=0;y=0;data=aaa|>"
       "<0f>1<|box;x1=10;y1=20;x2=110;y2=120;w=600;h=450|>"
       "<|mask;x=0;y=0;data=bbb|>")


def test_parse_satu_box_asli():
    boxes = parse_boxes(ONE)
    assert len(boxes) == 1
    b = boxes[0]
    assert (b["x1"], b["y1"], b["x2"], b["y2"]) == (299, 148, 543, 361)
    assert (b["w"], b["h"]) == (600, 450)
    assert b["x2"] == 543 and b["w"] == 600


def test_parse_dua_box_urutan_benar():
    boxes = parse_boxes(TWO)
    assert len(boxes) == 2
    assert boxes[0]["x1"] == 299
    assert boxes[1]["x1"] == 10
    assert boxes[1]["x2"] == 110


def test_parse_kosong():
    assert parse_boxes("") == []


def test_parse_tanpa_box():
    assert parse_boxes("<0f>0 tidak ada kotak") == []


def test_diameter_dari_sisi_kotak():
    # ((543-299) + (361-148)) / 2 = 228.5 (rumus di signature spec).
    assert box_diameter_px(
        {"x1": 299, "y1": 148, "x2": 543, "y2": 361}) == 228.5


def test_tanpa_api_key_tidak_melempar(monkeypatch):
    class Stub:
        MODEL_API_KEY = ""
        META_API_BASE_URL = "https://api.meta.ai/v1"
    monkeypatch.setattr(sam3, "get_settings", lambda: Stub())
    res = asyncio.run(sam3.segment_text_prompt(b"xxx", "steamed bun"))
    assert res["ok"] is False
    assert res["error"] == "api_key_tidak_ada"


def test_extract_text_gabung_semua_bagian():
    resp = {"output": [
        {"type": "message", "content": [{"text": "a"}, {"text": "b"}]},
        {"type": "other", "content": []}]}
    assert sam3.extract_text(resp) == "ab"
    assert sam3.extract_text({}) == ""
    assert sam3.extract_text({"output": [{"type": "message"}]}) == ""
