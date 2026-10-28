"""Guardrail repo: tidak ada kata terlarang di .py/.html/.js/.json/.md.

File ini + src/core/guardrail.py di-exclude (clause hidup di sana saja).
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SELF = Path(__file__).resolve()
FORBIDDEN = ["kalori", "calorie", "makro", "macro", "nutrisi", "nutrition",
             "diet", "sehat", "healthier", "wellness", "recommended for you",
             "aman dimakan", "basi", "layak konsumsi"]
SCAN_EXT = {".py", ".html", ".js", ".json", ".md"}
GUARDRAIL_FILE = ROOT / "src" / "core" / "guardrail.py"
SKIP = {SELF, GUARDRAIL_FILE}


def violations():
    out = []
    for p in ROOT.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in SCAN_EXT:
            continue
        if p.resolve() in SKIP:
            continue
        for i, line in enumerate(
                p.read_text(encoding="utf-8", errors="ignore").splitlines(),
                1):
            low = line.lower()
            for w in FORBIDDEN:
                if w in low:
                    out.append(f"{p.relative_to(ROOT)}:{i}: "
                               f"'{w}' -> {line.strip()[:80]}")
    return out


def test_no_forbidden_words():
    v = violations()
    assert not v, "Kata terlarang ditemukan:\n" + "\n".join(v)


def test_no_deprecated_modal_param():
    hits = [f"{p.relative_to(ROOT)}" for p in ROOT.rglob("*.py")
            if "container_idle_timeout" in p.read_text(
                encoding="utf-8", errors="ignore")
            and p.resolve() not in SKIP]
    assert not hits, f"container_idle_timeout deprecated: {hits}"
