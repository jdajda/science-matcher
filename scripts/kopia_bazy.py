"""Kopia zapasowa bazy serwera (data/baza.sqlite) do data/kopie/.

Uruchomienie: python3 scripts/kopia_bazy.py
Zostawia 30 ostatnich kopii. Bezpieczne także przy działającym serwerze (API kopii SQLite).
"""
import datetime
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "baza.sqlite"
DST_DIR = ROOT / "data" / "kopie"
KEEP = 30


def main():
    if not SRC.exists():
        print("Brak bazy do skopiowania:", SRC)
        return 1
    DST_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    dst = DST_DIR / f"baza-{stamp}.sqlite"
    src = sqlite3.connect(SRC)
    out = sqlite3.connect(dst)
    with out:
        src.backup(out)
    out.close()
    src.close()
    kopie = sorted(DST_DIR.glob("baza-*.sqlite"))
    for old in kopie[:-KEEP]:
        old.unlink()
    print(f"zapisano kopię: {dst} (przechowywane: {min(len(kopie), KEEP)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
