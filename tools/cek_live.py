"""Cek kondisi live https://bakpao.my.id (atau --url lain).

Hanya memakai stdlib (urllib). Mencetak tabel PASS/FAIL + durasi per
pemeriksaan, diakhiri ringkasan "x/y lulus". Keluar kode 1 bila ada yang gagal.

Pakai:
    python tools/cek_live.py
    python tools/cek_live.py --url http://127.0.0.1:8000
"""
import argparse
import json
import sys
import time
import urllib.error
import urllib.request

UA = {"User-Agent": "curl/8.4.0"}
TIMEOUT = 20


def get(base, path):
    """Kembalikan (status, body_teks, detik). Status 0 = kegagalan jaringan."""
    t0 = time.time()
    try:
        req = urllib.request.Request(base + path, headers=UA)
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            body = r.read().decode("utf-8", "replace")
            return r.status, body, time.time() - t0
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", "replace")
        except Exception:
            body = ""
        return e.code, body, time.time() - t0
    except Exception as e:
        return 0, "ERROR: %r" % e, time.time() - t0


def main():
    ap = argparse.ArgumentParser(description="Cek kondisi live bakpao.my.id")
    ap.add_argument("--url", default="https://bakpao.my.id",
                    help="alamat URL (default https://bakpao.my.id)")
    args = ap.parse_args()
    base = args.url.rstrip("/")

    hasil = []  # (nama, lulus, detik, detail)

    def catat(nama, lulus, detik, detail=""):
        hasil.append((nama, lulus, detik, detail))

    for path in ("/", "/dapur", "/katalog"):
        st, _, dt = get(base, path)
        catat("GET %s -> 200" % path, st == 200, dt, "HTTP %s" % st)

    st, body, dt = get(base, "/api/health")
    ok = False
    try:
        ok = st == 200 and json.loads(body).get("ok") is True
    except ValueError:
        ok = False
    catat("GET /api/health -> ok", ok, dt, "HTTP %s" % st)

    st, body, dt = get(base, "/api/pricing/hpp")
    ok, detail = False, "HTTP %s" % st
    try:
        d = json.loads(body)
        prods = d.get("products", {})
        fc = [p.get("food_cost_pct") for p in prods.values()]
        ok = (st == 200 and len(prods) == 6
              and all(isinstance(v, (int, float)) and 30 <= v <= 80 for v in fc)
              and d.get("indeks_pasar", {}).get("ok") is True)
        detail = "produk=%d food_cost=%s indeks_ok=%s" % (
            len(prods), fc, d.get("indeks_pasar", {}).get("ok"))
    except ValueError as e:
        detail = "JSON rusak: %s" % e
    catat("GET /api/pricing/hpp -> 6 produk", ok, dt, detail)

    st, body, dt = get(base, "/api/kitchen/queue")
    ok = False
    try:
        ok = st == 200 and "queue" in json.loads(body)
    except ValueError:
        ok = False
    catat("GET /api/kitchen/queue -> queue", ok, dt, "HTTP %s" % st)

    print("%-38s %-6s %8s  %s" % ("PEMERIKSAAN", "HASIL", "DETIK", "DETAIL"))
    lulus = 0
    for nama, ok_, dt, detail in hasil:
        print("%-38s %-6s %8.2f  %s"
              % (nama, "PASS" if ok_ else "FAIL", dt, detail))
        lulus += ok_
    print("%d/%d lulus" % (lulus, len(hasil)))
    return 0 if lulus == len(hasil) else 1


if __name__ == "__main__":
    sys.exit(main())
