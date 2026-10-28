"""Bakpao.my.id — FastAPI app. CWD boleh repo root maupun /root (Modal)."""
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parent  # src/
DATA_DIR = Path(os.environ.get("DATA_DIR", "data"))
if not DATA_DIR.is_absolute():
    # Relatif terhadap CWD bila dijalankan dari repo root.
    DATA_DIR = (Path.cwd() / DATA_DIR).resolve()
DATA_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Bakpao.my.id")

from src.api.routes import router  # noqa: E402

app.include_router(router)
app.mount("/static", StaticFiles(directory=str(ROOT / "static")),
          name="static")
