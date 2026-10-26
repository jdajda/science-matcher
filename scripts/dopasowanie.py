import argparse
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
SCORE_COLOR = "#4f7fb0"
SOURCE_LABEL = {"topic": "temat badawczy", "keyword": "słowo kluczowe", "work": "tytuł pracy"}


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


def person_color(field):
    if not field:
        return "#6b7280"
    return PALETTE[sum(ord(c) for c in field) % len(PALETTE)]


def coverage_color(cov):
    if cov >= 0.5:
        return "#5f9e80"
    if cov >= 0.25:
        return "#b08a4a"
    return "#b06464"


def initials(name):
    parts = [p for p in re.split(r"\s+", name) if p]
    return "".join(p[0] for p in parts[:2]).upper()


def site_parts():
    src = (ROOT / "index.html").read_text(encoding="utf-8")
    head_end = src.index("</style>") + len("</style>")
    head = src[: src.index("<body>")]
    head = head[: head.index("</head>")] if "</head>" in head else head
    head = src[:head_end]
    header_start = src.index('<header class="site-header">')
    header_end = src.index("</header>", header_start) + len("</header>")
    header = src[header_start:header_end]
    theme_start = src.index("var KEY='bm-theme';")
    theme_start = src.rindex("<script>", 0, theme_start)
    theme_end = src.index("</script>", theme_start) + len("</script>")
    theme_js = src[theme_start:theme_end]
    head = re.sub(r"<title>.*?</title>", "<title>Dopasowanie do naboru · Mapa badawcza WI AGH</title>", head, count=1)
    head = head.replace("localStorage.getItem('bm-theme')||'light'", "localStorage.getItem('bm-theme')||'dark'", 1)
    head = head.replace("document.documentElement.dataset.theme='light';}", "document.documentElement.dataset.theme='dark';}", 1)
    header = re.sub(r"<nav class=\"tabs\">.*?</nav>", "", header, flags=re.S)
    return head, header, theme_js


def card(i, r):
    orcid = r.get("orcid")
    link = (
        f"<a class='s-link' href='{h.escape(orcid)}' target='_blank' rel='noopener'>ORCID →</a>"
        if orcid else "<span class='s-link'>ORCID brak</span>"
    )
    kws = "".join(f"<span class='kw'>{h.escape(x['token'])}</span>" for x in r["hits"][:6])
    pct = round(r["coverage"] * 100)
    text = " ".join([r["wi_name"], r.get("openalex_name") or "", r.get("field") or ""] + [x["token"] for x in r["hits"]]).lower()
    return f"""
    <article class="staff-card" data-text="{h.escape(text)}">
      <div class="s-head">
        <div class="s-av">{h.escape(initials(r['wi_name']))}</div>
        <div class="s-id">
          <h3>{i}. {h.escape(r['wi_name'])}</h3>
          <div class="s-sub">{h.escape(r.get('openalex_name') or '')}</div>
          <div class="s-sub">{h.escape(r.get('field') or '')}</div>
        </div>
      </div>
      <div class="s-pills">
        <span class="s-pill">wynik {r['score']}</span>
        <span class="s-pill">pokrycie {pct}%</span>
        {f"<span class='s-pill' style='--c:{person_color(r.get('field'))}'>{h.escape(r.get('field'))}</span>" if r.get('field') else ""}
      </div>
      {f"<div class='s-kw'>{kws}</div>" if kws else ""}
      <div class="s-foot"><span>{r['score']} trafień z tematu</span>{link}</div>
    </article>"""


TERM_STYLE = {
    "digital": "--c:#4f7fb0;color:#4f7fb0;font-weight:600",
    "early": "--c:#5f9e80;color:#5f9e80;font-weight:600",
}


