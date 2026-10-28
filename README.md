# Bakpao.my.id — Autonomous Commerce & Kitchen Agent

**Live:** https://bakpao.my.id · **Deployment Modal:** https://baiwormyid--bakpao.modal.run
Meta Global AI Developer Hackathon 2026 · Startup Track · Bounty: **Best Build on Meta Open Weight Models**

> Tool global bisa bikin foto, atau bisa jadi chatbot.
> **Bakpao.my.id mengukur daganganmu, menghitung economics-nya, lalu menjaga uangnya masuk.**

---

## Kenapa saya bangun ini

Saya buka warung bakpao di Kab. Banyumas. Semua masih manual:

- **Harga jual** ditentukan perasaan. Kalau harga tepung atau ayam naik, ketahuan setelah sebulan rugi.
- **Ukuran bakpao** tidak pernah diukur. Yang terlalu kecil lolos ke pelanggan, yang terlalu besar memakan modal.
- **Pembayaran** lewat QRIS, lalu dicek satu per satu di aplikasi DANA: nominalnya cocok atau tidak.
- **Katalog** hanya foto di WhatsApp, tidak pernah rapi.

Bakpao.my.id adalah sistem yang saya pakai sendiri untuk menutup keempat lubang itu —
bukan prototipe untuk demo. Nomor, harga, dan QRIS di aplikasi ini milik warung saya.

---

## Apa yang dilakukannya

```
Pembeli                          Dapur
   │                                │
   ├─ pilih menu → keranjang ───────┤
   ├─ /pay/<kode>                   │
   │    QRIS merchant + nominal     │
   │    tepat + kode unik           │
   ├─ upload bukti transfer ────────┤
   │        │                       │
   │        ▼                       │
   │   [Verifier] model open-weights│
   │   baca struk → nominal + RRN   │
   │   → cocok? LUNAS               │
   │                                ▼
   │                        /dapur: antrean live
   │                        (polling 3 detik)
   │                                │
   ▼                                ▼
 /katalog                    [Vision] SAM 2.1
 poster + caption            ukur bakpao: cm²,
 (muse-image-1.0)            reject rate → HPP
```

**Empat pekerjaan, empat model:**

| Pekerjaan | Model | Di mana |
|---|---|---|
| Otak agent + baca struk (visi) | `meta-models/muse-spark-open-1026` | Baseten (open weights) |
| Segmentasi & ukur bakpao | `facebook/sam2.1-hiera-large` | Modal **CPU** (open weights) |
| Poster katalog | `muse-image-1.0` | Meta API |
| Caption katalog | `muse-spark-open-1026` | Baseten (open weights) |

---

## Kenapa open weights

Diuji langsung sebelum menulis satu baris kode aplikasi:

```json
POST https://api.meta.ai/v1/responses   model: "sam-3.1"
{"status": "completed", "output": [{ "type": "message",
  "content": [{ "type": "output_text", "text": "" }] }],
 "usage": { "input_tokens": 0, "output_tokens": 0, "images_processed": 1 }}
```

API menerima gambarnya (`images_processed: 1`) tetapi **tidak mengembalikan mask apa pun**.
Model segmentasi yang bisa dipanggil lewat API tidak memberi hasil yang bisa dipakai.

Karena itu bobot Meta yang dijalankan sendiri bukan pilihan gaya, melainkan satu-satunya jalur
yang bekerja: `facebook/sam2.1-hiera-large`, Apache-2.0, dijalankan di Modal.

### Yang terukur

| Metrik | Hasil |
|---|---|
| Segmentasi 900×600, 3 titik | **4,55 detik** (8 core CPU) |
| Akurasi diameter (gambar uji berskala diketahui) | 4,03 cm vs **4,00 cm** → galat 0,75% |
| Baca struk (open weights, visi) | nominal, RRN, metode bayar — benar, ~4 detik |
| Biaya satu poster | $0,01 |
| Biaya satu verifikasi struk | ~$0,003 |
| Total biaya pengembangan | **< $0,05** |

GPU tidak dipakai. Modal memblokir GPU sampai verifikasi kartu selesai, jadi sistem ini
dibangun di CPU — dan ternyata cukup: satu foto loyang butuh 4,5 detik.

---

## Menjalankan sendiri

