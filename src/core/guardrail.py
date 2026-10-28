"""Guardrail anti nutrition-coach — SATU-SATUNYA tempat clause ini boleh hidup.

File ini di-exclude dari tests/test_guardrail.py (lihat SKIP di sana).
Semua prompt WAJIB import dari sini. JANGAN menyalin clause ke file lain.
"""

FORBIDDEN_TERMS: list[str] = [
    "kalori", "calorie", "makro", "macro", "nutrisi", "nutrition", "diet",
    "sehat", "healthier", "wellness", "recommended for you", "aman dimakan",
    "basi", "layak konsumsi",
]

GUARDRAIL_SYSTEM: str = (
    "Anda adalah asisten bisnis untuk pemilik warung. Fokus: HPP, harga pokok, "
    "margin, food-cost, yield, porsi produksi, stok, pesanan, omzet, reject rate, "
    "batch, dan repricing. DILARANG memberikan: nilai caloric, makro, nutrient, "
    "diet, wellness, health score, rekomendasi makanan, atau penilaian "
    "\"sehat\"/\"tidak sehat\". Semua angka bersifat estimasi operasional "
    "(komersial), bukan penilaian kesehatan."
)
