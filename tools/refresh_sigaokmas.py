"""CLI: ambil harga SIGAOKMAS Kab. Banyumas → src/data/cache/sigaokmas/.

Logika ada di src/services/sigaokmas_fetch.py (dipakai juga oleh cron Modal).

Pemakaian:
    python tools/refresh_sigaokmas.py
    python tools/refresh_sigaokmas.py --days 14 --markets "" 4 5
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.services.sigaokmas_fetch import refresh  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7, help="jumlah hari ke belakang (berakhir H-1)")
    ap.add_argument("--markets", nargs="*", default=None, help='id pasar; "" = kabupaten')
    args = ap.parse_args()

    hasil = refresh(days=args.days, markets=args.markets)
    if not hasil["ok"]:
        print(f"Gagal: {hasil}", file=sys.stderr)
        return 1

    print(f"{hasil['baris']} baris -> {Path(hasil['out_dir']) / 'prices_raw.csv'}")
    print(f"periode {hasil['periode']['dari']}..{hasil['periode']['sampai']} "
          f"mode={','.join(hasil['mode_ambil'])} cakupan={hasil['cakupan']}")
    if hasil["gagal"]:
        print(f"gagal: {hasil['gagal']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
