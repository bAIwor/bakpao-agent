"""Klien vision: FastAPI -> VisionService Modal (internal .remote()).

Import modal_app DILAKUKAN di dalam fungsi supaya uvicorn lokal
tidak butuh modal saat start. Kalau Modal gagal -> dict ok:false,
JANGAN melempar exception.
"""
import base64


async def measure_image(image_bytes: bytes,
                        points: list | None = None) -> dict:
    try:
        from modal_app import VisionService
    except Exception as e:
        return {"ok": False, "error": "vision_tidak_tersedia",
                "detail": f"import gagal: {type(e).__name__}"}
    try:
        payload = {"image_b64": base64.b64encode(image_bytes).decode(),
                   "points": points}
        res = VisionService().segment.remote(payload)
        return dict(res)
    except Exception as e:
        return {"ok": False, "error": "vision_tidak_tersedia",
                "detail": str(e)[:200]}
