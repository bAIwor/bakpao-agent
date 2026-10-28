"""Segmentasi frasa via sam-3.1 (jalur kedua, tanpa titik manual).

Kontrak terverifikasi: POST /v1/responses model sam-3.1, prompt frasa kata
benda konkret ("steamed bun", bukan "bakpao" -> 0 hasil). Teks lengkap ada
di output[].content[].text. Nol hasil = teks kosong = keluaran sah.

Hanya box yang di-parse; mask tidak didekode (dekoder resmi @meta-sam/parser
hanya TypeScript). Untuk bakpao yang mendekati lingkaran, sisi kotak cukup
untuk perkiraan diameter.
"""
import base64
import json
import re
import urllib.error
import urllib.request

from src.core.config import get_settings

MODEL = "sam-3.1"
BOX_RE = re.compile(
    r"<\|box;x1=(\d+);y1=(\d+);x2=(\d+);y2=(\d+);w=(\d+);h=(\d+)\|>")


def parse_boxes(text: str) -> list[dict]:
    """Ambil semua <|box;...|> dari keluaran sam-3.1. Fungsi murni."""
    out = []
    for m in BOX_RE.finditer(text or ""):
        x1, y1, x2, y2, w, h = (int(g) for g in m.groups())
        out.append({"x1": x1, "y1": y1, "x2": x2, "y2": y2,
                    "w": w, "h": h})
    return out


def box_diameter_px(box: dict) -> float:
    """Perkiraan diameter dari kotak: ((x2-x1) + (y2-y1)) / 2."""
    return ((box["x2"] - box["x1"]) + (box["y2"] - box["y1"])) / 2.0


def extract_text(resp: dict) -> str:
    """Gabung semua teks dari output[].content[].text."""
    chunks = []
    for item in resp.get("output", []):
        for part in item.get("content", []):
            if isinstance(part.get("text"), str):
                chunks.append(part["text"])
    return "".join(chunks)


async def segment_text_prompt(image_bytes: bytes, phrase: str) -> dict:
    """Panggil sam-3.1 dengan frasa. Gagal -> ok:False, tanpa crash."""
    cfg = get_settings()
    if not cfg.MODEL_API_KEY:
        return {"ok": False, "error": "api_key_tidak_ada"}
    payload = {
        "model": MODEL,
        "input": [{"type": "message", "role": "user", "content": [
            {"type": "input_text", "text": phrase},
            {"type": "input_image", "image_url":
             "data:image/jpeg;base64," + base64.b64encode(
                 image_bytes).decode()}]}],
        "max_output_tokens": 2048,
    }
    try:
        req = urllib.request.Request(
            cfg.META_API_BASE_URL.rstrip("/") + "/responses",
            data=json.dumps(payload).encode(),
            headers={"Authorization": "Bearer " + cfg.MODEL_API_KEY,
                     "Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=120.0) as r:
            resp = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return {"ok": False, "error": "sam3_gagal",
                "detail": str(e.code)}
    except Exception as e:
        return {"ok": False, "error": "sam3_gagal",
                "detail": type(e).__name__}
    text = extract_text(resp)
    if not text.strip():
        return {"ok": True, "boxes": [], "phrase": phrase,
                "raw_chars": 0, "error": None}
    return {"ok": True, "boxes": parse_boxes(text), "phrase": phrase,
            "raw_chars": len(text), "error": None}
