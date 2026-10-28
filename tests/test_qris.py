"""Test QRIS service: aritmetika, CRC16, render, 3 mode."""
import base64

from src.services.qris_service import (
    build_amount_with_suffix,
    build_dynamic_qris_payload,
    build_payment_url,
    build_qr_payload,
    build_qris_for_order,
    crc16_qris,
    format_rupiah,
    generate_order_code,
    generate_unique_suffix,
    load_static_payload,
    render_qr_base64,
)

MERCHANT = ("00020101021126570011ID.DANA.WWW011893600915303639133902090363913390303UMI"
            "51440014ID.CO.QRIS.WWW0215ID10266246738480303UMI5204899953033605802ID"
            "5925bAIwor Agentic Indonesia,6013Kab. Banyumas610553136630479A2")


def test_amount_with_suffix():
    assert build_amount_with_suffix(13000, 185) == 13185   # 13.000 + 185
    assert build_amount_with_suffix(3000, 100) == 3100


def test_format_rupiah():
    assert format_rupiah(13185) == "Rp 13.185"
    assert format_rupiah(3000) == "Rp 3.000"


def test_suffix_range():
    for _ in range(50):
        assert 100 <= generate_unique_suffix() <= 999


def test_order_code_shape():
    code = generate_order_code()
    assert code.startswith("BQ-") and len(code) == 9


def test_payment_url_has_code():
    assert build_payment_url("BQ-7F3K9A").endswith("/pay/BQ-7F3K9A")


def test_qr_payload_default_is_url():
    payload = build_qr_payload("http://localhost:8000/pay/BQ-7F3K9A")
    assert payload.startswith("http")


def test_render_qr_base64_is_png():
    raw = base64.b64decode(render_qr_base64("http://localhost:8000/pay/BQ-X"))
    assert raw[:8] == b"\x89PNG\r\n\x1a\n"


def test_static_payload_matches_merchant():
    assert load_static_payload() == MERCHANT
    assert len(load_static_payload()) == 205


def test_crc16_matches_embedded():
    # tag '6304' ikut dihitung; potong hanya 4 hex nilai CRC.
    assert crc16_qris(MERCHANT[:-4]) == "79A2"
    assert MERCHANT.endswith("630479A2")


def test_dynamic_payload_recomputes_crc():
    dyn = build_dynamic_qris_payload(MERCHANT, 13185)
    assert "010212" in dyn  # tag 01 statis(11) -> dinamis(12)
    assert "54" in dyn
    head, crc = dyn[:-4], dyn[-4:]
    assert head.endswith("6304")
    assert crc16_qris(head) == crc


def test_build_qris_for_order_modes(monkeypatch):
    import src.services.qris_service as qs
    monkeypatch.setattr(qs.get_settings(), "QR_MODE", "static")
    r = build_qris_for_order(13185, "BQ-AAAAAA", suffix=185)
    assert r["mode"] == "static" and r["payload"] == MERCHANT
    assert r["nominal"] == 13185 and r["suffix"] == 185
    monkeypatch.setattr(qs.get_settings(), "QR_MODE", "url")
    r = build_qris_for_order(13185, "BQ-AAAAAA", suffix=185)
    assert r["mode"] == "url" and r["payload"].startswith("http")
