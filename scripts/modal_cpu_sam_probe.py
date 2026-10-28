"""Probe sekali pakai: SAM 2.1 di Modal CPU (tanpa payment method).

Pertanyaan yang dijawab: berapa detik load + inferensi per gambar di CPU?
Kalau <= ~30 s, demo live masih layak dan kita TIDAK butuh GPU sama sekali.

Jalankan:  python -m modal run scripts/modal_cpu_sam_probe.py
"""
import base64
import io
import json
import time

import modal

app = modal.App("bakpao-cpu-sam-probe")
hf_volume = modal.Volume.from_name("baiwor-hf-cache", create_if_missing=True)

cpu_image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install("torch", "torchvision", index_url="https://download.pytorch.org/whl/cpu")
    .pip_install("transformers>=4.52", "pillow", "numpy")
)

MODEL_ID = "facebook/sam2.1-hiera-large"


@app.cls(
    image=cpu_image,
    cpu=8,
    memory=16384,
    volumes={"/root/.cache/huggingface": hf_volume},
    timeout=900,
    scaledown_window=60,
    min_containers=0,
)
class CpuProbe:
    @modal.enter()
    def setup(self):
        import torch
        from transformers import Sam2Model, Sam2Processor

        t0 = time.time()
        self.processor = Sam2Processor.from_pretrained(MODEL_ID)
        self.model = Sam2Model.from_pretrained(MODEL_ID, dtype=torch.float32)
        self.model.eval()
        self.load_seconds = round(time.time() - t0, 1)
        self.torch = torch

    @modal.method()
    def segment(self, payload: dict) -> dict:
        import torch
        from PIL import Image

        img = Image.open(io.BytesIO(base64.b64decode(payload["image_b64"]))).convert("RGB")
        w, h = img.size
        pts = payload.get("points") or [[w // 2, h // 2]]
        # nesting WAJIB 4 level: [image][object][point][x, y]  (1 objek per titik)
        input_points = [[[p] for p in pts]]
        input_labels = [[[1] for _ in pts]]

        t0 = time.time()
        inputs = self.processor(images=img, input_points=input_points,
                                input_labels=input_labels, return_tensors="pt")
        with torch.no_grad():
            out = self.model(**inputs)
        infer = round(time.time() - t0, 2)

        masks = out.pred_masks          # [batch, objects, n_masks, H, W]
        iou = out.iou_scores            # [batch, objects, n_masks]
        best = int(iou[0, 0].argmax())
        m = masks[0, 0, best].float()
        area = int((m > 0.5).sum().item())
        return {
            "ok": True,
            "model": MODEL_ID,
            "device": "cpu",
            "image_px": [w, h],
            "points": pts,
            "objects": int(masks.shape[1]),
            "n_masks": int(masks.shape[2]),
            "mask_area_px": area,
            "mask_fraction": round(area / (w * h), 4),
            "iou_best": round(float(iou[0, 0, best]), 4),
            "load_seconds": self.load_seconds,
            "infer_seconds": infer,
            "total_seconds": round(self.load_seconds + infer, 1),
        }


@app.local_entrypoint()
def main():
    from PIL import Image, ImageDraw

    # 3 "bakpao" + papan referensi 10 cm / 20 cm (skala 30 px/cm)
    img = Image.new("RGB", (900, 600), (235, 228, 218))
    d = ImageDraw.Draw(img)
    for cx, cy in ((200, 250), (450, 250), (700, 250)):
        d.ellipse([cx - 60, cy - 60, cx + 60, cy + 60], fill=(205, 165, 115),
                  outline=(110, 70, 35), width=3)
    d.rectangle([100, 500, 400, 520], fill=(40, 40, 40))    # 10 cm
    d.rectangle([100, 545, 700, 565], fill=(40, 40, 40))    # 20 cm
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()

    t0 = time.time()
    res = CpuProbe().segment.remote({"image_b64": b64,
                                     "points": [[200, 250], [450, 250], [700, 250]]})
    res["wall_seconds"] = round(time.time() - t0, 1)
    print(json.dumps(res, indent=1))
