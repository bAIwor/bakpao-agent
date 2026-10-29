# 🥟 Bakpao.my.id — Autonomous Commerce & Kitchen Operations Agent

[![Live Production](https://img.shields.io/badge/Live_Storefront-bakpao.my.id-amber?style=for-the-badge&logo=cloudflare)](https://bakpao.my.id)
[![Meta Hackathon](https://img.shields.io/badge/Meta_Global_AI_Hackathon-2026_Startup_Track-blue?style=for-the-badge&logo=meta)](https://bakpao.my.id/cara-kerja)
[![Tests Passing](https://img.shields.io/badge/Pytest-67_Passed-emerald?style=for-the-badge&logo=pytest)](https://bakpao.my.id)

> **"Tool AI global umumnya hanya jadi chatbot atau image generator biasa. Bakpao.my.id secara nyata mengukur fisik daganganmu, menghitung biaya pokok operasional harian, dan menjaga uang pembayaran masuk ke dapur."**

Sistem operasional micro-bakery otonom ditenagai Meta AI Tooling dan model open-weights untuk UMKM kuliner di Kabupaten Banyumas, Jawa Tengah.

---

## 🎥 3-Minute Demo Video
[![Tonton Video Demo 3 Menit](https://img.shields.io/badge/YouTube-Video_Demo_3_Menit-red?style=for-the-badge&logo=youtube)](https://youtube.com)
*(Tautan rekaman alur penuh: pemesanan, verifikasi slip QRIS otomatis, layar dapur realtime, dan kontrol mutu visual nampan)*

---

## 🌐 Tautan Langsung Produksi (Live Links)

- **Etalase Toko**: [https://bakpao.my.id](https://bakpao.my.id) (Katalog 6 varian, keranjang belanja interaktif)
- **Katalog AI**: [https://bakpao.my.id/katalog](https://bakpao.my.id/katalog) (Poster resolusi tinggi & copywriting otomatis)
- **Layar Dapur Live (KDS)**: [https://bakpao.my.id/dapur](https://bakpao.my.id/dapur) (Antrean produksi realtime interval 3 detik)
- **Arsitektur & Cara Kerja**: [https://bakpao.my.id/cara-kerja](https://bakpao.my.id/cara-kerja) (Penjelasan alur teknis 4 tahap)
- **API HPP Resep & Margin**: [https://bakpao.my.id/api/pricing/hpp](https://bakpao.my.id/api/pricing/hpp)
- **API Komoditas SIGAOKMAS**: [https://bakpao.my.id/api/pricing/commodities](https://bakpao.my.id/api/pricing/commodities)

---

## 📖 Kisah Nyata: Kenapa Kami Membangun Bakpao.my.id?

Kami mengelola warung bakpao tradisional di Banyumas. Selama bertahun-tahun, operasional warung dijalankan secara manual dan penuh ketidakpastian:
1. **Biaya pokok (HPP) hanya ditebak di kepala**: Saat harga ayam atau tepung terigu melonjak di pasar lokal, harga jual tidak pernah disesuaikan tepat waktu sehingga margin tergerus tanpa disadari.
2. **Kualitas nampan kukus tidak seragam**: Tidak ada alat ukur praktis untuk mengetahui apakah bakpao mengembang sempurna ke diameter standar (&plusmn;4–7 cm) atau mengalami kegagalan adonan.
3. **Pemeriksaan struk QRIS manual yang lambat**: Setiap kali pembeli membayar via QRIS, kasir harus membuka aplikasi m-banking atau dashboard e-wallet untuk memastikan nominal exact benar-benar masuk sebelum pesanan dibuat di dapur.

**Bakpao.my.id** lahir dari kebutuhan firsthand tersebut—bukan sekadar proyek konsep, melainkan sistem kerja yang kami pakai langsung di warung kami sendiri dan dapat diduplikasi oleh ribuan pelaku UMKM kuliner lainnya.

---

## 🏗️ Arsitektur Sistem

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       PELANGGAN (Mobile Browser)                            │
│           https://bakpao.my.id (Storefront, Cart, QRIS Ticket)              │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ HTTPS / Cloudflare Edge
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                  FASTAPI BACKEND & AGENT ORCHESTRATION                      │
│                                                                             │
│  ┌─────────────────────────┐  ┌───────────────────────┐  ┌───────────────┐ │
│  │   Store & Order State   │  │ Deterministik Pricing │  │  KDS Engine   │ │
│  │  (Unique 3-Digit Code)  │  │   & HPP Resep Dinamis │  │ (3s Polling)  │ │
│  └────────────┬────────────┘  └───────────┬───────────┘  └───────┬───────┘ │
└───────────────┼───────────────────────────┼──────────────────────┼──────────┘
                │                           │                      │
     ┌──────────┴──────────┐     ┌──────────┴──────────┐           ▼
     ▼                     ▼     ▼                     ▼    ┌─────────────┐
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────┐ │ Layar Dapur │
│ Baseten      │ │ Meta Model   │ │ SIGAOKMAS    │ │Modal │ │ (/dapur)    │
│ Endpoint     │ │ API (Spark)  │ │ Banyumas     │ │CPU/T4│ └─────────────┘
│ Multimodal   │ │ Reasoning    │ │ Data Pasar   │ │SAM2.1│
│ Receipt OCR  │ │ Tool Calling │ │ Tradisional  │ │QC Bun│
└──────────────┘ └──────────────┘ └──────────────┘ └──────┘
```

---

## 🤖 Model Meta AI yang Digunakan

| Model Meta | Runtime / Provider | Peran Khusus dalam Sistem | Estimasi Biaya |
|---|---|---|---|
| **SAM 2.1 Hiera Large** (`facebook/sam2.1-hiera-large`) | Modal Serverless | Segmentasi nampan kukusan, hitung diameter fisik ($d=2\sqrt{A/\pi}$), deteksi tingkat reject | ~$0.0007 / analisis |
| **Muse Spark 1.3** | Meta Model API | Evaluasi fluktuasi HPP komoditas pasar, pembuatan keputusan repricing, dan notifikasi vendor | ~$0.000002 / run |
| **Muse Image 1.0** | Meta Model API | Generasi poster promosi produk komersial kualitas tinggi | $0.01 / poster |
| **Muse Spark Open 1026** | Baseten Endpoint | Pembacaan multimodal struk bukti bayar e-wallet & caption katalog | Kredit Hackathon |

---

## 💡 Soal model bobot terbuka — termasuk koreksi yang kami buat sendiri

Catatan awal kami (**Preflight P3**) menyimpulkan bahwa `sam-3.1` di Meta Model API
"mengembalikan teks kosong", sehingga bobot terbuka dianggap satu-satunya jalur.
**Kesimpulan itu salah.** Penyebabnya: prompt yang kami pakai saat itu (`"bakpao"`) tidak
cocok dengan satu objek pun, dan dokumentasi menyebut nol hasil sebagai keluaran yang sah
(*"zero matches is a valid outcome"*).

Diuji ulang dengan prompt yang benar (`"steamed bun"`), `sam-3.1` bekerja dan mengembalikan
box + mask:

```
<0f>0<|box;x1=299;y1=148;x2=543;y2=361;w=600;h=450|><|mask;x=0;y=0;data=...|>
```

Kami membiarkan koreksi ini di README karena prosesnya bagian dari cerita: satu tes dengan
prompt yang buruk hampir membuat kami membuang jalur yang berfungsi.

**Lalu kenapa segmentasi utama tetap memakai `sam2.1` di Modal?** Bukan karena API gagal,
melainkan karena bounty ini menilai penggunaan **bobot terbuka**. `facebook/sam2.1-hiera-large`
berlisensi Apache-2.0 dan bisa diunduh hari ini, sedangkan bobot `sam-3.1` masih gated
(approval manual). Jadi bobot Meta dijalankan sendiri di Modal, sementara `sam-3.1` tetap
tersedia sebagai jalur alternatif — keduanya melewati fungsi geometri yang sama,
`src/services/geometry.py`.

---

## 💰 Transparansi Biaya & Efisiensi Operasional

Sistem dirancang dengan pemisahan beban komputasi yang hemat biaya:
- **Vision di Modal Serverless**: Berjalan dengan `scaledown_window=60`, kontainer otomatis mati saat tidak ada antrean nampan (biaya idle $0).
- **Penalaran di Meta Model API (Spark 1.3)**: Struktur JSON schema ketat dengan reasoning effort rendah menghasilkan biaya mikro (~$0.000002 per evaluasi repricing).
- **Pemisahan Peran**: Logika aritmetika harga dilakukan 100% deterministik di Python, sedangkan model LLM difokuskan murni untuk penalaran bisnis dan bahasa komunikasi vendor.

---

## 🛠️ Menjalankan Sistem Secara Mandiri (Lokal)

### 1. Kloning Repositori & Pasang Ketergantungan
```bash
git clone https://github.com/bAIwor/bakpao-agent.git
cd bakpao-agent
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Jalankan Pengujian Otomatis
```bash
pytest --basetemp=.pytest_temp -q
# Hasil: 79 passed in ~0.8s
```

### 2b. Perbarui Indeks Harga Pasar (SIGAOKMAS)
```bash
python tools/refresh_sigaokmas.py            # 7 hari terakhir, 5 cakupan pasar
# -> src/data/cache/sigaokmas/prices_raw.csv + median_7d.json
```

### 2c. Bersihkan Antrean Demo (opsional)
```bash
python -m modal run tools/reset_demo_orders.py                  # lihat isi antrean
python -m modal run tools/reset_demo_orders.py --aksi kosongkan # arsipkan lalu kosongkan
```

### 3. Jalankan Skrip Demo End-to-End
```bash
python scripts/demo_e2e.py --url http://127.0.0.1:8000
# Menguji 12 tahapan integrasi penuh dalam ~10 detik
```

### 4. Mulai Server Pengembangan
```bash
python -m uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
```
Buka browser di `http://localhost:8000`.

---

## ⚖️ Batasan Sistem yang Jujur
1. **Akurasi Ukuran Fisik**: Estimasi diameter fisik memiliki rentang toleransi &plusmn;10–12% tergantung kemiringan sudut kamera terhadap papan referensi kalibrasi.
2. **Dasar HPP dari SIGAOKMAS**: HPP memakai median 7 hari harga eceran Kab. Banyumas dari portal SIGAOKMAS untuk enam bahan (terigu, gula, minyak, ayam, telur, kacang hijau), dikali faktor 1,0 — sengaja tidak dikoreksi ke bawah, jadi HPP condong lebih tinggi daripada harga grosir sebenarnya. Bahan yang tidak dipantau portal (coklat, santan, margarin, ragi, bumbu) memakai harga beli dapur. Setiap bahan menyimpan asalnya di `sumber_per_bahan`, dan `/api/pricing/hpp` menampilkan selisih harga dapur vs eceran. Data diperbarui otomatis oleh cron Modal `refresh_harga_pasar` setiap 08.30 WIB: hasilnya ditulis ke volume `/data/sigaokmas` dan dibaca web (reload berkala, tanpa redeploy). Portal memutus TLS dari sebagian jaringan, jadi fetcher memakai jalur langsung lalu reader proxy. Refresh manual: `python tools/refresh_sigaokmas.py`.

---

## 🥟 Tim Pengembang
- **PT. BAIWOR AGENTIC INDONESIA** (Kabupaten Banyumas, Jawa Tengah)
- **Wijang bAIwor** & Tim Pengembang
- Meta Global AI Developer Hackathon 2026 — *Startup Track & Open Weight Track*
