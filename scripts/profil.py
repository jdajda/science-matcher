import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import dopasowanie as dp  # noqa: E402
import panel as pn  # noqa: E402


def badap_index():
    src = (ROOT / "index.html").read_text(encoding="utf-8")
    m = re.search(r'<script id="app-data" type="application/json">(.*?)</script>', src, re.S)
    if not m:
        return {}
    data = json.loads(m.group(1))
    labels = {a["id"]: a.get("label", a["id"]) for a in data.get("areas", [])}
    out = {}
    for st in data.get("staff", []):
        out[st["name"]] = {
            "degree": st.get("degree", ""), "unit": st.get("unit", ""), "email": st.get("email", ""),
            "category": st.get("category", ""), "badap": st.get("badap", ""), "skos": st.get("skos", ""),
            "pubs": st.get("pubs", 0), "yearMax": st.get("yearMax", ""),
            "keywords": [k[0] for k in st.get("keywords", [])[:10]],
            "areas": [labels.get(a.get("id"), a.get("id")) for a in st.get("areas", [])],
        }
    return out


def brand_logo():
    """Sam znak wydziału (bez napisu), biały, wyciągnięty z logo w nagłówku."""
    import base64
    src = (ROOT / "index.html").read_text(encoding="utf-8")
    m = re.search(r'<img class="brand-logo"[^>]*src="data:image/svg\+xml;base64,([^"]+)"', src)
    if not m:
        return ""
    svg = base64.b64decode(m.group(1)).decode("utf-8-sig")
    rects = re.findall(r"<rect[^>]*/>", svg)
    if not rects:
        return ""

    def num(r, k):
        mm = re.search(r"\s" + k + r'="([^"]+)"', r)
        return float(mm.group(1)) if mm else 0.0

    xs, ys = [], []
    for r in rects:
        x, y, w, h = num(r, "x"), num(r, "y"), num(r, "width"), num(r, "height")
        xs += [x, x + w]
        ys += [y, y + h]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    body = "".join(re.sub(r"\sclass=\"[^\"]*\"", "", r).replace("/>", ' fill="#ffffff"/>') for r in rects)
    icon = f'<svg class="brand-mark" xmlns="http://www.w3.org/2000/svg" viewBox="{x0:.2f} {y0:.2f} {x1-x0:.2f} {y1-y0:.2f}" aria-hidden="true">{body}</svg>'
    return icon

