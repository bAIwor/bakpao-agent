"""Order store: dict + persist ke JSON file (aman untuk 1 instance).

Nomor antrean = counter di file (bukan in-memory) supaya tidak duplikat
saat container scaling. Di Modal, DATA_DIR=/data (volume).
"""
import datetime
import json
import os
from pathlib import Path

from src.services.qris_service import generate_order_code, generate_unique_suffix

STATUS_WAITING = "MENUNGGU_BAYAR"
STATUS_PAID = "LUNAS"
STATUS_FAILED = "GAGAL"
STATUS_DONE = "SELESAI"


class OrderNotFound(ValueError):
    pass


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _data_dir() -> Path:
    raw = os.environ.get("DATA_DIR", "")
    return Path(raw) if raw else _repo_root() / "data"


def _db_path() -> Path:
    return _data_dir() / "orders.json"


def _load() -> dict:
    p = _db_path()
    if p.is_file():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"orders": {}, "queue_counter": 0}


def _save(db: dict) -> None:
    _data_dir().mkdir(parents=True, exist_ok=True)
    _db_path().write_text(json.dumps(db, ensure_ascii=False, indent=1),
                           encoding="utf-8")


def _products() -> dict:
    p = _repo_root() / "src" / "data" / "products.json"
    items = json.loads(p.read_text(encoding="utf-8"))
    return {it["id"]: it for it in items if it.get("active", True)}


def create_order(items: list) -> dict:
    """items = [{product_id, qty}]. Total tepat, tanpa pembulatan."""
    catalog = _products()
    lines = []
    total = 0
    for it in items:
        pid, qty = it["product_id"], int(it["qty"])
        if pid not in catalog:
            raise ValueError(f"product_id tidak dikenal: {pid}")
        if qty <= 0:
            raise ValueError(f"qty harus > 0: {pid}")
        price = int(catalog[pid]["price"])
        total += price * qty
        lines.append({"product_id": pid, "name": catalog[pid]["name"],
                      "price": price, "qty": qty})
    suffix = generate_unique_suffix()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    order = {"order_code": generate_order_code(), "items": lines,
             "total": total, "unique_suffix": suffix,
             "amount": total + suffix, "status": STATUS_WAITING,
             "created_at": now, "paid_at": None, "queue_number": None}
    db = _load()
    db["orders"][order["order_code"]] = order
    _save(db)
    return order


def get_order(code: str) -> dict:
    order = _load()["orders"].get(code)
    if order is None:
        raise OrderNotFound(f"pesanan tidak ditemukan: {code}")
    return order


def mark_paid(code: str) -> dict:
    db = _load()
    if code not in db["orders"]:
        raise OrderNotFound(f"pesanan tidak ditemukan: {code}")
    order = db["orders"][code]
    order["status"] = STATUS_PAID
    order["paid_at"] = datetime.datetime.now(
        datetime.timezone.utc).isoformat()
    db["queue_counter"] = int(db.get("queue_counter", 0)) + 1
    order["queue_number"] = db["queue_counter"]
    _save(db)
    return order


def mark_failed(code: str) -> dict:
    db = _load()
    if code not in db["orders"]:
        raise OrderNotFound(f"pesanan tidak ditemukan: {code}")
    db["orders"][code]["status"] = STATUS_FAILED
    _save(db)
    return db["orders"][code]


def mark_done(code: str) -> dict:
    """Tombol dapur 'Siap Diantar' -> SELESAI."""
    db = _load()
    if code not in db["orders"]:
        raise OrderNotFound(f"pesanan tidak ditemukan: {code}")
    db["orders"][code]["status"] = STATUS_DONE
    _save(db)
    return db["orders"][code]


def list_orders() -> list:
    db = _load()
    return sorted(db["orders"].values(),
                  key=lambda o: o.get("created_at", ""))


def next_queue_number() -> int:
    db = _load()
    db["queue_counter"] = int(db.get("queue_counter", 0)) + 1
    _save(db)
    return db["queue_counter"]
