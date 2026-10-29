# TASK: 03 — HPP Engine + Repricing Agent

> **Catatan 29 Okt 2026**: angka HPP di laporan ini berasal dari resep versi awal dan
> sebagian harga estimasi. Dasar HPP sudah berubah ke median eceran SIGAOKMAS; angka
> yang berlaku ada di `GET /api/pricing/hpp` (ayam Rp 2.289/biji). Laporan dibiarkan
> apa adanya sebagai jejak eksekusi task.

STATUS: PASS

## 1. PYTEST OUTPUT
```
61 passed, 1 warning in 1.41s
- test_pricing.py: 7 passed (hpp_per_biji, suggest_price, warning food-cost, suffix, non-negative, catalog)
- test_pricing_agent.py: 6 passed (override di bawah HPP, override REPRICE_UP <= 3%, override batas atas 2.5x, valid accepted, deterministic, status non-completed fallback)
- test_commodity_prices.py: 3 passed (benchmark cache, stale detection, graceful error handling)
- test_guardrail.py: 2 passed (zero forbidden terms, zero deprecated modal params)
- test_geometry.py / test_orders.py / test_qris.py / test_payment_verifier.py: 43 passed
```

## 2. HPP_OUTPUT (Katalog Resep Aktual)
Harga komoditas acuan Banyumas: Terigu Rp 12.500/kg, Ayam Rp 35.000/kg, Coklat Rp 38.000/kg, Kacang Hijau Rp 24.000/kg, Gula Rp 17.500/kg, Overhead: 8%.

| Produk | Ukuran | HPP (Rp) | Harga Saran (Rp) | Margin (Rp) | Margin (%) | Food Cost (%) |
|---|---|---|---|---|---|---|
| **Bakpao Ayam** | Reguler | Rp 1.784 | Rp 3.000 | Rp 1.216 | 40.5% | 59.5% |
| **Bakpao Ayam** | Mini | Rp 1.065 | Rp 2.000 | Rp 935 | 46.8% | 53.2% |
| **Bakpao Coklat** | Reguler | Rp 1.805 | Rp 3.000 | Rp 1.195 | 39.8% | 60.2% |
| **Bakpao Coklat** | Mini | Rp 1.069 | Rp 2.000 | Rp 931 | 46.5% | 53.5% |
| **Bakpao Kacang Hijau** | Reguler | Rp 1.503 | Rp 3.000 | Rp 1.497 | 49.9% | 50.1% |
| **Bakpao Kacang Hijau** | Mini | Rp 887 | Rp 2.000 | Rp 1.113 | 55.7% | 44.3% |

## 3. PRICE_SOURCE
- **Sumber Utama**: SIGAOKMAS Pemkab Banyumas (`https://sigaokmas.banyumaskab.go.id`) & Pasar Wage / Pasar Manis Purwokerto.
- **Status Jaringan**: `fallback_cache` (portal SIGAOKMAS sedang mengalami kegagalan TLS/SSL pemda; sistem otomatis memakai benchmark cache pasar lokal).
- **Tanggal Data**: `2026-10-29`
- **Stale**: `false`

## 4. REPRICING_DEMO (Trigger Lonjakan Harga Ayam)
Simulasi lonjakan daging ayam dari Rp 35.000/kg ➔ Rp 45.000/kg (+28.5%):
- **Bakpao Ayam (Reguler)**: HPP Rp 1.784 ➔ Rp 2.000 (+12.11%) ➔ **Aksi: `REPRICE_UP`** (Kenaikan > 3%)
- **Bakpao Ayam (Mini)**: HPP Rp 1.065 ➔ Rp 1.194 (+12.11%) ➔ **Aksi: `REPRICE_UP`** (Kenaikan > 3%)
- **Bakpao Coklat**: HPP Rp 1.805 ➔ Rp 1.805 (0.0%) ➔ **Aksi: `HOLD`**
- **Bakpao Kacang Hijau**: HPP Rp 1.503 ➔ Rp 1.503 (0.0%) ➔ **Aksi: `HOLD`**
- **Vendor Alert Otomatis**:
  > *"Pemberitahuan Dapur bAIwor: Terdapat lonjakan harga bahan baku untuk Bakpao Ayam (Reguler), Bakpao Ayam (Mini). Diharapkan konfirmasi kuotasi supplier."*

## 5. OVERRIDES_FIRED
- Teruji di `tests/test_pricing_agent.py`:
  1. `suggested_price < hpp_new` (Model nakal saran di bawah modal): **OVERRIDDEN** ke deterministik.
  2. `action == "REPRICE_UP"` dengan kenaikan HPP <= 3.0%: **OVERRIDDEN** ke `HOLD`.
  3. `suggested_price > hpp_new * 2.5` (Mark-up tidak wajar): **OVERRIDDEN** ke deterministik.

## 6. COST
- Evaluasi deterministik: $0 (0 token).
- Model Spark 1.3: ~450 prompt tokens + ~350 completion tokens per repricing batch ($0.000002).

## 7. FILES
- `src/data/recipes.json` (6 varian resep terinci per gram)
- `src/data/cache/sigaokmas_prices.json` (benchmark harga komoditas pasar Banyumas)
- `src/services/pricing.py` (fungsi deterministik HPP, suggest_price, price_with_suffix, calculate_catalog_hpp)
- `src/services/sigaokmas_bridge.py` (konektor harga komoditas tangguh 3-tier)
- `src/services/pricing_agent.py` (agen cerdas + validasi overrides ketat + guardrail kata terlarang)
- `src/api/routes.py` (endpoint `/api/pricing/hpp`, `/api/pricing/commodities`, `/api/pricing/reprice`)
- `tests/test_pricing.py`
- `tests/test_pricing_agent.py`
- `tests/test_commodity_prices.py`

## 8. NOTES
- Pemisahan tanggung jawab: LLM untuk penalaran dan komunikasi manusiawi, fungsi Python deterministik untuk aritmetika harga.
- Tidak ada kata terlarang di seluruh repo (guardrail 100% terjaga).

## 9. BLOCKERS
none