def section(call_id, nabor, out):
    terms = "".join(
        f"<span class='s-pill' style='{TERM_STYLE.get(t, '')}'>{h.escape(t)}</span>" for t in out["topic_terms"][:8]
    )
    cards = "".join(card(i, r) for i, r in enumerate(out["top"], 1))
    return f"""
  <section class="call-section" id="{h.escape(call_id)}" style="margin-bottom:2.2rem">
    <div class="eyebrow">Słowa z projektu i publikacji · nabór</div>
    <h2 class="hero-title" style="font-size:1.35rem">{h.escape(call_id)}</h2>
    <p class="hero-sub">{h.escape(nabor)}</p>
    <div class="stats-bar" style="margin:1rem 0">
      <span class="stat"><b>{out['matched_people']}</b> osób z trafieniem</span>
      <span class="stat">w profilach: <b>{out.get('profiles_total', '')}</b></span>
      <span class="stat">pokazano: <b>{len(out['top'])}</b></span>
    </div>
    <div class="side-card" style="position:static;max-height:none;margin-bottom:1.2rem">
      <div class="side-head"><h3>Terminy z tematu</h3></div>
      <div class="s-pills">{terms}</div>
      <p class="side-note" style="margin-top:.8rem">{h.escape(out['uwaga'])}</p>
    </div>
    <div class="staff-list">{cards}
    </div>
  </section>"""


CONCEPT_PL = {
    "digital twin": "cyfrowy bliźniak",
    "early warning": "wczesne ostrzeganie",
    "disaster risk": "ryzyko katastrof",
    "machine learning": "uczenie maszynowe",
    "urban planning": "planowanie miejskie",
}


def topic_section(path):
    if not Path(path).exists():
        return ""
    res = json.loads(Path(path).read_text(encoding="utf-8"))
    top = res.get("top", [])[:10]
    if not top:
        return ""
    best = top[0]["wynik"] or 1
    cards = []
    for i, r in enumerate(top, 1):
        ev = []
        for x in r["pojecia"]:
            d = x.get("dowod")
            if d:
                ev.append(f"<li><b>{h.escape(CONCEPT_PL.get(x['pojecie'], x['pojecie']))}</b> ← {h.escape(d['temat'])}</li>")
        text = " ".join([r["wi_name"]] + [x["pojecie"] for x in r["pojecia"] if x.get("dowod")]).lower()
        cards.append(f"""
    <article class="staff-card" data-text="{h.escape(text)}">
      <div class="s-head">
        <div class="s-av">{h.escape(initials(r['wi_name']))}</div>
        <div class="s-id"><h3>{i}. {h.escape(r['wi_name'])}</h3></div>
      </div>
      <div class="s-pills">
        <span class="s-pill">wynik {round(r['wynik'] / best * 100)}%</span>
        <span class="s-pill">pokrycie {round(r['pokrycie'] * 100)}%</span>
      </div>
      <ul class="s-kw" style="padding-left:1.1rem">{''.join(ev) or '<li>brak dowodów</li>'}</ul>
    </article>""")
    return f"""
  <section class="call-section" id="tematy" style="margin-bottom:2.2rem">
    <div class="eyebrow">Dopasowanie po tematach OpenAlex</div>
    <h2 class="hero-title" style="font-size:1.35rem">{h.escape(res.get('nabor') or '')}</h2>
    <p class="hero-sub">Wstępne: mapowanie pojęć wybrałam sama, do potwierdzenia przez biuro. Wyniki są względne.</p>
    <div class="staff-list">{''.join(cards)}
    </div>
  </section>"""