def render():
    head, header, theme_js = dp.site_parts()
    head = head.replace("Dopasowanie do naboru · Mapa badawcza WI AGH", "Profil osoby · Mapa badawcza WI AGH")
    tabs = dp.nav_html("naukowcy")
    local = ""
    people = pn.people()
    badap = badap_index()
    for pe in people:
        pe["badap"] = badap.get(pe["name"], {})
    import biuro as bz
    projects = bz.call_projects()
    data = json.dumps({"people": people, "projects": projects, "baza": bz.completed_base(), "columns": [[c, l, col] for c, l, col in bz.COLUMNS], "default": "Eckes Maria"}, ensure_ascii=False).replace("</", "<\\/")
    script = SCRIPT.replace("__DATA__", data)
    logo = brand_logo()
    return f"""{head}
<style>a.tab, a.tab:hover {{ text-decoration: none; }}
.pc-wrap {{ border: 1px solid var(--border); border-radius: 14px; overflow: hidden; background: var(--surface); margin-top: 1rem; }}
.pc-band {{ background: var(--header-bg); color: #fff; padding: 1.3rem 1.6rem; }}
.pc-band .pc-title {{ font-size: 1.45rem; font-weight: 700; line-height: 1.2; overflow-wrap: anywhere; }}
.pc-band {{ display: flex; align-items: center; justify-content: space-between; gap: 1rem; }}
.pc-band-text {{ min-width: 0; }}
.pc-progress {{ margin-top: .7rem; display: flex; align-items: center; gap: .6rem; font-size: .78rem; }}
.pc-progress i {{ display: block; width: 160px; height: 6px; border-radius: 3px; background: rgba(255,255,255,.25); overflow: hidden; }}
.pc-progress b {{ display: block; height: 100%; background: #fff; }}
.pc-band .brand-mark {{ height: 56px; width: auto; flex-shrink: 0; }}
.pc-band .pc-sub {{ font-size: .78rem; letter-spacing: .12em; text-transform: uppercase; opacity: .85; margin-top: .45rem; }}
.pc-body {{ display: grid; grid-template-columns: 300px minmax(0, 1fr); }}
.pc-side {{ background: var(--surface2); padding: 1.1rem 1.3rem; border-right: 1px solid var(--border); min-width: 0; }}
.pc-main {{ padding: 1.1rem 1.6rem; min-width: 0; }}
.pc-h {{ font-size: .76rem; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; color: var(--accent); border-bottom: 2px solid var(--border); padding-bottom: .3rem; margin: 1.1rem 0 .55rem; }}
.pc-h:first-child {{ margin-top: 0; }}
.pc-list {{ list-style: none; padding: 0; margin: 0; font-size: .88rem; color: var(--text); line-height: 1.55; }}
.pc-list li {{ padding-left: .9rem; position: relative; overflow-wrap: anywhere; }}
.pc-list li::before {{ content: '·'; position: absolute; left: 0; color: var(--accent); font-weight: 700; }}
.pc-text {{ font-size: .9rem; color: var(--text); line-height: 1.6; }}
.pc-kv {{ font-size: .88rem; margin: .35rem 0; }}
.pc-kv b {{ color: var(--text); }}
.pc-kv select {{ margin-top: .25rem; width: 100%; }}
.pc-item {{ padding: .5rem 0; border-bottom: 1px solid var(--border); }}
.pc-item:last-child {{ border-bottom: none; }}
.pc-item b {{ display: block; font-size: .92rem; color: var(--text); overflow-wrap: anywhere; }}
.pc-item .pc-meta {{ font-style: italic; color: var(--text2); font-size: .8rem; margin-top: .15rem; }}
.pc-note {{ font-size: .82rem; color: var(--text2); }}
@media (max-width: 900px) {{ .pc-body {{ grid-template-columns: 1fr; }} .pc-side {{ border-right: none; border-bottom: 1px solid var(--border); }} }}
</style>
</head>
<body>
{header}
{tabs}
{local}

<main class="container">


  <div class="profile-top">
    <select id="pf-person" class="category-filter" aria-label="Wybór osoby"></select>
  </div>

  <div class="page-view active" id="view-naukowiec" data-role-only="naukowiec">
    <div class="pc-wrap">
      <div class="pc-band"><div class="pc-band-text"><h1 class="pc-title" id="nk-name"></h1><div class="pc-sub" id="nk-meta"></div><div class="pc-progress"><span id="nk-complete"></span><i><b id="nk-bar"></b></i></div></div>{logo}</div>
      <div class="pc-body">
        <aside class="pc-side">
          <div class="pc-h">Afiliacja</div>
          <div class="pc-kv" id="nk-affil"></div>
          <div class="pc-h">Identyfikatory</div>
          <div class="pc-kv" id="nk-ids"></div>
          <div class="pc-h">Kontakt służbowy</div>
          <div class="pc-kv" id="nk-email"></div>
          <div class="pc-h">Obszary i branże</div>
          <ul class="pc-list" id="nk-areas"></ul>
          <div class="pc-h">Tematy (OpenAlex, po angielsku)</div>
          <ul class="pc-list" id="nk-topics"></ul>
          <div class="pc-h">Technologie i metody</div>
          <ul class="pc-list" id="nk-keywords"></ul>
          <div class="pc-h">Wybrane publikacje</div>
          <ul class="pc-list" id="nk-works"></ul>
          <div class="pc-h">Projekty</div>
          <ul class="pc-list" id="nk-projects"></ul>
          <div class="pc-h">Certyfikaty</div>
          <p class="pc-note">Brak danych. Rejestr szkoleń nie jest jeszcze podłączony.</p>
          <div class="pc-h">Dostępność i zainteresowanie</div>
          <div class="pc-kv"><b>Dostępność</b><select class="category-filter" id="nk-dost" aria-label="Dostępność"><option>do ustalenia</option><option>tak</option><option>nie</option></select></div>
          <div class="pc-kv"><b>Zainteresowanie nowymi projektami</b><select class="category-filter" id="nk-zain" aria-label="Zainteresowanie nowymi projektami"><option>nie wiem</option><option>tak</option><option>nie</option></select></div>
          <div class="pc-note" id="nk-confirmed"></div>
        </aside>
        <section class="pc-main">
          <div class="pc-h">Co wnoszę do projektu</div>
          <textarea class="match-textarea" id="nk-wnosze" rows="3" aria-label="Co wnoszę do projektu"></textarea>
          <div class="pc-h">Szukam kompetencji lub partnerów</div>
          <textarea class="match-textarea" id="nk-szukam" rows="3" aria-label="Szukam kompetencji lub partnerów"></textarea>
          <div style="margin-top:.8rem;display:flex;gap:.6rem;align-items:center;flex-wrap:wrap"><button class="btn btn-primary" id="nk-save" type="button">Zapisz opis</button><button class="btn" id="nk-confirm" type="button">Potwierdzam, że dane są aktualne</button><span class="pc-note" id="nk-saved"></span></div>
          <div class="pc-h">Zgłoś korektę danych</div>
          <p class="pc-note">Widzisz błąd w danych z BaDAP albo OpenAlex? Opisz go, a biuro zobaczy zgłoszenie.</p>
          <textarea class="match-textarea" id="nk-correction" rows="2" placeholder="np. brakuje publikacji z 2026 r."></textarea>
          <div style="margin-top:.6rem;display:flex;gap:.6rem;align-items:center"><button class="btn" id="nk-correct" type="button">Wyślij korektę</button><span class="pc-note" id="nk-corr-saved"></span></div>
          <div class="pc-h">Moje zgłoszenia korekt</div>
          <div id="nk-corrections"></div>
          <div class="pc-h">Zaproszenia do naborów</div>
          <p class="pc-note" id="nk-invite-note"></p>
          <a class="btn" href="panel.html">Przejdź do zaproszeń</a>
        </section>
      </div>
    </div>
  </div>

  <div class="page-view" id="view-biuro" data-role-only="biuro">
    <div class="pc-wrap">
      <div class="pc-band"><div class="pc-band-text"><h1 class="pc-title" id="bi-name"></h1><div class="pc-sub" id="bi-meta"></div></div>{logo}</div>
      <div class="pc-body">
        <aside class="pc-side">
          <div class="pc-h">Tematy</div>
          <ul class="pc-list" id="bi-topics"></ul>
        </aside>
        <section class="pc-main">
          <div class="pc-h">Opis z profilu</div>
          <div class="pc-text" id="bi-desc"></div>
          <div class="pc-h">Projekty z zespołem</div>
          <div id="bi-projects"></div>
          <div class="pc-h">Korekty od osoby</div>
          <div id="bi-corrections"></div>
          <div class="pc-h">Zaproszenia</div>
          <div id="bi-invites"></div>
          <div class="pc-h">Historia</div>
          <div id="bi-timeline"></div>
        </section>
      </div>
    </div>
  </div>
</main>
{script}
{theme_js}
</body>
</html>
"""