```bash
git clone git@github.com:bAIwor/bakpao-agent.git
cd bakpao-agent
pip install -r requirements.txt
pytest -q                      # 67 test
uvicorn src.main:app --port 8000
```

Buka `http://localhost:8000`. Butuh `.env` (lihat `.env.example`) untuk fitur yang memanggil model.

Deploy ke Modal:

```bash
python -m modal deploy modal_app.py
```

---

## Endpoint

| Method | Path | Fungsi |
|---|---|---|
| GET | `/` | storefront |
| GET | `/pay/{code}` | halaman bayar (QRIS + nominal + kode unik) |
| GET | `/dapur` | dashboard antrean (polling 3 detik) |
| GET | `/katalog` | poster + caption |
| GET | `/cara-kerja` | penjelasan alur |
| GET | `/api/products` | daftar produk |
| POST | `/api/orders` | buat pesanan → `payment_url` + QR |
| GET | `/api/orders/{code}` | status pesanan |
| POST | `/api/orders/{code}/verify` | upload bukti transfer → `LUNAS` / `TIDAK_COCOK` / `PERLU_DICEK` |
| POST | `/api/orders/{code}/paid` | konfirmasi manual pemilik warung |
| POST | `/api/orders/{code}/complete` | tandai selesai (tombol dapur) |
| GET | `/api/kitchen/queue` | antrean dapur |
| POST | `/api/vision/measure` | ukur objek dari foto (SAM 2.1) |
| GET | `/api/pricing/hpp` | HPP per produk |
| POST | `/api/pricing/reprice` | jalankan agent repricing |

---

## Yang membuat ini bukan chatbot

1. **Verifikasi pembayaran yang menolak.** Nominal harus sama persis; `ID Transaksi` (RRN)
   yang sudah dipakai pesanan lain ditolak (`duplikat_transaksi`); waktu transfer di luar
   60 menit dari pesanan ditandai `PERLU_DICEK`. Kegagalan model → `GAGAL`, tidak pernah
   diam-diam lolos.
2. **Keputusan di kode, bukan di model.** Model hanya membaca gambar. Aturan LUNAS /
   TIDAK_COCOK / PERLU_DICEK dihitung deterministik di Python.
3. **Angka vision selalu berpasangan dengan ketidakpastian.** Setiap hasil menyertakan
   `diameter_cm_range`, `confidence`, dan `warnings`. Kalau skala tidak diketahui,
   sistem mengembalikan piksel — bukan cm karangan.
4. **Ruang lingkup yang sempit dan disengaja.** Asisten ini hanya membantu keputusan
   operasional pemilik warung — HPP, margin, food-cost, stok, omzet, reject rate.
   Ia tidak menilai makanan untuk konsumen. Batasan itu dikunci di `src/core/guardrail.py`
   dan ditegakkan oleh test otomatis yang memindai seluruh repo.

---

## Batasan yang saya akui

- **Takaran resep masih contoh.** `src/data/recipes.json` diberi penanda dan tidak dipakai
  untuk menyarankan harga sampai pemilik dapur mengisi angka aslinya.
- **Sumber harga pasar mati.** Portal SIGAOKMAS Banyumas tidak merespons; sistem memakai
  cache benchmark yang **ditandai sebagai contoh**, bukan diklaim sebagai harga hari ini.
- **Skala butuh acuan.** Tanpa benda berskala diketahui di foto, hasil hanya dalam piksel.
- **CPU, bukan GPU.** 4,5 detik per gambar cukup untuk demo; produksi akan lebih nyaman di GPU.

---

## Struktur

```
bakpao-agent/
├── modal_app.py            # satu app Modal: web FastAPI + VisionService (CPU)
├── src/core/               # config, guardrail
├── src/services/           # qris, orders, payment_verifier, vision_client,
│                           # geometry, pricing, pricing_agent, catalog_service
├── src/api/routes.py       # endpoint + halaman
├── src/static/             # storefront, pay, dapur, katalog, cara-kerja
├── scripts/                # probe preflight, generator fixture
├── docs/                   # laporan per task + bukti preflight
└── tests/                  # 67 test
```

---

## Lisensi & atribusi

Kode: MIT. Model: `facebook/sam2.1-hiera-large` (Apache-2.0) · `Muse Spark Open` (Meta open weights).
Foto produk & QRIS adalah milik PT. BAIWOR AGENTIC INDONESIA.