OWN_JS = """
(function(){
  const STOP = new Set(__STOP__);
  const PROFILES = __PROFILES__;
  const kw = document.getElementById('kw');
  const boxes = document.querySelectorAll('.sec-cb, .m-cb');
  function apply(){
    const q = kw.value.trim().toLowerCase();
    document.querySelectorAll('.sec').forEach(sec => {
      const m = document.querySelector('.m-cb[value="' + sec.dataset.method + '"]');
      const n = sec.dataset.method === 'slowa' ? document.querySelector('.sec-cb[value="' + sec.dataset.sec + '"]') : null;
      const on = (!m || m.checked) && (!n || n.checked);
      sec.style.display = on ? '' : 'none';
      sec.querySelectorAll('.staff-card').forEach(c => {
        c.style.display = (!q || c.dataset.text.includes(q)) ? '' : 'none';
      });
    });
  }
  function fold(s){ return s.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase(); }
  function toks(s){ return (fold(s).match(/[a-z0-9]{3,}/g) || []).filter(t => !STOP.has(t)); }
  function esc(s){ return String(s == null ? '' : s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
  function initials(n){ return n.split(/\s+/).filter(Boolean).slice(0,2).map(p => p[0]).join('').toUpperCase(); }
  const W = {topic: 3, keyword: 2, work: 1};
  function score(desc){
    const wanted = [...new Set(toks(desc))];
    const rows = [];
    PROFILES.forEach(p => {
      const terms = {};
      const add = (tok, kind, label) => {
        if (!terms[tok] || terms[tok].w < W[kind]) terms[tok] = {w: W[kind], kind: kind, label: label};
      };
      p.t.forEach(name => toks(name).forEach(tok => add(tok, 'topic', name)));
      p.w.forEach(work => {
        work[1].forEach(k => toks(k).forEach(tok => add(tok, 'keyword', k)));
        toks(work[0]).forEach(tok => add(tok, 'work', work[0]));
      });
      let total = 0; const hits = [];
      wanted.forEach(tok => {
        const t = terms[tok];
        if (t) { total += t.w; hits.push({token: tok, source: t.kind, evidence: t.label}); }
      });
      if (total > 0) rows.push({p: p, total: total, hits: hits});
    });
    rows.sort((a, b) => b.total - a.total);
    return rows.slice(0, 10);
  }
  function render(desc){
    const box = document.getElementById('own-results');
    if (!desc.trim()) { box.innerHTML = '<p class="hero-sub">Wpisz opis po lewej i kliknij „Dopasuj”.</p>'; apply(); return; }
    const rows = score(desc);
    if (!rows.length) { box.innerHTML = '<p class="hero-sub">Brak trafień. Spróbuj innych słów kluczowych.</p>'; apply(); return; }
    const best = rows[0].total;
    box.innerHTML = '<div class="staff-list">' + rows.map((r, i) => {
      const pct = Math.round(r.total / best * 100);
      const kws = r.hits.slice(0, 6).map(h => "<span class='kw'>" + esc(h.token) + "</span>").join('');
      const text = [r.p.n, r.p.o, r.p.f].concat(r.hits.map(h => h.token)).join(' ').toLowerCase();
      const link = r.p.r ? "<a class='s-link' href='" + esc(r.p.r) + "' target='_blank' rel='noopener'>ORCID →</a>" : "<span class='s-link'>ORCID brak</span>";
      return "<article class='staff-card' data-text='" + esc(text) + "'>" +
        "<div class='s-head'><div class='s-av'>" + esc(initials(r.p.n)) + "</div>" +
        "<div class='s-id'><h3>" + (i + 1) + ". " + esc(r.p.n) + "</h3><div class='s-sub'>" + esc(r.p.o || '') + "</div>" +
        "<div class='s-sub'>" + esc(r.p.f || '') + "</div></div></div>" +
        "<div class='s-pills'><span class='s-pill'>wynik " + pct + "%</span></div>" +
        "<div class='s-kw'>" + kws + "</div>" +
        "<div class='s-foot'>" + link + "</div></article>";
    }).join('') + '</div>';
    apply();
  }
  const ta = document.getElementById('own-text');
  document.getElementById('own-btn').addEventListener('click', () => render(ta.value));
  ta.addEventListener('keydown', e => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) render(ta.value); });
  kw.addEventListener('input', apply);
  boxes.forEach(b => b.addEventListener('change', apply));
})();
"""


def calendar_section():
    import collections
    import datetime
    today = datetime.date(2026, 10, 26).isoformat()
    items = json.loads((ROOT / "data/nabory_sedia.json").read_text(encoding="utf-8"))
    groups = collections.defaultdict(list)
    for t in items:
        groups[t["call"]].append(t)
    rows = []
    for call, topics in groups.items():
        starts = [t["start"][:10] for t in topics if t.get("start")]
        start = min(starts) if starts else ""
        deadlines = sorted({d for t in topics for d in (t.get("terminy") or [])})
        last = deadlines[-1] if deadlines else ""
        if last and last < today:
            status = "zamknięty"
        elif start and start > today:
            status = "planowany"
        elif start and last and start <= today <= last:
            status = "otwarty"
        else:
            status = "sprawdzić"
        rows.append((status != "otwarty", deadlines[0] if deadlines else "9999", call, start, deadlines, status, len(topics)))
    rows.sort()
    cards = []
    for _, _, call, start, deadlines, status, n in rows:
        term = " · ".join(deadlines) if deadlines else "brak danych"
        cards.append(
            f'<div class="member-row"><div class="m-info"><div class="m-name">{h.escape(call)}</div>'
            f'<div class="m-pubs">otwarcie: {h.escape(start or "brak")} · tematów: {n}</div></div>'
            f'<div class="m-score-num">{h.escape(status)} · termin: {h.escape(term)}</div></div>'
        )
    return (
        '<div class="sec" data-sec="kalendarz" data-method="kalendarz">'
        '<section class="call-section" id="kalendarz" style="margin-bottom:2.2rem">'
        '<div class="eyebrow">Kalendarz naborów</div>'
        '<h2 class="hero-title" style="font-size:1.35rem">Nabory 2027</h2>'
        '<p class="hero-sub">Dane z SEDIA, stan na 26.10.2026. Przy naborach dwuetapowych podano dwa terminy.</p>'
        + "".join(cards) +
        '</section></div>'
    )