SCRIPT = """
<script>
(function(){
  const DATA = __DATA__;
  const PANEL_KEY = 'bm-panel-v2', BIURO_KEY = 'bm-projekty-v1';
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const $ = id => document.getElementById(id);
  function toast(msg){
    let t = document.getElementById('toast');
    if (!t) { t = document.createElement('div'); t.id = 'toast'; t.setAttribute('role', 'status'); t.setAttribute('aria-live', 'polite');
      t.style.cssText = 'position:fixed;bottom:1.2rem;left:50%;transform:translateX(-50%);background:var(--surface);color:var(--text);border:1px solid var(--border);border-radius:10px;padding:.6rem 1rem;box-shadow:var(--shadow);z-index:99;font-size:.88rem;display:none;';
      document.body.appendChild(t); }
    t.textContent = msg; t.style.display = 'block';
    clearTimeout(t._h); t._h = setTimeout(function () { t.style.display = 'none'; }, 2600);
  }
  const initials = n => n.split(/\\s+/).filter(Boolean).slice(0,2).map(p => p[0]).join('').toUpperCase();
  const people = DATA.people;
  const bazaOver = (function () { try { return JSON.parse(localStorage.getItem('bm-baza-kier') || '{}'); } catch (e) { return {}; } })();
  const STAGE = {'zakończony': 'Zakończone', 'w realizacji': 'W trakcie realizacji', 'planowany': 'Przyszłe'};
  function bazaFor(name) {
    return (DATA.baza || []).filter(function (r) {
      var k = bazaOver.hasOwnProperty(String(r.id)) ? bazaOver[String(r.id)] : (r.kierownik_wi || '');
      return k === name;
    });
  }
  const ANSWERS = ['odpowiedź: tak', 'odpowiedź: nie', 'brak odpowiedzi'];
  const LABEL = {'szkic': 'szkic', 'zatwierdzone': 'zatwierdzone', 'wysłane': 'wysłane', 'odpowiedź: tak': 'dołącza', 'odpowiedź: nie': 'nie dołącza', 'brak odpowiedzi': 'brak odpowiedzi'};
  let panel = {profiles: {}, invites: []};
  let biuro = {cards: {}, custom: []};
  let current = new URLSearchParams(location.search).get('osoba') || DATA.default || (people[0] && people[0].name);

  function saveLocal(key, v){ try { localStorage.setItem(key, JSON.stringify(v)); } catch(e) {} }
  function loadLocal(key, fb){ try { return JSON.parse(localStorage.getItem(key) || 'null') || fb; } catch(e) { return fb; } }
  async function loadRemote(key){ try { const r = await fetch('/api/kv/' + encodeURIComponent(key), {cache: 'no-store'}); return r.ok ? await r.json() : null; } catch(e) { return null; } }
  function persist(key, v){
    saveLocal(key, v);
    fetch('/api/kv/' + encodeURIComponent(key), {method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(v)}).catch(() => {});
  }

  document.querySelectorAll('button.seg-btn[data-view]').forEach(b => b.addEventListener('click', () => {
    document.querySelectorAll('button.seg-btn[data-view]').forEach(x => { x.classList.toggle('active', x === b); x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
    document.querySelectorAll('.page-view').forEach(v => v.classList.toggle('active', v.id === 'view-' + b.dataset.view));
  }));

  function fillPicker(){
    $('pf-person').innerHTML = people.map(p => '<option value="' + esc(p.name) + '"' + (p.name === current ? ' selected' : '') + '>' + esc(p.name) + '</option>').join('');
  }
  function color(name){ const p = people.find(x => x.name === name); return (p && p.color) || '#4f7fb0'; }

  function renderNaukowiec(){
    const p = people.find(x => x.name === current); if (!p) return;
    const pr = panel.profiles[current] || {};
    $('nk-name').textContent = current;
    var b = p.badap || {};
    $('nk-meta').textContent = [b.degree, b.unit, (b.pubs || 0) + ' publikacji w BaDAP'].filter(Boolean).join(' · ');
    $('nk-keywords').innerHTML = (b.keywords || []).map(function (k) { return '<li>' + esc(k) + '</li>'; }).join('') || '<li>Brak słów kluczowych</li>';
    $('nk-email').textContent = b.email || 'brak';
    $('nk-affil').innerHTML = [b.degree, b.unit, b.category].filter(Boolean).map(function (x) { return '<div>' + esc(x) + '</div>'; }).join('') || 'brak danych';
    $('nk-ids').innerHTML = [
      p.orcid ? '<a href="' + esc(p.orcid) + '" target="_blank" rel="noopener">ORCID</a>' : 'ORCID: brak',
      b.badap ? '<a href="' + esc(b.badap) + '" target="_blank" rel="noopener">BaDAP</a>' : '',
      b.skos ? '<a href="' + esc(b.skos) + '" target="_blank" rel="noopener">SKOS</a>' : ''
    ].filter(Boolean).join(' · ');
    $('nk-areas').innerHTML = (b.areas || []).map(function (a) { return '<li>' + esc(a) + '</li>'; }).join('') || '<li>Brak obszarów</li>';
    var projs = allProjects().filter(function (x) { return (x.people || []).indexOf(current) !== -1; });
    var bz0 = bazaFor(current);
    $('nk-projects').innerHTML = projs.map(function (x) { return '<li>' + esc(x.title) + ' · ' + esc(x.column || '') + '</li>'; }).concat(bz0.map(function (r) { return '<li>' + esc(r.temat) + ' · ' + esc(STAGE[r.stan] || r.stan) + ' (' + esc(r.start) + ' – ' + esc(r.koniec) + ')' + (bazaOver.hasOwnProperty(String(r.id)) ? ' · przypisane przez biuro' : '') + '</li>'; })).join('') || '<li>Brak przypisanych projektów</li>';
    var pr0 = panel.profiles[current] || {};
    $('nk-confirmed').textContent = pr0.potwierdzono ? 'Dane potwierdzone: ' + pr0.potwierdzono + ' (potwierdzenie tożsamości przez SSO – po wdrożeniu)' : 'Dane nie zostały jeszcze potwierdzone przez właściciela.';
    var corr = (panel.korekty || []).filter(function (k) { return k.person === current; });
    $('nk-corrections').innerHTML = corr.length ? corr.map(function (k) { return '<div class="pc-item"><b>' + esc(k.text) + '</b><div class="pc-meta">' + esc(k.date) + ' · ' + esc(k.status) + '</div></div>'; }).join('') : '<p class="pc-note">Brak zgłoszeń.</p>';
    $('nk-topics').innerHTML = p.topics.map(t => '<li>' + esc(t) + '</li>').join('') || '<li>Brak tematów</li>';
    $('nk-works').innerHTML = p.recent.length ? p.recent.map(t => '<li>' + esc(t) + '</li>').join('') : '<li>Brak prac</li>';
    $('nk-wnosze').value = pr.wnosze || ''; $('nk-szukam').value = pr.szukam || '';
    $('nk-dost').value = pr.dost || 'do ustalenia'; $('nk-zain').value = pr.zain || 'nie wiem';
    $('nk-saved').textContent = '';
    var checks = [pr.wnosze, pr.szukam, pr.dost && pr.dost !== 'do ustalenia', pr.zain && pr.zain !== 'nie wiem', p.orcid, p.topics && p.topics.length, pr.potwierdzono];
    var done = checks.filter(Boolean).length;
    $('nk-complete').textContent = 'Profil uzupełniony: ' + done + ' z ' + checks.length + (pr.potwierdzono ? '' : ' (brakuje potwierdzenia danych)');
    $('nk-bar').style.width = Math.round(done / checks.length * 100) + '%';
    const inv = panel.invites.map((i, idx) => Object.assign({}, i, {idx: idx})).filter(i => i.person === current && i.status !== 'szkic');
    var open = inv.filter(function (i) { return i.status !== 'odpowiedź: tak' && i.status !== 'odpowiedź: nie' && i.status !== 'brak odpowiedzi'; }).length;
    $('nk-invite-note').textContent = open ? 'Czekają na Twoją odpowiedź: ' + open + '.' : (inv.length ? 'Wszystkie zaproszenia mają odpowiedź.' : 'Brak zaproszeń.');
  }

  function allProjects(){
    const base = DATA.projects.map(p => Object.assign({}, p, biuro.cards[p.id] || {}));
    const custom = biuro.custom.map(p => Object.assign({}, p, biuro.cards[p.id] || {}));
    return base.concat(custom);
  }
  function renderBiuro(){
    const p = people.find(x => x.name === current); if (!p) return;
    const pr = panel.profiles[current] || {};
    $('bi-name').textContent = current;
    var bb = p.badap || {};
    $('bi-meta').textContent = [bb.degree, bb.unit, bb.email].filter(Boolean).join(' · ');
    var bcorr = (panel.korekty || []).map(function (k, idx) { return Object.assign({}, k, {idx: idx}); }).filter(function (k) { return k.person === current; });
    $('bi-corrections').innerHTML = bcorr.length ? bcorr.map(function (k) {
      var done = k.status === 'rozpatrzone';
      return '<div class="pc-item"><b>' + esc(k.text) + '</b><div class="pc-meta">' + esc(k.date) + ' · ' + esc(k.status) + '</div>' +
        (done ? '' : '<button class="btn" data-done="' + k.idx + '" type="button" style="margin-top:.4rem">Oznacz jako rozpatrzone</button>') + '</div>';
    }).join('') : '<p class="pc-note">Brak zgłoszeń korekt.</p>';
    $('bi-corrections').querySelectorAll('[data-done]').forEach(function (b) {
      b.addEventListener('click', function () { panel.korekty[+b.dataset.done].status = 'rozpatrzone'; persist(PANEL_KEY, panel); toast('Oznaczono jako rozpatrzone'); renderAll(); });
    });
    $('bi-desc').innerHTML = pr.wnosze ? esc(pr.wnosze) + '<br><br><b>Szuka:</b> ' + esc(pr.szukam || '–') : 'Osoba nie uzupełniła profilu.';
    $('bi-topics').innerHTML = p.topics.map(t => '<li>' + esc(t) + '</li>').join('') || '<li>Brak tematów</li>';
    const projects = allProjects().filter(x => (x.people || []).includes(current));
    var bzList = bazaFor(current).map(r => '<div class="member-row"><div><b>' + esc(r.temat) + '</b><div class="s-sub">' + esc(r.start) + ' – ' + esc(r.koniec) + (r.kwota ? ' · ' + Math.round(r.kwota).toLocaleString('pl-PL') + ' PLN' : '') + '</div></div><span class="s-pill">' + esc(STAGE[r.stan] || r.stan) + '</span></div>').join('');
    var kanbanHtml = projects.map(x => '<div class="member-row"><div><b>' + esc(x.title) + '</b><div class="s-sub">' + esc(x.status || '') + (x.deadlines && x.deadlines.length ? ' · termin: ' + esc(x.deadlines.join(' · ')) : '') + '</div></div><span class="s-pill">' + esc(x.column || '') + '</span></div>').join('');
    $('bi-projects').innerHTML = (kanbanHtml + bzList) || '<p class="s-sub">Nie jest przypisana do żadnego projektu.</p>';
    const inv = panel.invites.filter(i => i.person === current);
    $('bi-invites').innerHTML = inv.length ? inv.map(i => '<div class="member-row"><div><b>' + esc(i.nabor) + '</b><div class="s-sub">rola: ' + esc(i.rola) + '</div></div><span class="s-pill">' + esc(LABEL[i.status] || i.status) + '</span></div>').join('') : '<p class="s-sub">Brak zaproszeń.</p>';
    const events = [];
    inv.forEach(i => {
      if (i.created) events.push([i.created, 'Utworzono szkic zaproszenia do ' + i.nabor]);
      if (i.sent) events.push([i.sent, 'Wysłano zaproszenie do ' + i.nabor]);
      if (ANSWERS.includes(i.status)) events.push([i.sent || i.created || '', 'Odpowiedź: ' + (LABEL[i.status] || i.status) + ' (' + i.nabor + ')']);
    });
    if (pr.zaktualizowano) events.push([pr.zaktualizowano, 'Profil zaktualizowany przez osobę']);
    events.sort((a, b) => (b[0] || '').localeCompare(a[0] || ''));
    $('bi-timeline').innerHTML = events.length ? events.map(e => '<div class="s-sub" style="margin:.35rem 0">' + esc(e[0]) + ' · ' + esc(e[1]) + '</div>').join('') : '<div class="s-sub">Brak zdarzeń.</div>';
  }

  function renderAll(){ renderNaukowiec(); renderBiuro(); }

  $('pf-person').addEventListener('change', e => { current = e.target.value; history.replaceState(null, '', '?osoba=' + encodeURIComponent(current)); renderAll(); });
  $('nk-confirm').addEventListener('click', () => {
    panel.profiles[current] = Object.assign({}, panel.profiles[current] || {}, {potwierdzono: new Date().toISOString().slice(0, 10)});
    persist(PANEL_KEY, panel); renderAll(); $('nk-saved').textContent = 'Potwierdzono'; toast('Dziękujemy. Data potwierdzenia została zapisana.');
  });
  $('nk-correct').addEventListener('click', () => {
    const text = $('nk-correction').value.trim();
    if (!text) { $('nk-corr-saved').textContent = 'Opisz, co wymaga poprawy.'; return; }
    panel.korekty = (panel.korekty || []).concat([{person: current, text: text, date: new Date().toISOString().slice(0, 10), status: 'nowe'}]);
    persist(PANEL_KEY, panel); $('nk-correction').value = ''; $('nk-corr-saved').textContent = 'Zgłoszenie wysłane do biura.';
    toast('Zgłoszenie wysłane do biura'); renderAll();
  });
  $('nk-save').addEventListener('click', () => {
    panel.profiles[current] = Object.assign({}, panel.profiles[current] || {}, {wnosze: $('nk-wnosze').value.trim(), szukam: $('nk-szukam').value.trim(), dost: $('nk-dost').value, zain: $('nk-zain').value, zaktualizowano: new Date().toISOString().slice(0, 10)});
    persist(PANEL_KEY, panel); $('nk-saved').textContent = 'Zapisano'; renderAll();
  });

  async function start(){
    const rp = await loadRemote(PANEL_KEY), rb = await loadRemote(BIURO_KEY);
    panel = rp || loadLocal(PANEL_KEY, panel);
    biuro = rb || loadLocal(BIURO_KEY, biuro);
    fillPicker(); renderAll();
  }
  start();
})();
</script>"""


def main():
    out = ROOT / "profil.html"
    out.write_text(render(), encoding="utf-8")
    print(f"zapisano: {out}")


if __name__ == "__main__":
    main()
