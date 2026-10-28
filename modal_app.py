"""Bakpao.my.id — Autonomous Commerce & Kitchen Agent.
SATU app Modal berisi: web (FastAPI ASGI) + GPU (SAM 2.1).
URL web: https://baiwormyid--bakpao.modal.run
Tulis file-nya saja di Task 1 — JANGAN deploy (deploy = Run #3).
"""
import modal

APP_NAME = "bakpao-agent"

# Volume: data order (persisten lintas restart container)
data_volume = modal.Volume.from_name("bakpao-data", create_if_missing=True)
# Volume: cache bobot HF (hemat cold start)
hf_volume = modal.Volume.from_name("baiwor-hf-cache", create_if_missing=True)

# Secret: kredensial API Meta (JANGAN pernah di-hardcode)
api_secret = modal.Secret.from_name("bakpao-secrets")

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
        "STORE_BASE_URL": "https://baiwormyid--bakpao.modal.run",
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
gpu_image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install("torch", "torchvision",
                 index_url="https://download.pytorch.org/whl/cu124")
    .pip_install("transformers>=4.48", "pillow", "numpy", "opencv-python-headless")
    .workdir("/root")
)

MODEL_ID = "facebook/sam2.1-hiera-large"


@app.cls(
    image=gpu_image,
    gpu="T4",
    volumes={"/root/.cache/huggingface": hf_volume},
    timeout=300,
    scaledown_window=60,            # nama param baru (yang lama deprecated)
    min_containers=0,
)
class VisionService:
    @modal.enter()
    def setup_model(self):
        import time
        import torch
        from transformers import Sam2Model, Sam2Processor
        t0 = time.time()
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.processor = Sam2Processor.from_pretrained(MODEL_ID)
        dtype = torch.float16 if self.device == "cuda" else torch.float32
        self.model = Sam2Model.from_pretrained(
            MODEL_ID, dtype=dtype).to(self.device).eval()
        self.load_seconds = round(time.time() - t0, 2)

    @modal.fastapi_endpoint(method="POST")
    def segment(self, payload: dict) -> dict:
        # Implementasi lengkap di Task 2 (BAKPAO_02_VISION_CALIBRATION.md).
        _ = payload
        return {"ok": False, "error": "vision_not_implemented"}