def render_html(sections):
    head, header, theme_js = site_parts()
    tabs = """
<nav class="tabs">
  <div class="container tabs-row">
    <a class="tab" href="index.html#staff">Naukowcy</a>
    <a class="tab" href="index.html#areas">Obszary badawcze</a>
    <a class="tab active" href="dopasowanie.html">Nabory i dopasowanie</a>
    <a class="tab" href="biuro.html">Projekty</a>
    <a class="tab" href="index.html#graph">Graf współpracy</a>
  </div>
</nav>"""
    topic_html = topic_section(ROOT / "data/dopasowanie_tematy_HORIZON-CL4-2026-04-DIGITAL-EMERGING-09.json")
    blocks = [calendar_section()]
    if topic_html:
        blocks.append(f'<div class="sec" data-sec="tematy" data-method="tematy">{topic_html}</div>')
    blocks += [f'<div class="sec" data-sec="{h.escape(sec[0])}" data-method="slowa">{section(*sec)}</div>' for sec in sections]
    blocks.insert(0, '<div class="sec" data-sec="wlasny" data-method="wlasny"><section class="call-section" id="wlasny" style="margin-bottom:2.2rem"><div class="eyebrow">Wpisz projekt · słowa z publikacji</div><h2 class="hero-title" style="font-size:1.35rem">Wpisz projekt</h2><div id="own-results"><p class="hero-sub">Wpisz opis po lewej i kliknij „Dopasuj”.</p></div></section></div>')
    body = "".join(blocks)
    calls_filter = "".join(
        f'<label class="f-check"><input type="checkbox" class="sec-cb" value="{h.escape(cid)}" checked> {h.escape(cid)}</label>'
        for cid, _, _ in sections
    )
    side = f"""
    <aside class="side-card">
      <div class="side-head"><h3>Filtry</h3></div>
      <div class="side-block">
        <span class="side-label">Szukaj</span>
        <input id="kw" type="search" placeholder="Nazwisko, dziedzina, słowo…" style="width:100%;margin-top:.5rem;padding:.55rem .7rem;border-radius:8px;border:1px solid var(--border);background:var(--bg);color:var(--text);font:inherit;font-size:.9rem">
      </div>
      <div class="side-block">
        <span class="side-label">Metoda dopasowania</span>
        <label class="f-check"><input type="checkbox" class="m-cb" value="slowa" checked> Słowa z projektu i publikacji</label>
        <label class="f-check"><input type="checkbox" class="m-cb" value="tematy" checked> Tematy OpenAlex</label>
        <label class="f-check"><input type="checkbox" class="m-cb" value="wlasny" checked> Wpisz projekt</label>
        <label class="f-check"><input type="checkbox" class="m-cb" value="kalendarz" checked> Kalendarz naborów</label>
      </div>
      <div class="side-block">
        <span class="side-label">Wpisz projekt</span>
        <textarea id="own-text" rows="4" placeholder="Krótko: czego potrzebuje projekt (1–3 zdania)" style="width:100%;margin-top:.5rem;padding:.55rem .7rem;border-radius:8px;border:1px solid var(--border);background:var(--bg);color:var(--text);font:inherit;font-size:.9rem"></textarea>
        <button id="own-btn" class="btn btn-primary" type="button" style="margin-top:.5rem;width:100%">Dopasuj</button>
      </div>
      <div class="side-block">
        <span class="side-label">Nabór</span>
        {calls_filter}
      </div>
      <p class="side-note">Wyniki są wstępne. Weryfikuje biuro.</p>
    </aside>"""
    profiles = json.loads((ROOT / "data/wi_profiles.json").read_text(encoding="utf-8"))
    payload = [
        {"n": p.get("wi_name"), "o": p.get("name") or "", "r": p.get("orcid") or "",
         "f": ((p.get("topics") or [{}])[0].get("field") or ""),
         "t": [t.get("name", "") for t in (p.get("topics") or [])],
         "w": [[w.get("title") or "", w.get("keywords") or []] for w in (p.get("works") or [])]}
        for p in profiles
    ]
    blob = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    js = OWN_JS.replace("__STOP__", json.dumps(sorted(STOP), ensure_ascii=False)).replace("__PROFILES__", blob)
    script = "<script>" + js + "</script>"
    return f"""{head}
<style>a.tab, a.tab:hover {{ text-decoration: none; }} .tabs-row {{ flex-wrap: wrap; }} .tab {{ white-space: normal; }} .m-info, .m-name, .s-id h3, .s-pill, .s-kw, .s-sub, .hero-title, .hero-sub, .stat, .side-note {{ overflow-wrap: anywhere; min-width: 0; }} .hero-title, h1, h2, h3 {{ line-height: 1.25; letter-spacing: 0; }} body, p, li {{ line-height: 1.5; }} .s-pill, .kw {{ line-height: 1.3; white-space: normal; }} .hero-sub {{ max-width: 70ch; }}</style>
</head>
<body>
{header}
{tabs}

<main class="container">
  <section class="hero-simple">
    <div class="eyebrow">Nabór Horyzont Europa</div>
    <h1 class="hero-title">Dopasowanie osób do naborów</h1>
    <p class="hero-sub">Dopasowanie na podstawie tytułów tematów; pełne opisy do uzupełnienia.</p>
  </section>
  <div class="staff-layout" style="margin-top:1.2rem">
    {side}
    <div>{body}</div>
  </div>
</main>
{script}
{theme_js}
</body>
</html>
"""


