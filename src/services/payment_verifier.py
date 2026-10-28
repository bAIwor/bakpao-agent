"""Payment verifier — STUB Task 1. Implementasi penuh di Task 4.

Plumbing (upload endpoint) sudah ada dari awal: file diterima,
dipakai di memory, TIDAK disimpan ke disk.
"""


async def verify_payment_screenshot(image_bytes: bytes, expected_amount: int,
                                    expected_suffix=None,
                                    order_code: str = "") -> dict:
    _ = (image_bytes, expected_amount, expected_suffix, order_code)
    return {"verified": False, "reason": "not_implemented",
            "status": "MENUNGGU_BAYAR", "order_code": order_code,
            "expected_amount": expected_amount, "detected_amount": None,
            "needs_human_review": True,
            "notes": "verifier Task 4 belum diimplementasikan"}
