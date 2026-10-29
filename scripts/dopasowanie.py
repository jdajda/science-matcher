import html as h
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

STOP = set("""
a aby albo and are as at be by for from in is it of on or that the this to with
will which their its into within using use based through also each such other
project projects topic proposal proposals call action actions research innovation
expected outcome outcomes scope scopes eligibility must should shall may
advanced local global new novel high level development methods method approach
approaches system systems solution solutions application applications tools tool
support supporting especially including include includes related area areas
oraz lub na do w z i o od po przez dla jest czy jak
""".split())

SOURCE_WEIGHT = {"topic": 3, "keyword": 2, "work": 1}
PALETTE = ['#5f8fc4','#7b7ec4','#b06b9c','#b08a4a','#5f9e80','#b35f62','#8a74bd','#5f9fa8','#b07a55','#9a6fb3','#6a8fbd','#6fa06f','#a8944c','#b0557a','#4f9d95','#8c7cbf','#b38a4c','#4f9d74','#7a6cbf','#9a6f96','#5f96bf','#b0566e','#6f7790','#4f5f8c']


def fold(text):
    text = unicodedata.normalize("NFKD", text)
    return "".join(c for c in text if not unicodedata.combining(c)).lower()


def tokens(text):
    return [t for t in re.findall(r"[a-z0-9]{3,}", fold(text)) if t not in STOP]


def profile_terms(profile):
    terms = {}
    for t in profile.get("topics", []):
        for tok in set(tokens(t["name"])):
            terms.setdefault(tok, []).append(("topic", t["name"]))
    for w in profile.get("works", []):
        for k in w.get("keywords", []):
            for tok in set(tokens(k)):
                terms.setdefault(tok, []).append(("keyword", k))
        for tok in set(tokens(w.get("title") or "")):
            terms.setdefault(tok, []).append(("work", w["title"]))
    return terms


def score(topic_tokens, profile):
    terms = profile_terms(profile)
    wanted = set(topic_tokens)
    hits = []
    total = 0
    for tok in sorted(wanted):
        if tok in terms:
            kinds = {}
            for kind, label in terms[tok]:
                kinds.setdefault(kind, label)
            best = max(kinds, key=lambda k: SOURCE_WEIGHT[k])
            total += SOURCE_WEIGHT[best]
            hits.append({"token": tok, "source": best, "evidence": kinds[best]})
    coverage = len(hits) / len(wanted) if wanted else 0
    return total, coverage, hits






def initials(name):
    parts = [p for p in re.split(r"\s+", name) if p]
    return "".join(p[0] for p in parts[:2]).upper()


BIURO_ONLY = {"projekty"}
NAV = [
    ("Naukowcy", "index.html", "naukowcy"),
    ("Projekty", "biuro.html", "projekty"),
    ("Zaproszenia", "panel.html", "panel"),
    ("Słowniki", "slowniki.html", "slowniki"),
]


def local_nav(items, mode="link"):
    if mode == "button":
        btns = "".join(
            f'<button class="tab seg-btn{" active" if i == 0 else ""}" type="button" data-view="{h.escape(key)}">{h.escape(label)}</button>'
            for i, (key, label) in enumerate(items)
        )
    else:
        btns = "".join(
            f'<a class="tab seg-btn{" active" if i == 0 else ""}" href="#{h.escape(key)}">{h.escape(label)}</a>'
            for i, (key, label) in enumerate(items)
        )
    return f'<div class="seg-bar" role="navigation" aria-label="Widoki strony"><div class="container seg-row">{btns}</div></div>'


def toggle_html():
    src = (ROOT / "index.html").read_text(encoding="utf-8")
    m = re.search(r'<button class="theme-toggle".*?</button>', src, flags=re.S)
    return m.group(0) if m else ""


def nav_html(active):
    items = ['<a class="tab" href="profil.html" data-role-only="naukowiec">Mój profil</a>']
    for label, href, key in NAV:
        cur_cls = " active" if key == active else ""
        cur_attr = ' aria-current="page"' if key == active else ""
        role_attr = ' data-role-only="biuro"' if key in BIURO_ONLY else ""
        items.append(f'<a class="tab{cur_cls}" href="{href}"{cur_attr}{role_attr}>{label}</a>')
    return f'<nav class="tabs" aria-label="Menu główne"><div class="container tabs-row">{"".join(items)}</div></nav>'


def site_parts():
    src = (ROOT / "index.html").read_text(encoding="utf-8")
    head_end = src.index("</style>") + len("</style>")
    head = src[: src.index("<body>")]
    head = head[: head.index("</head>")] if "</head>" in head else head
    head = src[:head_end]
    header_start = src.index('<header class="site-header">')
    header_end = src.index("</header>", header_start) + len("</header>")
    header = src[header_start:header_end]
    theme_start = src.index("var KEY='bm-theme-v2';")
    theme_start = src.rindex("<script>", 0, theme_start)
    theme_end = src.index("</script>", theme_start) + len("</script>")
    theme_js = src[theme_start:theme_end]
    head = re.sub(r"<title>.*?</title>", "<title>Dopasowanie do naboru · Mapa badawcza WI AGH</title>", head, count=1)
    head = head.replace("localStorage.getItem('bm-theme')||'light'", "localStorage.getItem('bm-theme')||'dark'", 1)
    head = head.replace("document.documentElement.dataset.theme='light';}", "document.documentElement.dataset.theme='dark';}", 1)
    header = re.sub(r"<nav class=\"tabs\">.*?</nav>", "", header, flags=re.S)
    header = re.sub(r"<nav class=\"subtabs\">.*?</nav>", "", header, flags=re.S)
    header = re.sub(r'<div class="seg-bar">.*?(?=</header>)', "", header, flags=re.S)
    theme_js = theme_js + '\n<script src="assets/app.js"></script>'
    return head, header, theme_js











def person_area_colors():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    m = re.search(r'<script id="app-data" type="application/json">(.*?)</script>', html, re.S)
    if not m:
        return {}
    data = json.loads(m.group(1))
    area_ids = [a["id"] for a in data.get("areas", [])]
    area_color = {aid: PALETTE[i % len(PALETTE)] for i, aid in enumerate(area_ids)}
    out = {}
    for st in data.get("staff", []):
        areas = st.get("areas") or []
        if areas and areas[0].get("id") in area_color:
            out[st["name"]] = area_color[areas[0]["id"]]
    return out