def compute(topic_file, profiles, top_n):
    topic_text = Path(topic_file).read_text(encoding="utf-8")
    topic_tokens = tokens(topic_text)
    results = []
    for p in profiles:
        s, cov, hits = score(topic_tokens, p)
        if s == 0:
            continue
        results.append({
            "wi_name": p.get("wi_name"),
            "openalex_name": p.get("name"),
            "orcid": p.get("orcid"),
            "field": (p.get("topics") or [{}])[0].get("field"),
            "score": s,
            "coverage": round(cov, 3),
            "hits": hits[:12],
        })
    results.sort(key=lambda r: (r["score"], r["coverage"]), reverse=True)
    return {
        "topic_file": str(topic_file),
        "topic_terms": sorted(set(topic_tokens)),
        "matched_people": len(results),
        "profiles_total": len(profiles),
        "top": results[:top_n],
        "uwaga": "Wynik pokazuje dowody z tematów i publikacji, nie ocenę kompetencji. Weryfikuje biuro.",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--calls", default=str(ROOT / "data/nabory.json"))
    ap.add_argument("--profiles", default=str(ROOT / "data/wi_profiles.json"))
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--out", default=str(ROOT / "data/dopasowanie_probka.json"))
    ap.add_argument("--html", default=str(ROOT / "dopasowanie.html"))
    args = ap.parse_args()

    profiles = json.loads(Path(args.profiles).read_text(encoding="utf-8"))
    calls = json.loads(Path(args.calls).read_text(encoding="utf-8"))
    sections = []
    dump = {}
    for c in calls:
        out = compute(ROOT / c["topic"], profiles, args.top)
        sections.append((c["id"], c["nabor"], out))
        dump[c["id"]] = out
        print(f"{c['id']}: osób z trafieniem {out['matched_people']}")
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(dump, ensure_ascii=False, indent=1), encoding="utf-8")
    Path(args.html).write_text(render_html(sections), encoding="utf-8")
    print(f"zapisano: {args.html}")


if __name__ == "__main__":
    main()
