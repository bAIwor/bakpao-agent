# BUKTI EKSEKUSI DEMO END-TO-END

```
======================================================================
🥟 BAKPAO.MY.ID — DEMO OTOMASI END-TO-END (META GLOBAL HACKATHON)
Waktu Mulai : 2026-10-29 07:30:39 WIB
Target URL  : http://127.0.0.1:8000
======================================================================

[Langkah 1/12] Pengecekan Status Keaktifan Sistem (/api/health)
  ✓ Layanan aktif: Bakpao.my.id | Waktu server: 2026-10-29T00:30:39.360467+00:00

[Langkah 2/12] Pengambilan Katalog Menu (/api/products)
  ✓ Berhasil memuat 6 varian menu:
    - Bakpao Ayam (Reguler) | Rp 3,500 | Paling Laris 🔥
    - Bakpao Ayam (Mini) | Rp 2,500 | Hemat 🌟
    - Bakpao Coklat (Reguler) | Rp 3,500 | Favorit Manis 🍫
    - Bakpao Coklat (Mini) | Rp 2,500 | Cemilan Pas ☕
    - Bakpao Kacang Hijau (Reguler) | Rp 3,500 | Klasik Wangi 🌿
    - Bakpao Kacang Hijau (Mini) | Rp 2,500 | Tradisional 🍵

[Langkah 3/12] Rujukan Harga Pasar Banyumas (/api/pricing/commodities)
  ✓ Sumber Data: Harga beli dapur (dikonfirmasi pemilik) + estimasi pasar untuk bahan minor (Tanggal: 2026-10-29)
  ✓ Status Jaringan: fallback_cache | Stale: False
    Terigu: Rp 12,500/kg | Ayam: Rp 35,000/kg | Coklat: Rp 38,000/kg

[Langkah 4/12] Perhitungan Deterministik HPP (/api/pricing/hpp)
  ✓ Analisis HPP & Margin Unit:
    - Bakpao Ayam (Reguler): HPP Rp 2,234 | Harga Saran Rp 3,000 | Margin 25.5% (Food Cost 74.5%)
    - Bakpao Ayam (Mini): HPP Rp 1,359 | Harga Saran Rp 2,000 | Margin 32.0% (Food Cost 68.0%)
    - Bakpao Coklat (Reguler): HPP Rp 1,319 | Harga Saran Rp 2,000 | Margin 34.1% (Food Cost 66.0%)

[Langkah 5/12] Simulasi Agen Repricing Pintar (/api/pricing/reprice)
  Simulasi kenaikan harga daging ayam +28.5% (Rp 35.000 -> Rp 45.000)...
  ✓ Ringkasan Keputusan: 2 varian ayam terdampak kenaikan HPP 8.6% perlu REPRICE_UP. 4 varian coklat dan kacang hijau HPP stabil, HOLD.
  ✓ Peringatan Vendor  : Harga ayam naik 28.57% dari 35000 ke 45000, memicu HPP varian ayam naik 8.6%. Evaluasi supplier ayam alternatif dan negosiasi batch berikutnya.
    * Bakpao Ayam (Reguler): HPP lama Rp 2,234 -> HPP baru Rp 2,427 (+8.64%) -> Aksi: REPRICE_UP
    * Bakpao Ayam (Mini): HPP lama Rp 1,359 -> HPP baru Rp 1,476 (+8.61%) -> Aksi: REPRICE_UP

[Langkah 6/12] Pembuatan Pesanan Pembeli (/api/orders)
  ✓ Pesanan Berhasil Dibuat: Kode [BQ-X3TMEK]
  ✓ Subtotal: Rp 9,500 | Kode Unik 3-Digit: 988
  ✓ Total Tagihan Exact: Rp 10.488 (Rp 10,488)
  ✓ URL Pembayaran: https://baiwormyid--bakpao.modal.run/pay/BQ-X3TMEK

[Langkah 7/12] Cek Status Pesanan (/api/orders/BQ-X3TMEK)
  ✓ Status Pesanan Saat Ini: MENUNGGU_BAYAR

[Langkah 8/12] Konfirmasi Mutasi QRIS Masuk (/api/orders/BQ-X3TMEK/paid)
  ✓ Status Berubah: LUNAS ✅
  ✓ Nomor Antrean Dapur: #4

[Langkah 9/12] Pemantauan Layar Dapur KDS (/api/kitchen/queue)
  ✓ Antrean aktif di dapur: 4 pesanan
  ✓ Pesanan [BQ-X3TMEK] terverifikasi masuk antrean produksi: True

[Langkah 10/12] Tombol Dapur: Siap Disajikan (/api/orders/BQ-X3TMEK/complete)
  ✓ Status Final: SELESAI 🎉 (Pesanan selesai)

[Langkah 11/12] Uji Mesin Geometri Vision (SAM 2.1 QC Simulation)
  ✓ Kalibrasi Skala Papan Acuan: 30.0 px/cm | Confidence: tinggi
  ✓ Deteksi Objek Loyang: 3 bakpao
  ✓ Median Diameter     : 4.0 cm (Rentang: 1.99 - 4.0 cm)
  ✓ Reject Rate         : 33.3% (1 reject)

[Langkah 12/12] Tinjauan Halaman Publik (/katalog)
  ✓ Halaman katalog dapat diakses sempurna (HTTP 200 OK)

======================================================================
✅ SELURUH 12 LANGKAH INTEGRASI END-TO-END BERHASIL TUNTAS 100%!
Total Durasi Pengujian: 11.32 detik
======================================================================
```
