"""Pobiera stopnie naukowe z SKOS AGH (źródło nadrzędne) dla pracowników WI.

Wynik: data/skos_stopnie.json  {nazwa: {"stopien": ..., "zrodlo": url, "pobrano": data}}
Stopień jest wyciągany z tytułu strony SKOS: "dr hab. inż. Jacek  Dajda — SkOs AGH".
"""
import datetime
import html as h
import json
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.html"
OUT = ROOT / "data" / "skos_stopnie.json"


def staff_from_index():
    src = INDEX.read_text(encoding="utf-8")
    m = re.search(r'<script id="app-data" type="application/json">(.*?)</script>', src, re.S)
    return json.loads(m.group(1))["staff"]


def fetch_title(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=40) as r:
        page = r.read().decode("utf-8", "replace")
    m = re.search(r"<title>(.*?)</title>", page, re.S)
    return h.unescape(m.group(1)) if m else ""


DEGREE_WORDS = {"prof.", "dr", "hab.", "hab", "inż.", "inż", "mgr", "lic.", "lic", "dr."}


def degree_from_title(title):
    # tytuł zaczyna się stopniem: "dr hab. inż. Jacek Dajda"; imię i nazwisko zostają poza stopniem
    t = re.sub(r"\s*—.*$", "", title).strip()
    tokens = re.sub(r"\s+", " ", t).split(" ")
    out = []
    for tok in tokens:
        if tok.lower() in DEGREE_WORDS:
            out.append(tok)
        else:
            break
    return " ".join(out)


def one(st):
    url = st.get("skos")
    if not url:
        return st["name"], None
    try:
        title = fetch_title(url)
        deg = degree_from_title(title)
        return st["name"], {"stopien": deg, "zrodlo": url, "tytul_strony": title,
                            "pobrano": datetime.date.today().isoformat()}
    except Exception as e:  # sieć / zmiana strony: zostaje stara wartość
        return st["name"], {"blad": str(e)[:120], "zrodlo": url}


def main():
    staff = staff_from_index()
    with ThreadPoolExecutor(max_workers=8) as ex:
        results = dict(ex.map(one, staff))
    ok = {k: v for k, v in results.items() if v and v.get("stopien")}
    OUT.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"pobrano stopnie: {len(ok)} z {sum(1 for s in staff if s.get('skos'))} stron SKOS")
    return 0


if __name__ == "__main__":
    main()
