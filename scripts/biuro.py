import collections
import datetime
import html as h
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import dopasowanie as dp  # noqa: E402

TAB_NAME = "Projekty"
TODAY = datetime.date.today().isoformat()
COLUMNS = [
    ("przyszle", "Przyszłe", "#4f7fb0"),
    ("otwarte", "Otwarte", "#5f9e80"),
    ("realizacja", "W trakcie realizacji", "#b08a4a"),
    ("zakonczone", "Zakończone", "#8a94a6"),
]
STATUS_TO_COLUMN = {"planowany": "przyszle", "otwarty": "otwarte", "zamknięty": "zakonczone", "sprawdzić": "przyszle"}
SOURCES = ["Nabór UE", "Partner zewnętrzny", "Inne"]
PROGRAMS = ["Dane i AI", "Cyfryzacja", "Przemysł", "Energia i środowisko", "Zdrowie", "Inne"]
ROLES = ["badawcza", "zarządcza", "wdrożeniowa", "komunikacja"]


TITLES_PL = json.loads((ROOT / "data/tytuly_pl.json").read_text(encoding="utf-8"))


AREA_COLORS = dp.person_area_colors()


def color_for(name):
    return AREA_COLORS.get(name) or dp.PALETTE[sum(ord(c) for c in name) % len(dp.PALETTE)]


def call_projects():
    items = json.loads((ROOT / "data/nabory_sedia.json").read_text(encoding="utf-8"))
    groups = collections.defaultdict(list)
    for t in items:
        groups[t["call"]].append(t)
    projects = []
    for call, topics in groups.items():
        starts = [t["start"][:10] for t in topics if t.get("start")]
        start = min(starts) if starts else ""
        deadlines = sorted({d for t in topics for d in (t.get("terminy") or [])})
        last = deadlines[-1] if deadlines else ""
        if last and last < TODAY:
            status = "zamknięty"
        elif start and start > TODAY:
            status = "planowany"
        elif start and last and start <= TODAY <= last:
            status = "otwarty"
        else:
            status = "sprawdzić"
        projects.append({
            "id": call,
            "title": call,
            "opis": "",
            "source": "Nabór UE",
            "program": "",
            "typ": "",
            "slowa": [],
            "start": start,
            "deadlines": deadlines,
            "status": status,
            "column": STATUS_TO_COLUMN[status],
            "tematy": [TITLES_PL.get(t["id"]) or t.get("title") or t["id"] for t in topics],
            "people": [],
        })
    projects.sort(key=lambda p: (p["column"] != "otwarte", p["deadlines"][0] if p["deadlines"] else "9999", p["id"]))
    return projects


def people_list():
    profiles = json.loads((ROOT / "data/wi_profiles.json").read_text(encoding="utf-8"))
    names = sorted({p.get("wi_name") for p in profiles if p.get("wi_name")})
    return [{"name": n, "color": color_for(n)} for n in names]


def demo_people(projects, people):
    names = [x["name"] for x in people]
    if not names:
        return
    picked = [p for p in projects if p["column"] in ("otwarte", "przyszle")][:4]
    for i, p in enumerate(picked):
        p["people"] = names[i * 3 : i * 3 + 3]


