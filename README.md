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

## 💡 Mengapa Model Bobot Terbuka (Open-Weights) Sangat Krusial?

Dalam tahap pengujian preflight kami (**Preflight P3 di `docs/preflight/report.md`**), pemanggilan model tertutup `sam-3.1` melalui Meta Model API **hanya mengembalikan teks kosong** tanpa data mask spasial yang dapat diolah.

Oleh karena itu, penyebaran bobot terbuka **`facebook/sam2.1-hiera-large`** (Apache-2.0, ungated) pada runtime Modal adalah **satu-satunya solusi teknis yang valid** untuk mendapatkan mask resolusi penuh, memungkinkan kalibrasi matematis cm riil dari papan acuan dua garis.

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
git clone https://github.com/PT-BAIWOR-AGENTIC-INDONESIA/bakpao-agent.git
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
# Hasil: 67 passed in ~1.3s
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
2. **Konektivitas SIGAOKMAS**: Jika server pemda Banyumas mengalami kendala jaringan atau TLS, sistem otomatis memakai *benchmark cache* lokal pasar Banyumas agar pesanan tidak terganggu.

---

## 🥟 Tim Pengembang
- **PT. BAIWOR AGENTIC INDONESIA** (Kabupaten Banyumas, Jawa Tengah)
- **Wijang bAIwor** & Tim Pengembang
- Meta Global AI Developer Hackathon 2026 — *Startup Track & Open Weight Track*
