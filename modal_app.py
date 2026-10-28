"""Bakpao.my.id — Autonomous Commerce & Kitchen Agent.
SATU app Modal berisi: web (FastAPI ASGI) + CPU (SAM 2.1 open-weights).
URL web: https://baiwormyid--bakpao.modal.run
JANGAN deploy/run/serve dari run ini (Run #3 yang deploy).
"""
import modal

APP_NAME = "bakpao-agent"

# Volume: data order (persisten lintas restart container)
data_volume = modal.Volume.from_name("bakpao-data", create_if_missing=True)
# Volume: cache bobot HF (hemat cold start)
hf_volume = modal.Volume.from_name("baiwor-hf-cache", create_if_missing=True)

# Secret: dibaca dari .env.modal (gitignored). Berisi MODEL_API_KEY + BASETEN_API_KEY.
# TIDAK memakai `modal secret create ... KEY=<nilai>` — nilai key akan masuk log.
api_secret = modal.Secret.from_dotenv(filename=".env.modal")

# ============================================================================
# WEB
# ============================================================================
web_image = (
    modal.Image.debian_slim(python_version="3.12")          # pin: wheel 3.14 belum ada
    .pip_install_from_requirements("requirements.txt")        # verified ADA di modal 1.6.3
    .add_local_dir("src", remote_path="/root/src", copy=True,  # .py + .html + .json ikut
                   ignore=["__pycache__"])
    .workdir("/root")                                        # "src/static" resolve relatif
)

app = modal.App(APP_NAME)


@app.function(
    image=web_image,
    secrets=[api_secret],
    volumes={"/data": data_volume},
    env={
        "DATA_DIR": "/data",
        "STORE_BASE_URL": "https://bakpao.my.id",
        "MODAL_WORKSPACE": "baiwormyid",
    },
    timeout=300,
    scaledown_window=300,      # web tidur setelah 5 mnt idle
    min_containers=0,
)
@modal.asgi_app(label="bakpao")   # -> https://baiwormyid--bakpao.modal.run
def web():
    # IMPORT DI DALAM BODY (bukan top-level) — top-level = ImportError saat deploy.
    from src.main import app as fastapi_app
    return fastapi_app


# ============================================================================
# GPU — SAM 2.1 (open-weights Meta, Apache-2.0, UNGATED)
# Dipanggil INTERNAL dari web: VisionService().segment.remote(payload)
# ============================================================================
cpu_image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install("torch", "torchvision",
                 index_url="https://download.pytorch.org/whl/cpu")
    .pip_install("transformers>=4.52", "pillow", "numpy")
    .workdir("/root")
)

MODEL_ID = "facebook/sam2.1-hiera-large"  # Ungated, Apache-2.0


@app.cls(
    image=cpu_image,
    cpu=8,
    memory=16384,
    volumes={"/root/.cache/huggingface": hf_volume},
    timeout=900,
    scaledown_window=60,
    min_containers=0,
)
class VisionService:
    @modal.enter()
    def setup_model(self):
        import time
        import torch
        from transformers import Sam2Model, Sam2Processor
        t0 = time.time()
        self.processor = Sam2Processor.from_pretrained(MODEL_ID)
        self.model = Sam2Model.from_pretrained(
            MODEL_ID, dtype=torch.float32).eval()
        self.load_seconds = round(time.time() - t0, 2)

    @modal.method()
    def segment(self, payload: dict) -> dict:
        """payload = {"image_b64": str, "points": [[x, y], ...]}."""
        import base64
        import io
        import time
        import torch
        from PIL import Image
        t0 = time.time()
        img = Image.open(
            io.BytesIO(base64.b64decode(payload["image_b64"]))).convert("RGB")
        w, h = img.size
        pts = payload.get("points") or [[w // 2, h // 2]]
        # nesting WAJIB 4 level: [image][object][point][x, y].
        inputs = self.processor(
            images=img, input_points=[[[p] for p in pts]],
            input_labels=[[[1] for _ in pts]], return_tensors="pt")
        with torch.no_grad():
            out = self.model(**inputs)
        # post_process_masks butuh original_sizes (dan reshaped_input_sizes).
        # Signature berbeda antar versi transformers -> coba berurutan.
        orig_sizes = inputs.get("original_sizes")
        reshaped = inputs.get("reshaped_input_sizes")
        masks_cpu = out.pred_masks.cpu()
        attempts = (
            ((masks_cpu, orig_sizes, reshaped), {"binarize": True}),
            ((masks_cpu, orig_sizes, reshaped), {}),
            ((masks_cpu, orig_sizes), {}),
        )
        full = None
        last_error = "signature post_process_masks tidak dikenal"
        for args, kwargs in attempts:
            try:
                full = self.processor.post_process_masks(*args, **kwargs)[0]
                break
            except TypeError as exc:
                last_error = str(exc)[:200]
                continue
            except Exception as exc:
                return {"ok": False, "error": "mask_postprocess_gagal",
                        "detail": str(exc)[:200]}
        if full is None:
            return {"ok": False, "error": "mask_postprocess_gagal",
                    "detail": last_error}
        objects = []
        for i in range(full.shape[0]):
            best = int(out.iou_scores[0, i].argmax())
            area = int((full[i, best] > 0.5).sum().item())
            import math
            objects.append({"area_px": area,
                            "iou": round(float(out.iou_scores[0, i, best]), 4),
                            "diameter_px": round(
                                2.0 * math.sqrt(area / math.pi), 1)})
        return {"ok": True, "model": MODEL_ID, "device": "cpu",
                "objects": objects, "image_px": [w, h],
                "infer_seconds": round(time.time() - t0, 2)}
