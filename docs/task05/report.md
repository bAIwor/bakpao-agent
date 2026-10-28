# TASK: 05 — Katalog

STATUS: PASS

PYTEST (output asli, 29 Okt 2026):
```
67 passed in 1.63s
```
6 test baru test_catalog_service (tolak kata-terlarang, tolak harga salah,
terima valid, pricelist dari produk, template valid, extract b64/None).
Guardrail hijau (kata uji dibangun dari potongan agar file test tidak
self-detect).

POSTERS: 1 ter-generate | file:
src/static/assets/katalog/bakpao-ayam.webp (367.500 B, WEBP, 11,1 dtk)
| biaya $0,01
Catatan: model menulis "Bakpao" (satu typo kecil) — dibiarkan apa adanya
sebagai bukti output asli.

CAPTIONS (Baseten meta-models/muse-spark-open-1026, via choices[0]):
"Bakpao Ayam Reguler isi ayam cincang bumbu gurih cuma Rp3.000! Kulit
lembut dan rasa gurih nikmat di setiap gigitan."
6/6 caption dari Baseten lolos validasi (harga cocok, tanpa kata terlarang).

PRICELIST: markdown 6 produk dari harga products.json (3.000/2.000),
ditulis di build_pricelist — bukan hardcode.

GUARDRAIL: hijau (67 passed mencakup test_guardrail; laporan ini dipindai).

FILES:
- src/services/catalog_service.py (poster, caption+template, pricelist, publish)
- src/api/routes.py (GET /katalog, POST /api/catalog/generate)
- src/static/index.html (tautan "Lihat katalog lengkap")
- src/static/katalog.html + src/data/catalog.json (hasil publish, 6 entri)
- tests/test_catalog_service.py

NOTES:
1. BASETEN_* sudah ada di .env + config.py (agen lain) — dipakai apa adanya;
   endpoint = BASE + "/chat/completions" (BASE sudah berakhiran /v1).
2. Poster lain memakai foto produk (/static) sampai di-generate manual via
   POST /api/catalog/generate.
3. Suhu caption 0.7 (kreativitas); validasi deterministik tetap berlaku.

BLOCKERS: none
