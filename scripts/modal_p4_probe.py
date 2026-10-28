"""P4 PREFLIGHT — SAM 2.1 open-weights di Modal T4 (sementara, pra-Task 2).

App terpisah "bakpao-preflight" supaya tidak bentrok dengan deploy Task 1.
Aturan: gpu="T4", scaledown_window=60 (nama param baru),
modal.App, volume cache bobot, min_containers=0.

Jalankan:  python -m modal run scripts/modal_p4_probe.py
Output: JSON {mask_ok, load_seconds, inference_seconds, usd_per_image}.
"""

import base64
import io
import json
import time

import modal

app = modal.App("bakpao-preflight")
hf_volume = modal.Volume.from_name("baiwor-hf-cache", create_if_missing=True)

gpu_image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install("torch", "torchvision",
                 index_url="https://download.pytorch.org/whl/cu124")
    .pip_install("transformers>=4.48", "pillow", "numpy")
)

MODEL_ID = "facebook/sam2.1-hiera-large"  # UNGATED, Apache-2.0
T4_USD_PER_HOUR = 0.59


@app.cls(gpu="T4", image=gpu_image,
         volumes={"/root/.cache/huggingface": hf_volume},
         scaledown_window=60, timeout=300, min_containers=0)
class Probe:
    @modal.enter()
    def setup(self):
        import torch
        from transformers import Sam2Model, Sam2Processor
        t0 = time.time()
        self.processor = Sam2Processor.from_pretrained(MODEL_ID)
        self.model = Sam2Model.from_pretrained(
            MODEL_ID, dtype=torch.float16).to("cuda").eval()
        self.load_seconds = round(time.time() - t0, 1)

    @modal.method()
    def segment(self, payload: dict) -> dict:
        import torch
        from PIL import Image
        t0 = time.time()
        img = Image.open(
            io.BytesIO(base64.b64decode(payload["image_b64"]))).convert("RGB")
        w, h = img.size
        inputs = self.processor(
            images=img, input_points=[[[w // 2, h // 2]]],
            input_labels=[[1]], return_tensors="pt")
        for k, v in inputs.items():
            try:
                inputs[k] = v.to("cuda", dtype=torch.float16) \
                    if v.is_floating_point() else v.to("cuda")
            except Exception:
                pass
        with torch.no_grad():
            out = self.model(**inputs)
        masks = out.pred_masks  # [1, 1, n, H, W]
        import torch as _t
        m = (masks[0, 0, 0].float().mean().item())
        iou = out.iou_scores[0, 0, 0].tolist()
        infer = round(time.time() - t0, 2)
        return {"ok": True, "model": MODEL_ID, "device": "cuda",
                "load_seconds": self.load_seconds,
                "inference_seconds": infer,
                "mask_mean": round(m, 4), "iou": iou,
                "usd_per_image": round(infer / 3600 * T4_USD_PER_HOUR, 5)}


@app.local_entrypoint()
def main():
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (600, 450), (120, 120, 120))
    d = ImageDraw.Draw(img)
    for cx in (150, 300, 450):
        for cy in (150, 300):
            d.ellipse([cx - 60, cy - 60, cx + 60, cy + 60],
                      fill=(210, 170, 120), outline=(90, 60, 30), width=3)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    t0 = time.time()
    res = Probe().segment.remote({"image_b64": b64})
    res["wall_seconds"] = round(time.time() - t0, 1)
    print(json.dumps(res, indent=1))
