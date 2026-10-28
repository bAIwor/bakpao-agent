# TASK: 01 — Scaffolding

STATUS: PASS

FILES (baru/ubah di task ini):
- requirements.txt (+python-multipart, temuan smoke test)
- .env.example, README.md, .gitignore (+.env.modal)
- src/core/config.py, src/core/guardrail.py
- src/data/products.json, src/data/recipes.json (TODO-DAPUR, tanpa takaran karangan)
- src/data/merchant_qris.txt (sudah ada, diverifikasi 205 char + CRC 79A2)
- src/services/qris_service.py, orders.py, payment_verifier.py (STUB), meta_client.py
- src/api/routes.py (+GET /api/orders/{code}/qr untuk pay.html — tambahan dari spec)
- src/main.py (fix ROOT static + DATA_DIR default lokal "data", lihat NOTES)
- modal_app.py (tulis saja, TANPA deploy)
- src/static/: index.html, pay.html, dapur.html, cara-kerja.html, app.js, pay.js, dapur.js
- scripts/gen_placeholder_images.py + 6 placeholder + merchant-qris.png (valid JPEG 1762x2480)
- tests/test_qris.py, tests/test_orders.py, tests/test_guardrail.py

PYTEST (output asli, 29 Okt 2026):
```
19 passed in 0.32s
```
Rincian: test_qris 12 (termasuk CRC79A2 + dynamic recompute), test_orders 5,
test_guardrail 2. Satu FAIL sementara (substring scan menangkap kata param lama
di komentar modal_app.py + probe) → diparafrase, hijau.

HEALTH: tidak via curl (sandbox blokir socket) — via pemanggilan fungsi langsung:
```
{'ok': True, 'time': '2026-10-28T19:46:20+00:00', 'service': 'Bakpao.my.id'}
```

ORDER_TEST (fungsi langsung, DATA_DIR sementara):
```
order: BQ-4HX7TX MENUNGGU_BAYAR Rp 6.887 qr_len=1140
qr_endpoint: /pay/BQ-4HX7TX
queue_n: 1
complete: SELESAI
```
(2x ayam reguler = 6000 + suffix 887 = 6887 — aritmetika cocok.)

PAGES: /pay/<code> dan /dapur tidak dibuka via browser (sandbox) — route
terdaftar (14 di router, dilayani via _IncludedRouter FastAPI 0.162);
pay.html/dapur.html lolos guardrail scan.

GUARDRAIL: tests/test_guardrail.py hijau (19 passed mencakup keduanya).
SMOKE_TEST: SKIP_SANDBOX — uvicorn gagal bind dengan PermissionError
[WinError 10013] (batas sandbox, bukan bug kode). App import + StaticFiles OK.

GIT (repo-local wijang@bakpao.my.id, tanpa ubah config global):
- 7ddb436 chore: scaffold FastAPI app, config, guardrail, data menu
- 26174ea feat: order store + QRIS service (CRC16 dinamis + 3 mode)
- 59956f0 feat: storefront, cart, pay-page QR, dashboard dapur
- 740f41f chore: product placeholders + merchant QRIS asset
- (fix + docs menyusul di bawah)
`git status` tidak menampilkan .env maupun .env.modal (ter-ignore).

COST: Rp 0 (nol panggilan model, nol deploy)

NOTES (penyimpangan dari spec + alasan):
1. requirements.txt + python-multipart>=0.0.9 — WAJIB untuk endpoint upload
   (FastAPI menolak route File/UploadFile tanpanya). Spec §3.1 belum memuatnya.
2. src/main.py DATA_DIR default lokal "data" (bukan "/data") — "/data" di Windows
   = C:\data (risiko izin tulis). Di Modal, env DATA_DIR=/data tetap dipakai.
3. Tambah GET /api/orders/{code}/qr — pay.html butuh membaca ulang QR setelah
   redirect (qr_b64 hanya ada di respons POST /api/orders).
4. dapur butuh POST /api/orders/{code}/complete (SELESAI) — implisit di §3.8,
   belum ada di tabel §3.7.
5. git: flag `-c safe.directory=...` per perintah karena sandbox jalan sebagai
   user berbeda (tanpa ubah config global). `scripts/modal_cpu_probe.py` BUKAN
   file saya (agen lain sedang bekerja) — dibiarkan untracked.
6. FASE D: scripts/preflight.py → docs/preflight/preflight.py.archive (aturan
   §2.8); out.txt (0 byte) dihapus; .env di-append 3 var; .env.modal dibuat
   via skrip (tercetak hanya panjang=48, tanpa nilai).

BLOCKERS: none
