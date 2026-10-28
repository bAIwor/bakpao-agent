# Bakpao.my.id — Autonomous Commerce & Kitchen Agent

> "Tool global bisa bikin foto atau bisa jadi chatbot. **Bakpao.my.id mengukur
> daganganmu, menghitung economics-nya, lalu menjaga uangnya masuk.**"

Web app warung bakpao: storefront + keranjang, halaman bayar QR (`/pay/<kode>`),
dashboard dapur live (`/dapur`). Dibangun untuk Meta Global AI Developer
Hackathon 2026 — fokus bounty **Best Build on Meta Open Weight Models**.

## Yang baru di hackathon ini

- QR pay-page + nominal exact + kode unik (3 mode: `static` / `dynamic` / `url`)
- Order store (file JSON, nomor antrean anti-duplikat)
- Plumbing verifikasi struk (stub di Task 1, penuh di Task 4)
- `modal_app.py`: SATU app Modal berisi web FastAPI + GPU SAM 2.1 (internal)

## Jalan lokal

```bash
cd bakpao-agent
pip install -r requirements.txt
pytest -q
uvicorn src.main:app --port 8000
```

Buka `http://localhost:8000` di browser.

## Endpoint

| Method | Path | Fungsi |
|---|---|---|
| GET | `/api/health` | cek hidup |
| GET | `/api/products` | daftar produk aktif |
| POST | `/api/orders` | buat pesanan → order + payment_url + qr_b64 |
| GET | `/api/orders/{code}` | status pesanan (polling) |
| POST | `/api/orders/{code}/verify` | upload bukti transfer (stub Task 1) |
| POST | `/api/orders/{code}/cancel` | batalkan pesanan |
| POST | `/api/orders/{code}/complete` | tandai selesai (tombol dapur) |
| GET | `/api/kitchen/queue` | antrean dapur (polling 3 detik) |
| POST | `/api/vision/measure` | ukur objek dari foto (butuh Modal) |

Halaman: `/` storefront · `/pay/{code}` bayar · `/dapur` dapur · `/cara-kerja`
penjelasan alur.

## Mode QR (`QR_MODE`)

- `static` (default): QRIS statis merchant + nominal exact & kode unik diketik
  manual oleh pembeli.
- `dynamic`: nominal tertanam di payload (tag 54), CRC dihitung ulang.
- `url`: QR berisi URL halaman bayar.

## Struktur

```
bakpao-agent/
├── modal_app.py          # deploy Modal (web + GPU, 1 app)
├── src/core/             # config + guardrail
├── src/services/         # qris, orders, payment_verifier (stub), meta_client, vision_client, geometry
├── src/api/routes.py     # endpoint + halaman
├── src/static/           # storefront, pay, dapur
├── src/data/             # products, recipes (TODO-DAPUR), merchant_qris
└── tests/                # qris, orders, guardrail
```

## Biaya

Task 1: **Rp 0** — nol panggilan model.
