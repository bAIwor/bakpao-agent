from fastapi.testclient import TestClient

import src.api.routes as routes
from src.main import app


def test_reprice_menggabungkan_kiriman_sebagian(monkeypatch):
    """Hanya ayam yang dikirim: bahan lain harus ikut dari harga acuan."""
    tertangkap = {}

    async def palsu(recipes, today, yesterday):
        tertangkap["today"] = today
        tertangkap["yesterday"] = yesterday
        return {"per_item": [], "vendor_alert": "", "summary": ""}

    monkeypatch.setattr(routes, "evaluate_repricing", palsu)
    resp = TestClient(app).post("/api/pricing/reprice",
                                json={"prices_today": {"ayam": 45000}})

    assert resp.status_code == 200
    assert tertangkap["today"]["ayam"] == 45000
    assert tertangkap["today"]["terigu"] > 0
    assert tertangkap["yesterday"]["ayam"] != 45000
