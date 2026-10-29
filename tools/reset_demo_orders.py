"""Lihat / kosongkan antrean order di volume produksi (untuk rekaman demo).

Arsip dibuat dulu, jadi data lama tidak hilang — hanya dipindahkan.

    python -m modal run tools/reset_demo_orders.py::lihat
    python -m modal run tools/reset_demo_orders.py::kosongkan
"""
import datetime
import json

import modal

app = modal.App("bakpao-maintenance")
data_volume = modal.Volume.from_name("bakpao-data")

ORDERS = "/data/orders.json"


@app.function(volumes={"/data": data_volume}, timeout=120)
def lihat() -> dict:
    data_volume.reload()
    try:
        with open(ORDERS, encoding="utf-8") as f:
            orders = json.load(f)
    except FileNotFoundError:
        return {"ada": False, "pesan": "orders.json belum ada"}
    db = orders if isinstance(orders, dict) else {"orders": orders}
    daftar = list(db.get("orders", {}).values())
    hitung: dict[str, int] = {}
    for o in daftar:
        hitung[o.get("status", "?")] = hitung.get(o.get("status", "?"), 0) + 1
    waktu = sorted(o.get("created_at", "") for o in daftar if o.get("created_at"))
    return {"ada": True, "jumlah": len(daftar), "per_status": hitung,
            "antrean_terakhir": db.get("queue_counter"),
            "terlama": waktu[0] if waktu else None,
            "terbaru": waktu[-1] if waktu else None}


@app.function(volumes={"/data": data_volume}, timeout=120)
def kosongkan() -> dict:
    data_volume.reload()
    try:
        with open(ORDERS, encoding="utf-8") as f:
            isi = f.read()
    except FileNotFoundError:
        return {"ok": True, "pesan": "tidak ada berkas, tidak ada yang dikosongkan"}

    orders = json.loads(isi)
    jumlah = len(orders.get("orders", {})) if isinstance(orders, dict) else len(orders)
    stempel = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7)))
    arsip = f"/data/orders_archive_{stempel:%Y%m%d-%H%M%S}.json"
    with open(arsip, "w", encoding="utf-8") as f:
        f.write(isi)
    with open(ORDERS, "w", encoding="utf-8") as f:
        f.write('{"orders": {}, "queue_counter": 0}')
    data_volume.commit()
    return {"ok": True, "dipindah": jumlah, "arsip": arsip}


@app.local_entrypoint()
def main(aksi: str = "lihat"):
    """modal run tools/reset_demo_orders.py            # lihat
       modal run tools/reset_demo_orders.py --aksi kosongkan
    """
    fungsi = kosongkan if aksi == "kosongkan" else lihat
    print(fungsi.remote())
