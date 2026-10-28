"""Test order store: total tepat, status, antrean, error jelas."""
import pytest

from src.services import orders as store


@pytest.fixture
def db(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    return tmp_path


def test_create_totals_exact(db):
    o = store.create_order([{"product_id": "bakpao-ayam", "qty": 2},
                            {"product_id": "bakpao-coklat", "qty": 1}])
    assert o["total"] == 2 * 3500 + 3500
    assert o["amount"] == o["total"] + o["unique_suffix"]
    assert o["status"] == "MENUNGGU_BAYAR"
    assert o["paid_at"] is None and o["queue_number"] is None


def test_unknown_product_clear_error(db):
    with pytest.raises(ValueError, match="tidak dikenal"):
        store.create_order([{"product_id": "bakpao-naga", "qty": 1}])


def test_mark_paid_sets_queue(db):
    o = store.create_order([{"product_id": "bakpao-kacang-hijau", "qty": 1}])
    p = store.mark_paid(o["order_code"])
    assert p["status"] == "LUNAS" and p["paid_at"]
    assert p["queue_number"] == 1


def test_queue_number_increments(db):
    a = store.next_queue_number()
    b = store.next_queue_number()
    assert b == a + 1


def test_missing_order_clear_error(db):
    with pytest.raises(store.OrderNotFound):
        store.get_order("BQ-XXXXXX")
    with pytest.raises(store.OrderNotFound):
        store.mark_paid("BQ-XXXXXX")


def test_cancel_and_list(db):
    o = store.create_order([{"product_id": "bakpao-ayam", "qty": 1}])
    store.mark_failed(o["order_code"])
    assert store.get_order(o["order_code"])["status"] == "GAGAL"
    assert len(store.list_orders()) == 1