def render(demo=False):
    head, header, theme_js = dp.site_parts()
    head = head.replace("Dopasowanie do naboru · Mapa badawcza WI AGH", "Projekty · Mapa badawcza WI AGH")
    local = dp.local_nav([("pj-board", "Tablica etapów"), ("pj-report", "Statystyki")])
    tabs = dp.nav_html("projekty") + local
    projects = call_projects()
    people = people_list()
    if demo:
        demo_people(projects, people)
    payload = {
        "key": "bm-projekty-demo" if demo else "bm-projekty-v1",
        "today": TODAY,
        "projects": projects,
        "people": people,
        "columns": [[c, l, col] for c, l, col in COLUMNS],
        "sources": SOURCES,
        "programs": PROGRAMS,
        "roles": ROLES,
    }
    data = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    script = SCRIPT.replace("__DATA__", data)
    opt = lambda items: "".join(f'<option value="{h.escape(x)}">{h.escape(x)}</option>' for x in items)
    col_checks = "".join(
        f'<label class="f-check"><input type="checkbox" class="pj-col-cb" value="{c}" checked> {h.escape(l)}</label>'
        for c, l, _ in COLUMNS
    )
    return f"""{head}
<style>a.tab, a.tab:hover {{ text-decoration: none; }} 
.pj-layout {{ display: grid; grid-template-columns: 260px minmax(0, 1fr); gap: 1.2rem; align-items: start; }}
.pj-side {{ font-size: .88rem; min-width: 0; box-sizing: border-box; }}
.pj-side .side-block {{ display: flex; flex-direction: column; gap: .35rem; }}
.pj-side .side-label {{ display: block; font-weight: 600; color: var(--text); }}
.pj-side .side-head h3 {{ margin: 0; }}
.pj-side .f-check {{ display: flex; align-items: center; gap: .5rem; margin: 0; padding: .1rem 0; }}
.pj-side .f-check input {{ margin: 0; width: 16px; height: 16px; flex-shrink: 0; }}
.pj-side input, .pj-side select {{ width: 100%; box-sizing: border-box; margin: 0; }}
.pj-side {{ position: sticky; top: 1rem; background: var(--surface); border: 1px solid var(--border); border-radius: 14px; padding: 1rem 1.1rem; }}
.pj-side .side-block {{ border-top: 1px solid var(--border); padding: .8rem 0; }}
.pj-side input, .pj-side select {{ width: 100%; margin-top: .4rem; padding: .45rem .6rem; border-radius: 8px; border: 1px solid var(--border); background: var(--bg); color: var(--text); font: inherit; font-size: .88rem; }}
.pj-board {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: .9rem; align-items: start; }}
.pj-col {{ background: var(--surface); border: 1px solid var(--border); border-radius: 14px; padding: .8rem; min-width: 0; }}
.pj-col-head {{ display: flex; justify-content: space-between; align-items: center; gap: .5rem; padding-bottom: .6rem; border-bottom: 3px solid var(--c); margin-bottom: .2rem; }}
.pj-col-head h3 {{ font-size: .95rem; }}
.pj-count {{ font-size: .8rem; color: var(--text2); }}
.pj-card {{ background: var(--bg); border: 1px solid var(--border); border-left: 4px solid var(--c); border-radius: 10px; margin-top: .6rem; overflow-wrap: anywhere; }}
.pj-card > summary {{ list-style: none; cursor: pointer; padding: .7rem .8rem; }}
.pj-card > summary::-webkit-details-marker {{ display: none; }}
.pj-title {{ font-weight: 600; font-size: .92rem; color: var(--text); line-height: 1.3; }}
.pj-meta {{ font-size: .8rem; color: var(--text2); margin-top: .25rem; line-height: 1.4; }}
.pj-tags {{ display: flex; flex-wrap: wrap; gap: .3rem; margin-top: .4rem; }}
.pj-tag {{ font-size: .72rem; color: var(--text2); background: var(--surface2); border-radius: 999px; padding: .1rem .5rem; }}
.pj-dots {{ display: flex; flex-wrap: wrap; gap: .3rem; margin-top: .5rem; }}
.pj-dot {{ width: 26px; height: 26px; border-radius: 50%; color: #fff; font-size: .7rem; font-weight: 700; display: inline-flex; align-items: center; justify-content: center; }}
.pj-body {{ padding: 0 .8rem .8rem; border-top: 1px solid var(--border); }}
.pj-body p, .pj-body li {{ font-size: .85rem; color: var(--text2); line-height: 1.5; }}
.pj-body ul {{ padding-left: 1.1rem; margin: .4rem 0; }}
.pj-section {{ margin-top: .7rem; }}
.pj-label {{ font-size: .78rem; font-weight: 700; color: var(--text); text-transform: uppercase; letter-spacing: .04em; }}
.pj-chip {{ display: inline-flex; align-items: center; gap: .35rem; border-radius: 999px; padding: .15rem .3rem .15rem .15rem; background: var(--surface2); font-size: .8rem; margin: .2rem .25rem .2rem 0; }}
.pj-chip .pj-dot {{ width: 22px; height: 22px; font-size: .62rem; }}
.pj-chip button {{ background: none; border: none; color: var(--text2); cursor: pointer; font-size: .9rem; padding: 0 .2rem; }}
.pj-body select, .pj-form input, .pj-form select, .pj-form textarea {{ width: 100%; margin-top: .3rem; padding: .4rem .55rem; border-radius: 8px; border: 1px solid var(--border); background: var(--surface); color: var(--text); font: inherit; font-size: .85rem; }}
.pj-form {{ background: var(--surface); border: 1px solid var(--border); border-radius: 14px; padding: 1rem; margin-bottom: 1.2rem; }}
.pj-form-grid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .8rem; margin-top: .6rem; }}
.pj-form-grid .wide {{ grid-column: span 2; }}
.pj-empty {{ color: var(--text2); font-size: .85rem; padding: .6rem 0; }}
.pj-stats {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: .8rem; margin-top: 1.4rem; }}
.pj-stat {{ background: var(--surface); border: 1px solid var(--border); border-top: 3px solid var(--c); border-radius: 12px; padding: .8rem 1rem; }}
.pj-stat b {{ font-size: 1.4rem; color: var(--text); display: block; }}
.pj-stat span {{ font-size: .8rem; color: var(--text2); }}
.pj-actions {{ display: flex; gap: .6rem; flex-wrap: wrap; margin: .8rem 0; }}
.pj-body .btn {{ margin-top: .7rem; }}
@media (max-width: 1100px) {{ .pj-board {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }} }}
@media (max-width: 900px) {{ .pj-layout {{ grid-template-columns: 1fr; }} .pj-side {{ position: static; }} .pj-form-grid {{ grid-template-columns: 1fr; }} .pj-form-grid .wide {{ grid-column: auto; }} .pj-stats {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }} }}
@media print {{ body * {{ visibility: hidden; }} #pj-report, #pj-report * {{ visibility: visible; }} #pj-report {{ position: absolute; left: 0; top: 0; width: 100%; }} .tabs, header, .pj-form, .pj-board, .pj-side, .pj-actions {{ display: none !important; }} }}
</style>
</head>
<body>
{header}
{tabs}

<main class="container">
  <section class="hero-simple">
    <div class="eyebrow">Baza projektów</div>
    <h1 class="hero-title">Projekty i dobór zespołu</h1>
    <p class="hero-sub">Projekty przechodzą przez etapy od przyszłych do zakończonych. Przypisz osoby z WI, rozwiń kartę, żeby zobaczyć opis naboru.</p>
  </section>

  <div class="pj-form">
    <div class="pj-label">Nowy projekt (z zewnątrz lub z naboru)</div>
    <div class="pj-form-grid">
      <div><input id="pj-new-title" type="text" placeholder="Nazwa projektu"></div>
      <div><select id="pj-new-source">{opt(SOURCES)}</select></div>
      <div><select id="pj-new-call"><option value="">Bez naboru</option></select></div>
      <div><select id="pj-new-program">{opt(PROGRAMS)}</select></div>
      <div><select id="pj-new-role">{opt(ROLES)}</select></div>
      <div><input id="pj-new-term" type="date" title="Termin składania lub zakończenia"></div>
      <div class="wide"><input id="pj-new-slowa" type="text" placeholder="Słowa kluczowe, po przecinku (np. digital twin, AI)"></div>
      <div class="wide"><textarea id="pj-new-opis" rows="2" placeholder="Krótki opis: czego dotyczy projekt"></textarea></div>
    </div>
    <button id="pj-new-btn" class="btn btn-primary" type="button" style="margin-top:.8rem">Dodaj do Przyszłych</button>
  </div>

  <div class="pj-layout">
    <aside class="pj-side">
      <div class="side-head"><h3>Filtry</h3></div>
      <div class="side-block">
        <span class="side-label">Szukaj</span>
        <input id="pj-q" type="search" placeholder="Nazwa, opis, słowo kluczowe…">
      </div>
      <div class="side-block">
        <span class="side-label">Etap</span>
        {col_checks}
      </div>
      <div class="side-block">
        <span class="side-label">Status naboru</span>
        <select id="pj-status"><option value="">wszystkie</option><option>planowany</option><option>otwarty</option><option>zamknięty</option><option>sprawdzić</option></select>
      </div>
      <div class="side-block">
        <span class="side-label">Źródło</span>
        <select id="pj-source"><option value="">wszystkie</option>{opt(SOURCES)}</select>
      </div>
      <div class="side-block">
        <span class="side-label">Program</span>
        <select id="pj-program"><option value="">wszystkie</option>{opt(PROGRAMS)}</select>
      </div>
      <div class="side-block">
        <span class="side-label">Typ roli</span>
        <select id="pj-role"><option value="">wszystkie</option>{opt(ROLES)}</select>
      </div>
      <div class="side-block">
        <span class="side-label">Osoba w zespole</span>
        <select id="pj-person"><option value="">wszystkie</option></select>
      </div>
      <div class="side-block">
        <span class="side-label">Termin do</span>
        <input id="pj-deadline" type="date">
      </div>
      <div class="side-block">
        <button id="pj-reset" class="link-btn" type="button">Wyczyść filtry</button>
      </div>
    </aside>
    <div>
      <div class="pj-board" id="pj-board"></div>
    </div>
  </div>

  <div id="pj-report">
    <div class="pj-actions"><button id="pj-print" class="btn btn-primary" type="button">Pobierz statystyki (PDF)</button> <button id="pj-csv" class="btn" type="button">Pobierz projekty (CSV)</button></div>
    <div class="pj-stats" id="pj-stats"></div>
  </div>
</main>
{script}
{theme_js}
</body>
</html>
"""


