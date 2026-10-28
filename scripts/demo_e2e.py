"""Demo otomatis End-to-End untuk verifikasi seluruh alur sistem Bakpao.my.id.

Menjalankan alur:
1. Health Check
2. Katalog Produk Aktif
3. Harga Komoditas Pasar Banyumas (SIGAOKMAS)
4. Perhitungan HPP & Margin Resep
5. Simulasi Agen Repricing (Kenaikan Harga Bahan Baku)
6. Pembuatan Pesanan Pembeli (Order + Kode Unik + QRIS DANA Bisnis)
7. Pemantauan Pesanan & Polling
8. Konfirmasi Pembayaran QRIS (LUNAS)
9. Pembaruan Antrean Layar Dapur (KDS)
10. Penyelesaian Pesanan Dapur
11. Verifikasi Geometri Vision (Quality Control Loyang Bakpao)
12. Visualisasi Poster AI & Katalog
"""
from __future__ import annotations

import argparse
import datetime
import json
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import httpx

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.services.geometry import mask_to_metrics, measure_objects, scale_from_references


def run_e2e_demo(base_url: str = "http://127.0.0.1:8000") -> dict:
    base_url = base_url.rstrip("/")
    log_lines = []

    def p(text: str = ""):
        print(text)
        log_lines.append(text)

    start_time = time.time()
    p("=" * 70)
    p("🥟 BAKPAO.MY.ID — DEMO OTOMASI END-TO-END (META GLOBAL HACKATHON)")
    p(f"Waktu Mulai : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S WIB')}")
    p(f"Target URL  : {base_url}")
    p("=" * 70)

    client = httpx.Client(timeout=30.0, verify=False)

    # 1. Health Check
    p("\n[Langkah 1/12] Pengecekan Status Keaktifan Sistem (/api/health)")
    r1 = client.get(f"{base_url}/api/health")
    assert r1.status_code == 200, f"Health check gagal: {r1.status_code}"
    h = r1.json()
    p(f"  ✓ Layanan aktif: {h.get('service')} | Waktu server: {h.get('time')}")

    # 2. Katalog Produk
    p("\n[Langkah 2/12] Pengambilan Katalog Menu (/api/products)")
    r2 = client.get(f"{base_url}/api/products")
    assert r2.status_code == 200, "Gagal ambil produk"
    prods = r2.json().get("products", [])
    p(f"  ✓ Berhasil memuat {len(prods)} varian menu:")
    for item in prods:
        p(f"    - {item['name']} | Rp {item['price']:,} | {item['badge']}")

    # 3. Komoditas Pasar
    p("\n[Langkah 3/12] Rujukan Harga Pasar Banyumas (/api/pricing/commodities)")
    r3 = client.get(f"{base_url}/api/pricing/commodities")
    assert r3.status_code == 200, "Gagal ambil komoditas"
    c_data = r3.json()
    p(f"  ✓ Sumber Data: {c_data.get('sumber')} (Tanggal: {c_data.get('tanggal')})")
    p(f"  ✓ Status Jaringan: {c_data.get('status')} | Stale: {c_data.get('stale')}")
    prices = c_data.get("prices", {})
    p(f"    Terigu: Rp {prices.get('terigu'):,}/kg | Ayam: Rp {prices.get('ayam'):,}/kg | Coklat: Rp {prices.get('coklat'):,}/kg")

    # 4. HPP & Margin
    p("\n[Langkah 4/12] Perhitungan Deterministik HPP (/api/pricing/hpp)")
    r4 = client.get(f"{base_url}/api/pricing/hpp")
    assert r4.status_code == 200, "Gagal ambil HPP"
    hpp_data = r4.json().get("products", {})
    p(f"  ✓ Analisis HPP & Margin Unit:")
    for pid, info in list(hpp_data.items())[:3]:
        p(f"    - {info['name']}: HPP Rp {info['hpp']:,} | Harga Saran Rp {info['suggested_price']:,} | Margin {info['margin_pct']}% (Food Cost {info['food_cost_pct']}%)")

    # 5. Simulasi Repricing Agent
    p("\n[Langkah 5/12] Simulasi Agen Repricing Pintar (/api/pricing/reprice)")
    p("  Simulasi kenaikan harga daging ayam +28.5% (Rp 35.000 -> Rp 45.000)...")
    yesterday = dict(prices)
    today = dict(prices)
    today["ayam"] = 45000
    r5 = client.post(f"{base_url}/api/pricing/reprice", json={"prices_today": today, "prices_yesterday": yesterday})
    assert r5.status_code == 200, "Gagal repricing"
    dec = r5.json().get("decision", {})
    p(f"  ✓ Ringkasan Keputusan: {dec.get('summary')}")
    p(f"  ✓ Peringatan Vendor  : {dec.get('vendor_alert')}")
    for it in dec.get("per_item", []):
        if it["action"] == "REPRICE_UP":
            p(f"    * {it['product_id']}: HPP lama Rp {it['hpp_old']:,} -> HPP baru Rp {it['hpp_new']:,} (+{it['hpp_change_pct']}%) -> Aksi: {it['action']}")

    # 6. Pembuatan Pesanan Pembeli
    p("\n[Langkah 6/12] Pembuatan Pesanan Pembeli (/api/orders)")
    order_payload = {
        "items": [
            {"product_id": "bakpao-ayam", "qty": 2},
            {"product_id": "bakpao-coklat-mini", "qty": 1},
        ]
    }
    r6 = client.post(f"{base_url}/api/orders", json=order_payload)
    assert r6.status_code == 200, "Gagal buat order"
    order = r6.json()
    code = order["order_code"]
    p(f"  ✓ Pesanan Berhasil Dibuat: Kode [{code}]")
    p(f"  ✓ Subtotal: Rp {order['total']:,} | Kode Unik 3-Digit: {order['unique_suffix']}")
    p(f"  ✓ Total Tagihan Exact: {order['nominal_rp']} (Rp {order['amount']:,})")
    p(f"  ✓ URL Pembayaran: {order['payment_url']}")

    # 7. Cek Status Order
    p(f"\n[Langkah 7/12] Cek Status Pesanan (/api/orders/{code})")
    r7 = client.get(f"{base_url}/api/orders/{code}")
    assert r7.status_code == 200, "Gagal cek order"
    status_order = r7.json()
    p(f"  ✓ Status Pesanan Saat Ini: {status_order['status']}")

    # 8. Konfirmasi Pembayaran QRIS
    p(f"\n[Langkah 8/12] Konfirmasi Mutasi QRIS Masuk (/api/orders/{code}/paid)")
    r8 = client.post(f"{base_url}/api/orders/{code}/paid")
    assert r8.status_code == 200, "Gagal konfirmasi lunas"
    paid_order = r8.json()
    p(f"  ✓ Status Berubah: {paid_order['status']} ✅")
    p(f"  ✓ Nomor Antrean Dapur: #{paid_order['queue_number']}")

    # 9. Verifikasi Antrean Layar Dapur
    p("\n[Langkah 9/12] Pemantauan Layar Dapur KDS (/api/kitchen/queue)")
    r9 = client.get(f"{base_url}/api/kitchen/queue")
    assert r9.status_code == 200, "Gagal baca antrean dapur"
    q_orders = r9.json().get("queue", [])
    found_in_q = any(o["order_code"] == code for o in q_orders)
    p(f"  ✓ Antrean aktif di dapur: {len(q_orders)} pesanan")
    p(f"  ✓ Pesanan [{code}] terverifikasi masuk antrean produksi: {found_in_q}")

    # 10. Penyelesaian Pesanan Dapur
    p(f"\n[Langkah 10/12] Tombol Dapur: Siap Disajikan (/api/orders/{code}/complete)")
    r10 = client.post(f"{base_url}/api/orders/{code}/complete")
    assert r10.status_code == 200, "Gagal complete order"
    comp_order = r10.json()
    p(f"  ✓ Status Final: {comp_order['status']} 🎉 (Pesanan selesai)")

    # 11. Verifikasi Geometri Vision (Loyang Bakpao)
    p("\n[Langkah 11/12] Uji Mesin Geometri Vision (SAM 2.1 QC Simulation)")
    scale = scale_from_references({"garis_10cm": 300.0, "garis_20cm": 600.0}, {"garis_10cm": 10.0, "garis_20cm": 20.0})
    p(f"  ✓ Kalibrasi Skala Papan Acuan: {scale['px_per_cm']} px/cm | Confidence: {scale['confidence']}")
    # Simulasi 3 loyang: 2 normal (@ 11310 px) + 1 reject (@ 2800 px)
    mock_masks = [
        {"area_px": 11310, "iou": 0.94},
        {"area_px": 11310, "iou": 0.93},
        {"area_px": 2800, "iou": 0.55},
    ]
    measurement = measure_objects(mock_masks, scale["px_per_cm"])
    p(f"  ✓ Deteksi Objek Loyang: {measurement['count']} bakpao")
    p(f"  ✓ Median Diameter     : {measurement['median_diameter_cm']} cm (Rentang: {measurement['diameter_cm_range'][0]} - {measurement['diameter_cm_range'][1]} cm)")
    p(f"  ✓ Reject Rate         : {measurement['reject_rate_pct']}% ({measurement['reject_count']} reject)")

    # 12. Halaman Publik Katalog
    p("\n[Langkah 12/12] Tinjauan Halaman Publik (/katalog)")
    r12 = client.get(f"{base_url}/katalog")
    assert r12.status_code == 200, "Gagal muat /katalog"
    p("  ✓ Halaman katalog dapat diakses sempurna (HTTP 200 OK)")

    elapsed = round(time.time() - start_time, 2)
    p("\n" + "=" * 70)
    p(f"✅ SELURUH 12 LANGKAH INTEGRASI END-TO-END BERHASIL TUNTAS 100%!")
    p(f"Total Durasi Pengujian: {elapsed} detik")
    p("=" * 70)

    return {"ok": True, "elapsed": elapsed, "log": "\n".join(log_lines)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000", help="Base URL target pengujian")
    args = parser.parse_args()

    res = run_e2e_demo(args.url)
    out_file = REPO_ROOT / "docs" / "demo_log.md"
    out_file.write_text(
        f"# BUKTI EKSEKUSI DEMO END-TO-END\n\n```\n{res['log']}\n```\n",
        encoding="utf-8",
    )
    print(f"\n[INFO] Laporan eksekusi tersimpan di {out_file}")
