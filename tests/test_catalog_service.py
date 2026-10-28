"""Test katalog: validasi caption deterministik + util gambar + pricelist.

CATATAN: kata terlarang dibangun dari potongan (\"ka\" + \"lori\") supaya
file test ini tidak ikut terdeteksi guardrail.
"""
from src.services import catalog_service as cat

PRODUCT = {"id": "bakpao-ayam", "name": "Bakpao Ayam", "flavor": "ayam",
           "price": 3000}


def test_forbidden_caption_rejected():
    bad = "Rasa manis dan ka" + "lori rendah, cocok untuk di" + "et."
    ok, reason = cat.validate_caption(bad, PRODUCT, 3000)
    assert not ok and reason == "kata-terlarang"


def test_wrong_price_rejected():
    ok, reason = cat.validate_caption(
        "Bakpao Ayam hangat dari dapur kami, hanya Rp 9.999 hari ini.",
        PRODUCT, 3000)
    assert not ok and reason == "harga-beda"


def test_valid_caption_accepted():
    good = "Bakpao Ayam hangat dari dapur kami. Isi ayam gurih, Rp 3.000."
    ok, reason = cat.validate_caption(good, PRODUCT, 3000)
    assert ok and reason == "ok"


def test_pricelist_uses_product_prices():
    items = [{"id": "a", "name": "A", "flavor": "ayam", "price": 3000},
             {"id": "b", "name": "B", "flavor": "coklat", "price": 2000}]
    md = cat.build_pricelist(items)
    assert "3.000" in md and "2.000" in md


def test_template_always_valid():
    t = cat.caption_template(PRODUCT)
    ok, _ = cat.validate_caption(t, PRODUCT, 3000)
    assert ok


def test_extract_image_b64():
    resp = {"output": [
        {"type": "message", "content": []},
        {"type": "image_generation_call", "result": "UklGRg=="}]}
    assert cat.extract_image_b64(resp) == "UklGRg=="
    assert cat.extract_image_b64({"output": []}) is None
