"""Odświeża nabory Horyzontu z SEDIA i zapisuje datę aktualizacji.

Uruchamiany co 14 dni (patrz scripts/pl.science-macher.nabory.plist).
Ręcznie: python3 scripts/odswiez_nabory.py
"""
import datetime
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import pobierz_nabory as pn  # noqa: E402

PREFIXES = [
    "HORIZON-CL2-2026", "HORIZON-CL2-2027",
    "HORIZON-CL3-2026", "HORIZON-CL3-2027",
    "HORIZON-CL4-2026", "HORIZON-CL4-2027",
    "HORIZON-CL5-2026", "HORIZON-CL5-2027",
    "HORIZON-CL6-2026", "HORIZON-CL6-2027",
    "HORIZON-MSCA-2026", "HORIZON-MSCA-2027",
    "HORIZON-WIDERA-2026", "HORIZON-WIDERA-2027",
]
DATA = ROOT / "data" / "nabory_sedia.json"
META = ROOT / "data" / "nabory_aktualizacja.json"


def main():
    today = datetime.date.today().isoformat()
    texts = {}
    fetched = {}
    for prefix in PREFIXES:
        found = pn.collect(prefix, 2, texts)
        print(f"{prefix}: tematów {len(found)}")
        fetched.update(found)

    if not fetched:
        print("Nie pobrano żadnych tematów. Dane nie zostały zmienione.")
        return 1

    current = {t["id"]: t for t in json.loads(DATA.read_text(encoding="utf-8"))} if DATA.exists() else {}
    for tid, t in fetched.items():
        t["status"] = pn.topic_status(tid, t["call"], texts)
        current[tid] = t  # nowsza wersja nadpisuje starą; tematy, których API nie zwróciło, zostają

    items = sorted(current.values(), key=lambda t: (t["call"], t["id"]))
    DATA.write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
    META.write_text(json.dumps({
        "aktualizacja": today,
        "tematow": len(items),
        "naborow": len({t["call"] for t in items}),
        "zrodlo": "SEDIA (api.tech.ec.europa.eu)",
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"zapisano {len(items)} tematów, {len({t['call'] for t in items})} naborów, data {today}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