SCRIPT = """
<script>
  const STORE_API = location.protocol.indexOf('http') === 0;
  async function loadRemote(key){
    if (!STORE_API) return null;
    try { const r = await fetch('/api/kv/' + encodeURIComponent(key), {cache: 'no-store'}); if (!r.ok) return null; return await r.json(); } catch(e) { return null; }
  }
  async function loadState(key, fallback){
    const v = await loadRemote(key);
    if (v) return v;
    try { const l = JSON.parse(localStorage.getItem(key) || 'null'); if (l) return l; } catch(e) {}
    return fallback;
  }
  function saveState(key, v){
    try { localStorage.setItem(key, JSON.stringify(v)); } catch(e) {}
    if (STORE_API) fetch('/api/kv/' + encodeURIComponent(key), {method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(v)}).catch(() => {});
  }

(async function(){
  const DATA = __DATA__;
  const KEY = DATA.key;
  let st = await loadState(KEY, {cards: {}, custom: []});
  const save = () => saveState(KEY, st);
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const initials = n => n.split(/\\s+/).filter(Boolean).slice(0,2).map(p => p[0]).join('').toUpperCase();
  const colorOf = {}; DATA.people.forEach(p => colorOf[p.name] = p.color);
  const colById = {}; DATA.columns.forEach(c => colById[c[0]] = c[2]);
  const $ = id => document.getElementById(id);
  function toast(msg){
    let t = document.getElementById('toast');
    if (!t) { t = document.createElement('div'); t.id = 'toast'; t.setAttribute('role', 'status'); t.setAttribute('aria-live', 'polite');
      t.style.cssText = 'position:fixed;bottom:1.2rem;left:50%;transform:translateX(-50%);background:var(--surface);color:var(--text);border:1px solid var(--border);border-radius:10px;padding:.6rem 1rem;box-shadow:var(--shadow);z-index:99;font-size:.88rem;display:none;';
      document.body.appendChild(t); }
    t.textContent = msg; t.style.display = 'block';
    clearTimeout(t._h); t._h = setTimeout(() => { t.style.display = 'none'; }, 2600);
  }

  function allProjects(){
    const base = DATA.projects.map(p => Object.assign({}, p, st.cards[p.id] || {}));
    const custom = st.custom.map(p => Object.assign({}, p, st.cards[p.id] || {}));
    return base.concat(custom);
  }
  function update(id, patch){
    st.cards[id] = Object.assign({}, st.cards[id] || {}, patch);
    save(); render();
  }
  function dots(people){
    return people.map(n => '<span class="pj-dot" title="' + esc(n) + '" style="background:' + colorOf[n] + '">' + esc(initials(n)) + '</span>').join('');
  }
  function tagsOf(p){
    const tags = [p.source, p.program, p.typ].concat(p.slowa || []).filter(Boolean);
    return tags.length ? '<div class="pj-tags">' + tags.map(t => '<span class="pj-tag">' + esc(t) + '</span>').join('') + '</div>' : '';
  }
  function card(p){
    const col = colById[p.column];
    const term = p.deadlines && p.deadlines.length ? p.deadlines.join(' · ') : (p.term || 'brak terminu');
    const chips = (p.people || []).map(n => '<span class="pj-chip"><span class="pj-dot" style="background:' + colorOf[n] + '">' + esc(initials(n)) + '</span>' + esc(n) + ' <button data-remove="' + esc(p.id) + '" data-name="' + esc(n) + '" type="button">×</button></span>').join('');
    const peopleOpts = '<option value="">+ dodaj osobę</option>' + DATA.people.filter(x => !(p.people || []).includes(x.name)).map(x => '<option value="' + esc(x.name) + '">' + esc(x.name) + '</option>').join('');
    const colOpts = DATA.columns.map(c => '<option value="' + c[0] + '"' + (c[0] === p.column ? ' selected' : '') + '>' + c[1] + '</option>').join('');
    const topics = (p.tematy || []).length ? '<ul>' + p.tematy.map(t => '<li>' + esc(t) + '</li>').join('') + '</ul>' : '<p>Brak tematów.</p>';
    return '<details class="pj-card" style="--c:' + col + '"' + (p.open ? ' open' : '') + '>' +
      '<summary><div class="pj-title">' + esc(p.title) + '</div>' +
      '<div class="pj-meta">' + esc(p.status || '') + ' · termin: ' + esc(term) + '</div>' + tagsOf(p) +
      '<div class="pj-dots">' + dots(p.people || []) + '</div></summary>' +
      '<div class="pj-body">' +
        (p.opis ? '<div class="pj-section"><div class="pj-label">Opis</div><p>' + esc(p.opis) + '</p></div>' : '') +
        '<div class="pj-section"><div class="pj-label">Tematy naboru</div>' + topics + '</div>' +
        '<div class="pj-section"><div class="pj-label">Zespół</div>' + (chips || '<div class="pj-empty">Brak osób. Dodaj z listy poniżej.</div>') +
        '<select data-add="' + esc(p.id) + '">' + peopleOpts + '</select></div>' +
        '<div class="pj-section"><div class="pj-label">Etap</div><select data-move="' + esc(p.id) + '">' + colOpts + '</select></div>' +
        '<button class="btn" type="button" data-card="' + esc(p.id) + '">Wizytówka do wysłania</button>' +
      '</div></details>';
  }
  function passes(p){
    const q = $('pj-q').value.trim().toLowerCase();
    const cols = Array.from(document.querySelectorAll('.pj-col-cb:checked')).map(x => x.value);
    if (!cols.includes(p.column)) return false;
    if (q) {
      const text = [p.title, p.opis, p.id, p.source, p.program, p.typ].concat(p.slowa || [], p.tematy || []).join(' ').toLowerCase();
      if (!text.includes(q)) return false;
    }
    if ($('pj-status').value && p.status !== $('pj-status').value) return false;
    if ($('pj-source').value && p.source !== $('pj-source').value) return false;
    if ($('pj-program').value && p.program !== $('pj-program').value) return false;
    if ($('pj-role').value && p.typ !== $('pj-role').value) return false;
    if ($('pj-person').value && !(p.people || []).includes($('pj-person').value)) return false;
    if ($('pj-deadline').value) {
      const d = (p.deadlines && p.deadlines.length) ? p.deadlines[p.deadlines.length - 1] : (p.term || '');
      if (!d || d > $('pj-deadline').value) return false;
    }
    return true;
  }
  function stats(projects){
    const people = new Set(); projects.forEach(p => (p.people || []).forEach(n => people.add(n)));
    const cols = DATA.columns.map(c => '<div class="pj-stat" style="--c:' + c[2] + '"><b>' + projects.filter(p => p.column === c[0]).length + '</b><span>' + esc(c[1]) + '</span></div>').join('');
    const extra = '<div class="pj-stat" style="--c:#4f7fb0"><b>' + projects.length + '</b><span>projektów łącznie</span></div>' +
      '<div class="pj-stat" style="--c:#5f9e80"><b>' + people.size + '</b><span>osób w zespołach</span></div>';
    $('pj-stats').innerHTML = cols + extra;
  }
  function wizytowka(p){
    const term = p.deadlines && p.deadlines.length ? p.deadlines.join(' · ') : (p.term || 'brak terminu');
    const team = (p.people || []).length ? (p.people || []).map(n => '<li>' + esc(n) + '</li>').join('') : '<li>zespół w przygotowaniu</li>';
    const topics = (p.tematy || []).map(t => '<li>' + esc(t) + '</li>').join('');
    const subject = encodeURIComponent('Zaproszenie do projektu: ' + p.title);
    const body = encodeURIComponent('Dzień dobry,\\n\\nzapraszamy do udziału w projekcie: ' + p.title + '.\\nTermin: ' + term + '.\\n\\nProsimy o odpowiedź: czy jest Pan/Pani zainteresowana/y udziałem i w jakiej roli?\\n\\nPozdrawiamy,\\nBiuro projektowe Wydziału Informatyki AGH');
    const w = window.open('', '_blank');
    w.document.write('<!doctype html><html lang="pl"><head><meta charset="utf-8"><title>Wizytówka: ' + esc(p.title) + '</title><style>body{font-family:-apple-system,Segoe UI,sans-serif;max-width:720px;margin:2rem auto;color:#1c2736;line-height:1.5}h1{font-size:1.4rem}h2{font-size:1rem;margin-top:1.2rem}.meta{color:#5a6679}ul{padding-left:1.2rem}.btn{display:inline-block;margin-top:1rem;padding:.5rem 1rem;border-radius:8px;background:#2c64a0;color:#fff;text-decoration:none}@media print{.btn{display:none}}</style></head><body>' +
      '<h1>' + esc(p.title) + '</h1><div class="meta">' + esc(p.status || '') + ' · termin: ' + esc(term) + '</div>' +
      (p.opis ? '<h2>Opis</h2><p>' + esc(p.opis) + '</p>' : '') +
      '<h2>Tematy naboru</h2><ul>' + (topics || '<li>brak</li>') + '</ul>' +
      '<h2>Zespół</h2><ul>' + team + '</ul>' +
      '<p>Czy chce Pan/Pani dołączyć do projektu? Proszę odpowiedzieć na wiadomość lub skontaktować się z biurem projektowym.</p>' +
      '<a class="btn" href="mailto:?subject=' + subject + '&body=' + body + '">Otwórz wiadomość e-mail</a> ' +
      '<a class="btn" href="javascript:window.print()">Zapisz jako PDF</a></body></html>');
    w.document.close();
  }
  function render(){
    const all = allProjects();
    const people = new Set(); all.forEach(p => (p.people || []).forEach(n => people.add(n)));
    const sel = $('pj-person'), cur = sel.value;
    sel.innerHTML = '<option value="">wszystkie</option>' + Array.from(people).sort().map(n => '<option value="' + esc(n) + '">' + esc(n) + '</option>').join('');
    sel.value = cur;
    const shown = all.filter(passes);
    const board = $('pj-board');
    board.innerHTML = DATA.columns.map(c => {
      const items = shown.filter(p => p.column === c[0]);
      return '<div class="pj-col" style="--c:' + c[2] + '"><div class="pj-col-head"><h3>' + esc(c[1]) + '</h3><span class="pj-count">' + items.length + '</span></div>' +
        (items.map(card).join('') || '<div class="pj-empty">Brak projektów w tym etapie. Dodaj nowy formularzem powyżej albo zdejmij filtry.</div>') + '</div>';
    }).join('');
    board.querySelectorAll('[data-add]').forEach(s => s.addEventListener('change', e => {
      const id = e.target.dataset.add; const name = e.target.value; if (!name) return;
      const p = all.find(x => x.id === id);
      update(id, {people: (p.people || []).concat([name]), open: true});
    }));
    board.querySelectorAll('[data-remove]').forEach(b => b.addEventListener('click', e => {
      const id = e.currentTarget.dataset.remove; const name = e.currentTarget.dataset.name;
      if (!confirm('Usunąć osobę „' + name + '” z zespołu?')) return;
      const p = all.find(x => x.id === id);
      update(id, {people: (p.people || []).filter(n => n !== name), open: true});
    }));
    board.querySelectorAll('[data-move]').forEach(s => s.addEventListener('change', e => {
      update(e.target.dataset.move, {column: e.target.value, open: true});
    }));
    board.querySelectorAll('[data-card]').forEach(b => b.addEventListener('click', e => {
      e.preventDefault();
      wizytowka(all.find(x => x.id === e.currentTarget.dataset.card));
    }));
    board.querySelectorAll('details').forEach(d => d.addEventListener('toggle', () => {
      const m = d.querySelector('[data-move]'); if (!m) return;
      st.cards[m.dataset.move] = Object.assign({}, st.cards[m.dataset.move] || {}, {open: d.open});
      save();
    }));
    stats(all);
  }
  const newCall = $('pj-new-call');
  DATA.projects.forEach(p => { const o = document.createElement('option'); o.value = p.id; o.textContent = p.id; newCall.appendChild(o); });
  $('pj-new-btn').addEventListener('click', () => {
    const title = $('pj-new-title').value.trim();
    if (!title) return;
    const call = newCall.value;
    const base = DATA.projects.find(p => p.id === call);
    const slowa = $('pj-new-slowa').value.split(',').map(s => s.trim()).filter(Boolean);
    const term = $('pj-new-term').value;
    toast('Dodano projekt do etapu Przyszłe');
    st.custom.push({
      id: 'custom-' + Date.now(), title: title,
      opis: $('pj-new-opis').value.trim(),
      source: $('pj-new-source').value, program: $('pj-new-program').value, typ: $('pj-new-role').value,
      slowa: slowa, term: term,
      start: '', deadlines: base ? base.deadlines : (term ? [term] : []),
      status: call ? 'nabór ' + call : 'bez naboru',
      column: 'przyszle', tematy: base ? base.tematy : [], people: []
    });
    ['pj-new-title', 'pj-new-opis', 'pj-new-slowa', 'pj-new-term'].forEach(id => $(id).value = '');
    save(); render();
  });
  ['pj-q', 'pj-status', 'pj-source', 'pj-program', 'pj-role', 'pj-person', 'pj-deadline'].forEach(id => $(id).addEventListener('input', render));
  document.querySelectorAll('.pj-col-cb').forEach(c => c.addEventListener('change', render));
  $('pj-reset').addEventListener('click', () => {
    ['pj-q', 'pj-deadline'].forEach(id => $(id).value = '');
    ['pj-status', 'pj-source', 'pj-program', 'pj-role', 'pj-person'].forEach(id => $(id).value = '');
    document.querySelectorAll('.pj-col-cb').forEach(c => c.checked = true);
    render();
  });
  $('pj-print').addEventListener('click', () => window.print());
  $('pj-csv').addEventListener('click', () => {
    const cols = ['nazwa', 'nabór', 'etap', 'status', 'termin', 'źródło', 'program', 'typ roli', 'słowa kluczowe', 'osoby w zespole'];
    const colName = c => (DATA.columns.find(x => x[0] === c) || [c, c])[1];
    const q = v => '"' + String(v == null ? '' : v).replace(/"/g, '""') + '"';
    const rows = allProjects().map(p => [
      p.title, p.id, colName(p.column), p.status || '',
      (p.deadlines && p.deadlines.length ? p.deadlines.join(' | ') : (p.term || '')),
      p.source || '', p.program || '', p.typ || '',
      (p.slowa || []).join(', '), (p.people || []).join(', ')
    ].map(q).join(';'));
    const csv = '\\ufeff' + cols.map(q).join(';') + '\\r\\n' + rows.join('\\r\\n');
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([csv], {type: 'text/csv;charset=utf-8'}));
    a.download = 'projekty_' + DATA.today + '.csv';
    document.body.appendChild(a); a.click(); a.remove();
  });
  render();
  setInterval(async () => {
    const v = await loadRemote(KEY);
    if (v && JSON.stringify(v) !== JSON.stringify(st)) { st = v; render(); }
  }, 15000);
})();
</script>"""


def main():
    out = ROOT / "biuro.html"
    out.write_text(render(), encoding="utf-8")
    print(f"zapisano: {out}")
    demo = ROOT / "biuro_przyklad.html"
    demo.write_text(render(demo=True), encoding="utf-8")
    print(f"zapisano przykład z przypisanymi osobami: {demo}")


if __name__ == "__main__":
    main()
