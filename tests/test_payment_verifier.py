"""Test verifikasi bukti transfer: normalisasi nominal + aturan keputusan.

Tidak memanggil model (offline) — memakai hasil baca buatan.
"""
from src.services.payment_verifier import (
    STATUS_ERROR,
    STATUS_PAID,
    STATUS_REJECT,
    STATUS_REVIEW,
    decide,
    normalise_amount,
    parse_time,
)

EXPECTED = 13185


def receipt(**over):
    base = {
        "is_transfer_screenshot": True,
        "detected_amount": 13185,
        "detected_reference": "TRX20261029ABC",
        "detected_bank": "DANA",
        "detected_time": "2026-10-29T10:05:00",
        "confidence": 0.95,
        "notes": "",
    }
    base.update(over)
    return base


def test_normalise_amount_variants():
    assert normalise_amount("Rp13.185")[0] == 13185
    assert normalise_amount("Rp 13.185")[0] == 13185
    assert normalise_amount("13185")[0] == 13185
    assert normalise_amount(13185)[0] == 13185
    assert normalise_amount("13,185")[0] == 13185
    assert normalise_amount("Rp13,185.00")[0] == 13185
    assert normalise_amount("32 185")[0] == 32185


def test_normalise_amount_rejects_letters():
    amount, problem = normalise_amount("RpI3.185")
    assert amount is None and problem == "nominal_ambigu"


def test_normalise_amount_empty():
    assert normalise_amount(None) == (None, "nominal_tidak_terbaca")
    assert normalise_amount("") == (None, "nominal_tidak_terbaca")


def test_parse_time_iso():
    assert parse_time("2026-10-29T10:05:00") is not None
    assert parse_time("29 Okt 2026 10:05") is None
    assert parse_time("") is None


def test_valid_receipt_is_paid():
    r = decide(receipt(), EXPECTED, "BQ-AAAAAA", {})
    assert r["status"] == STATUS_PAID and r["verified"] is True
    assert r["detected_amount"] == EXPECTED
    assert r["needs_human_review"] is False


def test_wrong_amount_rejected_with_difference():
    r = decide(receipt(detected_amount="Rp30.000"), EXPECTED, "BQ-AAAAAA", {})
    assert r["status"] == STATUS_REJECT
    assert r["reason"] == "nominal_beda"
    assert "16815" in r["notes"]         # |13185 - 30000|


def test_not_a_receipt():
    r = decide(receipt(is_transfer_screenshot=False), EXPECTED, "BQ-AAAAAA", {})
    assert r["status"] == STATUS_REJECT and r["reason"] == "bukan_struk_transfer"


def test_low_confidence_needs_check():
    r = decide(receipt(confidence=0.3), EXPECTED, "BQ-AAAAAA", {})
    assert r["status"] == STATUS_REVIEW and r["reason"] == "confidence_rendah"


def test_medium_confidence_paid_but_reviewed():
    r = decide(receipt(confidence=0.7), EXPECTED, "BQ-AAAAAA", {})
    assert r["status"] == STATUS_PAID
    assert r["needs_human_review"] is True


def test_duplicate_reference_blocked():
    used = {"TRX20261029ABC": "BQ-LAINXX"}
    r = decide(receipt(), EXPECTED, "BQ-AAAAAA", used)
    assert r["status"] == STATUS_ERROR and r["reason"] == "duplikat_transaksi"


def test_same_order_replay_allowed():
    used = {"TRX20261029ABC": "BQ-AAAAAA"}
    r = decide(receipt(), EXPECTED, "BQ-AAAAAA", used)
    assert r["status"] == STATUS_PAID


def test_outside_time_window():
    r = decide(receipt(detected_time="2026-10-29T03:00:00"), EXPECTED,
               "BQ-AAAAAA", {}, created_at="2026-10-29T10:00:00+00:00")
    assert r["status"] == STATUS_REVIEW
    assert r["reason"] == "di_luar_jendela_waktu"


def test_inside_time_window():
    # 17:20 WIB == 10:20 UTC; pesanan 10:00 UTC -> selisih 20 menit
    r = decide(receipt(detected_time="2026-10-29T17:20:00"), EXPECTED,
               "BQ-AAAAAA", {}, created_at="2026-10-29T10:00:00+00:00")
    assert r["status"] == STATUS_PAID


def test_naive_receipt_time_read_as_wib():
    """Struk tanpa zona waktu = jam toko (WIB, UTC+7)."""
    stamp = parse_time("2026-10-29T17:00:00")
    assert stamp.hour == 10 and stamp.tzinfo is not None


def test_invalid_model_response():
    r = decide(None, EXPECTED, "BQ-AAAAAA", {})
    assert r["status"] == STATUS_ERROR and r["reason"] == "respons_tidak_valid"


def test_response_always_carries_both_amounts():
    for payload in (receipt(), receipt(detected_amount=1), receipt(confidence=0.1)):
        r = decide(payload, EXPECTED, "BQ-AAAAAA", {})
        assert r["expected_amount"] == EXPECTED
        assert "detected_amount" in r
