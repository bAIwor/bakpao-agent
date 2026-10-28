# TASK: 02 — Vision CPU

STATUS: PASS

PYTEST (output asli, 29 Okt 2026):
```
45 passed in 0.84s
```
Rincian baru: test_geometry 9 (skala exact + inkonsisten, metrik 11310 px,
uniform/reject/kosong, mock-tanpa-Modal, endpoint-tanpa-Modal, fixture vs
ground truth). test_qris/orders/guardrail lama tetap hijau.

GEOMETRY (contoh nyata dari test):
```
11310 px @ 30 px/cm -> diameter 4.00 cm, area 12.57 cm2
300 px/10 cm vs 600 px/20 cm -> px_per_cm 30.0, spread 0.0%, confidence tinggi
300 px/10 cm vs 540 px/20 cm -> confidence rendah + 1 warning
```

ENDPOINT (TestClient, tanpa Modal — output asli):
```
POST /api/vision/measure -> 200 {'ok': False, 'error': 'vision_tidak_tersedia',
  'detail': 'Function has not been hydrated ... App ... is not running.',
  'confidence': 'rendah', 'warnings': [...]}
POST /api/vision/measure (base64 sampah) -> 400 {'detail': 'base64 tidak valid'}
GET /api/health -> 200 (uvicorn lokal tetap start normal)
```

GUARDRAIL: hijau (bagian dari 45 passed). Clause hanya di
src/core/guardrail.py; file baru tidak menyalinnya.

FILES:
- src/services/geometry.py (murni: scale_from_references, mask_to_metrics,
  measure_objects)
- src/services/vision_client.py (measure_image; import modal_app di dalam
  fungsi; gagal -> ok:false, tanpa exception)
- modal_app.py (VisionService CPU: cpu=8, memory=16384, torch cpu wheel,
  transformers>=4.52, @modal.method segment, post_process_masks +
  gagal-jujur; TANPA gpu=)
- src/api/routes.py (POST /api/vision/measure + Cache-Control: no-store)
- scripts/gen_vision_fixtures.py + tests/fixtures/vision/ (3 PNG + ground_truth)
- tests/test_geometry.py

COST: $0 (tidak ada panggilan model / GPU; modal tidak dijalankan di run ini)

NOTES (penyimpangan + alasan):
1. `scale_cm` diartikan sebagai {"px_per_cm": angka} dari acuan yang diketahui.
   Tanpa itu -> ukuran piksel + "skala": "tidak_diketahui". Tidak mengarang cm.
2. `post_process_masks` dibungkus try/except -> gagal jujur
   (mask_postprocess_gagal + detail), bukan angka palsu. Pola 4-level
   input_points/labels disalin persis dari probe CPU terverifikasi
   (scripts/modal_cpu_sam_probe.py, tidak diubah).
3. products.json kembali 6 item (reguler+mini) oleh agen lain — BUKAN file saya,
   tidak saya sentuh/komit. Test + endpoint Task 2 tidak tergantung bentuk menu.
4. File agen lain (app.js/html edit, probe CPU, komit Baseten/maskot) dibiarkan
   apa adanya.

BLOCKERS: GPU Modal tetap butuh metode pembayaran di akun (P4). VisionService
CPU ditulis dari pola probe terverifikasi tetapi BELUM pernah di-run (dilarang
di run ini) — verifikasi deploy milik Qoder.
