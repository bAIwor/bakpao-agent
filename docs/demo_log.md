# BUKTI EKSEKUSI DEMO END-TO-END

```
======================================================================
🥟 BAKPAO.MY.ID — DEMO OTOMASI END-TO-END (META GLOBAL HACKATHON)
Waktu Mulai : 2026-10-29 06:08:02 WIB
Target URL  : http://127.0.0.1:8000
======================================================================

[Langkah 1/12] Pengecekan Status Keaktifan Sistem (/api/health)
  ✓ Layanan aktif: Bakpao.my.id | Waktu server: 2026-10-28T23:08:02.563333+00:00

[Langkah 2/12] Pengambilan Katalog Menu (/api/products)
  ✓ Berhasil memuat 6 varian menu:
    - Bakpao Ayam (Reguler) | Rp 3,500 | Paling Laris 🔥
    - Bakpao Ayam (Mini) | Rp 2,500 | Hemat 🌟
    - Bakpao Coklat (Reguler) | Rp 3,500 | Favorit Manis 🍫
    - Bakpao Coklat (Mini) | Rp 2,500 | Cemilan Pas ☕
    - Bakpao Kacang Hijau (Reguler) | Rp 3,500 | Klasik Wangi 🌿
    - Bakpao Kacang Hijau (Mini) | Rp 2,500 | Tradisional 🍵

[Langkah 3/12] Rujukan Harga Pasar Banyumas (/api/pricing/commodities)
  ✓ Sumber Data: SIGAOKMAS Pemkab Banyumas (Pasar Wage & Pasar Manis Purwokerto) (Tanggal: 2026-10-29)
  ✓ Status Jaringan: fallback_cache | Stale: False
    Terigu: Rp 12,500/kg | Ayam: Rp 35,000/kg | Coklat: Rp 38,000/kg

[Langkah 4/12] Perhitungan Deterministik HPP (/api/pricing/hpp)
  ✓ Analisis HPP & Margin Unit:
    - Bakpao Ayam (Reguler): HPP Rp 1,784 | Harga Saran Rp 2,500 | Margin 28.6% (Food Cost 71.4%)
    - Bakpao Ayam (Mini): HPP Rp 1,065 | Harga Saran Rp 1,500 | Margin 29.0% (Food Cost 71.0%)
    - Bakpao Coklat (Reguler): HPP Rp 1,805 | Harga Saran Rp 2,500 | Margin 27.8% (Food Cost 72.2%)

[Langkah 5/12] Simulasi Agen Repricing Pintar (/api/pricing/reprice)
  Simulasi kenaikan harga daging ayam +28.5% (Rp 35.000 -> Rp 45.000)...
  ✓ Ringkasan Keputusan: 2 varian Bakpao Ayam HPP naik 12.11% akibat kenaikan ayam, diputuskan REVIEW_SUPPLIER dengan tahan harga jual. 4 varian Coklat dan Kacang Hijau HPP 0% HOLD.
  ✓ Peringatan Vendor  : Harga ayam naik dari 35000 ke 45000, memicu HPP Bakpao Ayam Reguler dan Mini naik 12.11%. Evaluasi supplier ayam alternatif, negosiasi batch dan cek yield porsi untuk tekan food-cost.

[Langkah 6/12] Pembuatan Pesanan Pembeli (/api/orders)
  ✓ Pesanan Berhasil Dibuat: Kode [BQ-7TPHFA]
  ✓ Subtotal: Rp 9,500 | Kode Unik 3-Digit: 269
  ✓ Total Tagihan Exact: Rp 9.769 (Rp 9,769)
  ✓ URL Pembayaran: https://baiwormyid--bakpao.modal.run/pay/BQ-7TPHFA

[Langkah 7/12] Cek Status Pesanan (/api/orders/BQ-7TPHFA)
  ✓ Status Pesanan Saat Ini: MENUNGGU_BAYAR

[Langkah 8/12] Konfirmasi Mutasi QRIS Masuk (/api/orders/BQ-7TPHFA/paid)
  ✓ Status Berubah: LUNAS ✅
  ✓ Nomor Antrean Dapur: #3

[Langkah 9/12] Pemantauan Layar Dapur KDS (/api/kitchen/queue)
  ✓ Antrean aktif di dapur: 3 pesanan
  ✓ Pesanan [BQ-7TPHFA] terverifikasi masuk antrean produksi: True

[Langkah 10/12] Tombol Dapur: Siap Disajikan (/api/orders/BQ-7TPHFA/complete)
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
Total Durasi Pengujian: 8.31 detik
======================================================================
```
