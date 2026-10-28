"""Wrapper Meta Model API (dipakai Task 3 & 4). Task 1: nol panggilan.

Aturan: max_output_tokens >= 2048; teks dibaca dari output[].content[].text.
"""
import httpx

from src.core.config import get_settings


class MetaClient:
    def __init__(self, api_key: str = "", base_url: str = ""):
        cfg = get_settings()
        self.api_key = api_key or cfg.MODEL_API_KEY
        self.base_url = (base_url or cfg.META_API_BASE_URL).rstrip("/")

    def responses(self, payload: dict, timeout: float = 120.0) -> dict:
        """POST /responses. Tidak dipanggil saat import."""
        r = httpx.post(self.base_url + "/responses", json=payload,
                       headers={"Authorization": "Bearer " + self.api_key},
                       timeout=timeout)
        r.raise_for_status()
        return r.json()

    @staticmethod
    def extract_text(resp: dict) -> str:
        for item in resp.get("output", []):
            if item.get("type") == "message":
                for c in item.get("content", []):
                    if c.get("text"):
                        return c["text"]
        return ""


def build_payload(model: str, instructions: str, text: str,
                  effort: str = "low", max_tokens: int = 4096) -> dict:
    return {"model": model, "instructions": instructions,
            "input": [{"role": "user", "content": [
                {"type": "input_text", "text": text}]}],
            "max_output_tokens": max_tokens,
            "reasoning": {"effort": effort}, "temperature": 0.0}
