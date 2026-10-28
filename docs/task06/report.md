# Laporan — TASK 05b SAM 3.1 frasa

```
TASK: 05b — SAM 3.1 frasa
STATUS: PASS
PYTEST: 74 passed in 1.10s (EXIT=0; 7 test sam3 baru, lama tetap hijau)
PARSE: 1 box: x1=299 x2=543 w=600 (fixture asli spec)
REAL_CALL: 8 box | pertama x1=299 y1=148 x2=543 y2=361 w=600 h=450 | raw_chars=58292 | 1 panggilan dari jatah 2 (~$0,02)
BACKEND: sam21 tidak berubah? ya (default tanpa points tetap titik_hilang)
FILES: src/services/sam3_client.py, tests/test_sam3_client.py, src/api/routes.py, docs/task06/report.md
NOTES: box_diameter_px di spec tertulis 178.5 untuk contoh itu, tetapi rumus
  di spec yang sama ((x2-x1)+(y2-y1))/2 memberi 228.5 ((543-299)+(361-148))/2.
  Rumus yang dipakai; test menegaskan 228.5. Tanpa scale_cm endpoint
  mengembalikan diameter_px (cermin pola sam21: tanpa acuan cm, angka piksel
  saja). pytest perlu --basetemp ke dir temp baru karena dir pytest-of-Wijang
  di TEMP terkunci (masalah mesin, bukan kode; tanpa tmp_path semua hijau).
BLOCKERS: none
```
