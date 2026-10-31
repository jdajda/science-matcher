import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import dopasowanie as dp  # noqa: E402

import datetime
TODAY = datetime.date.today().isoformat()


AREA_COLORS = dp.person_area_colors()
TITLES_PL = json.loads((ROOT / "data/tytuly_pl.json").read_text(encoding="utf-8"))
ROLES_PROJ = ["kierownik zadania", "wykonawca", "ekspert doradczy", "koordynacja komunikacji", "lider pakietu prac", "specjalista ds. danych", "inna (opisana w uzasadnieniu)"]


def people():
    tem = json.loads((ROOT / "data/wi_tematy_osob.json").read_text(encoding="utf-8"))
    prof = {p.get("wi_name"): p for p in json.loads((ROOT / "data/wi_profiles.json").read_text(encoding="utf-8"))}
    out = []
    for t in tem:
        name = t["wi_name"]
        p = prof.get(name, {})
        out.append({
            "name": name,
            "orcid": p.get("orcid") or "",
            "works": p.get("works_count") or 0,
            "topics": [x["name"] for x in t.get("tematy", [])[:6]],
            "field": ((t.get("tematy") or [{}])[0].get("field") or ""),
            "recent": [w.get("title") for w in (p.get("works") or [])[:3]],
            "color": AREA_COLORS.get(name) or dp.PALETTE[sum(ord(c) for c in name) % len(dp.PALETTE)],
        })
    out.sort(key=lambda x: x["name"])
    return out


def calls():
    items = json.loads((ROOT / "data/nabory_sedia.json").read_text(encoding="utf-8"))
    groups = {}
    for t in items:
        g = groups.setdefault(t["call"], {"id": t["call"], "deadlines": set(), "starts": [], "topics": 0, "titles": []})
        g["topics"] += 1
        g["titles"].append(html.unescape(TITLES_PL.get(t["id"]) or t.get("title") or t["id"]))
        g["deadlines"].update(t.get("terminy") or [])
        if t.get("start"):
            g["starts"].append(t["start"][:10])
    out = []
    for g in groups.values():
        dl = sorted(g["deadlines"])
        start = min(g["starts"]) if g["starts"] else ""
        last = dl[-1] if dl else ""
        if last and last < TODAY:
            status = "zamknięty"
        elif start and start > TODAY:
            status = "planowany"
        elif start and last and start <= TODAY <= last:
            status = "otwarty"
        else:
            status = "sprawdzić"
        out.append({"id": g["id"], "status": status, "deadlines": dl, "topics": g["topics"], "titles": g["titles"]})
    out.sort(key=lambda x: (x["status"] != "otwarty", x["deadlines"][0] if x["deadlines"] else "9999"))
    return out


def projects():
    """Nabory i trwające projekty, do których można wysłać zaproszenie (z opisem)."""
    out = []
    # build wymogi map
    items = json.loads((ROOT / "data/nabory_sedia.json").read_text(encoding="utf-8"))
    wymogi = {}
    for t in items:
        call = t["call"]
        wymogi.setdefault(call, [])
        wymogi[call].append({"nazwa": html.unescape(TITLES_PL.get(t["id"]) or t.get("title") or t["id"]), "wymagane": "tak", "kategoria": "tematyka"})
    for c in calls():
        shown = "; ".join(c["titles"][:4]) + (" …" if len(c["titles"]) > 4 else "")
        out.append({"id": c["id"], "nazwa": c["id"], "typ": "nabór", "termin": (c["deadlines"][-1] if c["deadlines"] else ""),
                    "opis": "Nabór UE. Tematy: " + shown, "wymogi": wymogi.get(c["id"], [])[:6]})
    rows = json.loads((ROOT / "data/projekty_zrealizowane.json").read_text(encoding="utf-8"))
    for r in rows:
        if r["koniec"] < TODAY:
            continue
        out.append({"id": "base-%s" % r["id"], "nazwa": r.get("nazwa") or r["temat"], "typ": "projekt", "termin": r["koniec"],
                    "opis": "%s. Zleceniodawca: %s. Okres: %s – %s." % (r["temat"], r["zleceniodawca"], r["start"], r["koniec"])})
    return out


def render():
    head, header, theme_js = dp.site_parts()
    head = head.replace("Dopasowanie do naboru · Mapa badawcza WI AGH", "Panel · Mapa badawcza WI AGH")
    tabs = dp.nav_html("panel")
    payload = {"people": people(), "calls": calls(), "projects": projects(), "rolesProj": ROLES_PROJ, "today": TODAY}
    data = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    script = SCRIPT.replace("__DATA__", data)
    return f"""{head}
<style>a.tab, a.tab:hover {{ text-decoration: none; }} 
.pn-switch {{ display: inline-flex; border: 1px solid var(--border); border-radius: 999px; padding: .2rem; background: var(--surface); margin: .6rem 0 1rem; }}
.pn-switch button {{ border: none; background: transparent; color: var(--text2); font: inherit; font-size: .9rem; padding: .45rem 1.1rem; border-radius: 999px; cursor: pointer; }}
.pn-switch button.active {{ background: var(--accent); color: var(--on-accent); font-weight: 600; }}
.pn-sub {{ display: flex; gap: .5rem; flex-wrap: wrap; margin: .6rem 0 1rem; }}
.pn-sub button {{ padding: .4rem .85rem; border-radius: 999px; border: 1px solid var(--border); background: var(--surface); color: var(--text2); font: inherit; font-size: .85rem; cursor: pointer; }}
.pn-sub button.active {{ border-color: var(--accent); color: var(--accent); font-weight: 600; }}
.pn-view, .pn-pane {{ display: none; }} .pn-view.active, .pn-pane.active {{ display: block; }}
.pn-kpi {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: .8rem; margin-bottom: 1.1rem; }}
.pn-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 14px; padding: 1rem 1.1rem; min-width: 0; }}
.pn-card h3 {{ font-size: .95rem; margin-bottom: .6rem; }}
.pn-big {{ font-size: 1.6rem; font-weight: 700; color: var(--text); display: block; line-height: 1.2; }}
.pn-small {{ font-size: .82rem; color: var(--text2); line-height: 1.45; }}
.pn-grid2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: .8rem; }}
.pn-stack {{ display: flex; flex-direction: column; gap: .8rem; }}
.pn-bar {{ display: grid; grid-template-columns: minmax(0, 1fr) 2.4rem; gap: .5rem; align-items: center; margin: .4rem 0; font-size: .85rem; color: var(--text); }}
.pn-bar .track {{ background: var(--surface2); border-radius: 4px; overflow: hidden; height: 8px; }}
.pn-bar i {{ display: block; height: 8px; border-radius: 4px; background: var(--accent); }}
.pn-row {{ display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: .5rem; align-items: center; padding: .55rem 0; border-top: 1px solid var(--border); font-size: .88rem; }}
.pn-row:first-child {{ border-top: none; }}
.pn-form label {{ display: block; font-size: .8rem; font-weight: 600; color: var(--text); margin: .6rem 0 .2rem; }}
.pn-form input, .pn-form select, .pn-form textarea, .pn-pick {{ width: 100%; box-sizing: border-box; padding: .5rem .65rem; border-radius: 8px; border: 1px solid var(--border); background: var(--bg); color: var(--text); font: inherit; font-size: .88rem; }}
.pn-avatar {{ width: 52px; height: 52px; border-radius: 50%; background: var(--accent); color: #fff; font-weight: 700; font-size: 1rem; display: inline-flex; align-items: center; justify-content: center; flex-shrink: 0; }}
.pn-chips {{ display: flex; flex-wrap: wrap; gap: .35rem; margin-top: .5rem; }}
.pn-chip {{ font-size: .78rem; background: var(--surface2); color: var(--text2); border-radius: 999px; padding: .15rem .6rem; }}
.pn-status {{ font-size: .75rem; font-weight: 600; border-radius: 999px; padding: .15rem .55rem; background: var(--surface2); color: var(--text2); white-space: nowrap; }}
.pn-status.ok {{ color: #2f7d5b; }} .pn-status.warn {{ color: #b08a4a; }}
.pn-inv {{ border: 1px solid var(--border); border-radius: 12px; padding: .8rem .9rem; background: var(--bg); margin-top: .6rem; }}
.pn-inv-head {{ display: flex; justify-content: space-between; align-items: flex-start; gap: .6rem; flex-wrap: wrap; }}
table.pn-table {{ width: 100%; border-collapse: collapse; font-size: .85rem; }}
table.pn-table th, table.pn-table td {{ text-align: left; padding: .5rem .4rem; border-bottom: 1px solid var(--border); vertical-align: top; }}
table.pn-table th {{ color: var(--text2); font-weight: 600; font-size: .78rem; }}
.pn-btn {{ padding: .5rem 1rem; border-radius: 8px; border: 1px solid var(--accent); background: var(--accent); color: var(--on-accent); font: inherit; font-size: .86rem; font-weight: 600; cursor: pointer; }}
.pn-btn.ghost {{ background: transparent; color: var(--accent); }}
.pn-btn.bad {{ background: transparent; color: #b06464; border-color: #b06464; }}
.pn-filter {{ display: flex; gap: .6rem; flex-wrap: wrap; align-items: center; margin-bottom: .9rem; }}
.pn-filter .pn-pick {{ flex: 1 1 240px; }}
.pn-chip-btn {{ font: inherit; font-size: .8rem; padding: .3rem .7rem; border-radius: 999px; border: 1px solid var(--border); background: var(--surface); color: var(--text2); cursor: pointer; }}
.pn-chip-btn.on {{ border-color: var(--accent); color: var(--accent); font-weight: 600; }}
.pn-empty {{ color: var(--text2); font-size: .9rem; padding: 1rem 0; }}
.pn-note {{ font-size: .8rem; color: var(--text2); margin-top: .8rem; line-height: 1.45; }}
@media (max-width: 900px) {{ .pn-kpi {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }} .pn-grid2 {{ grid-template-columns: 1fr; }} }}
</style>
</head>
<body>
{header}
{tabs}

<main class="container">
  <section class="hero-simple">
    <div class="eyebrow">Panel</div>
    <h1 class="hero-title">Panel użytkownika</h1>
    <p class="hero-sub">Widok dla naukowca (profil i zaproszenia do naborów) oraz widok dla biura projektowego (przegląd naborów i zaproszeń). Dane zapisują się w tej przeglądarce.</p>
  </section>



  <!-- NAUKOWIEC -->
  <div class="pn-view active" id="view-nauk" data-role-only="naukowiec">
    <p class="pn-small" id="pn-change-wrap" style="margin:0 0 .6rem"><button class="link-btn" id="pn-change-me" type="button">To nie ja. Zmień osobę</button></p>
    <div class="pn-card pn-form" id="pn-whois" hidden>
      <h3>Kim jesteś?</h3>
      <p class="pn-small">Wybierz swoje nazwisko z listy pracowników WI. Zapamiętamy wybór w tej przeglądarce.</p>
      <input id="pn-whois-input" list="pn-whois-list" autocomplete="off" placeholder="Zacznij pisać nazwisko…" aria-label="Twoje nazwisko">
      <datalist id="pn-whois-list"></datalist>
      <div style="margin-top:.6rem"><button class="btn btn-primary" id="pn-whois-save" type="button">Zapisz</button> <span class="pn-small" id="pn-whois-msg"></span></div>
    </div>
    <div class="pn-card pn-form" id="pp-card" style="margin-top:1rem">
      <h3>Zaproponuj współpracownika</h3>
      <p class="pn-small">Propozycja trafi do biura. Biuro ją sprawdzi i dopiero wtedy wyśle oficjalne zaproszenie.</p>
      <label for="pp-osoba">Osoba z WI</label><input id="pp-osoba" list="zp-osoba-list" autocomplete="off" placeholder="Zacznij pisać nazwisko…">
      <label for="pp-proj">Projekt lub nabór</label><select id="pp-proj"></select>
      <label for="pp-rola">Rola w projekcie</label><select id="pp-rola"></select>
      <label for="pp-uzas">Dlaczego ta osoba?</label><input id="pp-uzas" type="text" placeholder="np. publikacje o optymalizacji">
      <div style="margin-top:.8rem"><button class="pn-btn" id="pp-send" type="button">Wyślij propozycję do biura</button></div>
      <div class="pn-small" id="pp-mine" style="margin-top:.8rem"></div>
    </div>
    <div class="pn-grid2">
      <div class="pn-stack">
        <div class="pn-card">
          <h3 id="pn-who">Moje dane</h3>
          <input id="pn-search" class="pn-pick" type="search" aria-label="Szukaj osoby po nazwisku" placeholder="Szukaj osoby po nazwisku…" style="margin-bottom:.5rem" hidden>
          <select id="pn-person" class="pn-pick" aria-label="Osoba" hidden></select>
          <div id="pn-person-card" style="margin-top:1rem"></div>
        </div>
        <div class="pn-card">
          <h3>Moje zaproszenia do naborów</h3>
          <div id="nk-invites"></div>
        </div>
      </div>
      <div class="pn-card pn-form">
        <h3>Mój profil</h3>
        <label for="pf-wnosze">Co wnoszę do projektu</label>
        <textarea id="pf-wnosze" rows="3"></textarea>
        <label for="pf-szukam">Jakich kompetencji lub partnerów szukam</label>
        <textarea id="pf-szukam" rows="3"></textarea>
        <label for="pf-dost">Dostępność</label>
        <select id="pf-dost" aria-label="Dostępność"><option>do ustalenia</option><option>tak</option><option>nie</option></select>
        <label for="pf-zain">Zainteresowanie nowymi projektami</label>
        <select id="pf-zain" aria-label="Zainteresowanie nowymi projektami"><option>nie wiem</option><option>tak</option><option>nie</option></select>
        <div style="margin-top:.9rem"><button class="pn-btn" id="pf-save" type="button">Zapisz profil</button> <span class="pn-small" id="pf-saved"></span></div>
        <p class="pn-note">Bez logowania zmiany są zapisywane lokalnie. Przed publikacją profil wymaga potwierdzenia właściciela (W1).</p>
      </div>
    </div>
  </div>

  <!-- BIURO -->
  <div class="pn-view" id="view-biuro" data-role-only="biuro">
    <div class="pn-card pn-form" style="margin-bottom:1rem">
      <label for="bi-me">Twoje imię i nazwisko (osoba z biura)</label>
      <div style="display:flex;gap:.5rem;flex-wrap:wrap"><input id="bi-me" type="text" placeholder="np. Anna Kowalska" style="flex:1;min-width:200px"><button class="pn-btn ghost" id="bi-me-save" type="button">Zapisz</button></div>
      <label for="bi-rola">Twoja rola w biurze</label>
      <select id="bi-rola" aria-label="Twoja rola w biurze"><option value="biuro">specjalista ds. projektów</option><option value="koordynator">koordynator</option></select>
      <p class="pn-small">Szkic utworzony przez Ciebie zatwierdzi inna osoba z biura (W11). Opiekuna projektu przypisuje koordynator. Do czasu logowania SSO wpisz się tu w przeglądarce.</p>
    </div>
    <details class="pn-card" style="margin-bottom:1rem">
      <summary>Ostatnie zmiany w bazie i tablicy</summary>
      <div id="bi-hist" class="pn-small" style="margin-top:.6rem"></div>
    </details>
    <div class="pn-sub">
      <button class="active" data-pane="nabory">Zaproszenia</button>
      <button data-pane="nowe">Nowe zaproszenie</button>
    </div>


    <div class="pn-pane active" id="pane-nabory">
      <div class="pn-filter">
        <input id="bi-q" class="pn-pick" type="search" aria-label="Szukaj osoby albo naboru" placeholder="Szukaj osoby albo naboru">
        <div class="pn-chips" id="bi-chips" role="group" aria-label="Filtr statusu"></div>
      </div>
      <div class="pn-card"><div id="bi-list"></div></div>
      <p class="pn-note">Naborów bez zaproszeń nie pokazujemy. Nowe zaproszenie utworzysz w zakładce „Nowe zaproszenie”.</p>
    </div>

    <div class="pn-pane" id="pane-nowe">
      <div class="pn-card pn-form" style="max-width:720px">
        <h3>Nowe zaproszenie (szkic)</h3>
        <label for="zp-osoba">Osoba</label><input id="zp-osoba" list="zp-osoba-list" autocomplete="off" placeholder="Zacznij pisać nazwisko…"><datalist id="zp-osoba-list"></datalist><p class="pn-small" id="zp-osoba-info" aria-live="polite">Wybierz osobę z podpowiedzi z listy pracowników WI.</p>
        <label for="zp-nabor">Projekt lub nabór</label><select id="zp-nabor"></select>
        <p class="pn-small" id="zp-opis" aria-live="polite">Wybierz projekt, żeby zobaczyć jego opis. Opis trafi do zaproszenia.</p>
        <label for="zp-rola">Rola w projekcie</label><select id="zp-rola"></select>
        <label for="zp-uzas">Uzasadnienie (krótko)</label><input id="zp-uzas" type="text" placeholder="np. publikacje z predykcji szeregów czasowych">
        <div style="margin-top:.9rem"><button class="pn-btn" id="zp-add" type="button">Utwórz szkic</button></div>
        <p class="pn-note">Wysyłka tylko po zatwierdzeniu (W11). Wiadomość otwiera się w programie pocztowym.</p>
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
  const ME = (function () { try { return JSON.parse(localStorage.getItem('bm-me') || 'null') || {}; } catch (e) { return {}; } })();
  const NAUK = ME.role === 'naukowiec';
  const KEY = 'bm-panel-v3';
  let st = await loadState(KEY, {profiles: {}, invites: []});
  const save = () => saveState(KEY, st);
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const $ = id => document.getElementById(id);
  function toast(msg){
    let t = document.getElementById('toast');
    if (!t) { t = document.createElement('div'); t.id = 'toast'; t.setAttribute('role', 'status'); t.setAttribute('aria-live', 'polite');
      t.style.cssText = 'position:fixed;bottom:1.2rem;left:50%;transform:translateX(-50%);background:var(--surface);color:var(--text);border:1px solid var(--border);border-radius:10px;padding:.6rem 1rem;box-shadow:var(--shadow);z-index:99;font-size:.88rem;display:none;';
      document.body.appendChild(t); }
    t.textContent = msg; t.style.display = 'block';
    clearTimeout(t._h); t._h = setTimeout(() => { t.style.display = 'none'; }, 2600);
  }
  const initials = n => n.split(/\\s+/).filter(Boolean).slice(0,2).map(p => p[0]).join('').toUpperCase();
  const FLOW = ['szkic', 'zatwierdzone', 'wysłane'];
  const ANSWERS = ['odpowiedź: tak', 'odpowiedź: nie', 'brak odpowiedzi'];
  const STATUSES = FLOW.concat(ANSWERS);
  const people = DATA.people;
  const callsById = {}; DATA.calls.forEach(c => callsById[c.id] = c);
  const made = await loadState('bm-baza-nowe', []);
  (function () {
    made.filter(r => r.koniec >= DATA.today).forEach(r => DATA.projects.push({id: r.id, nazwa: r.nazwa || r.temat, typ: 'projekt', termin: r.koniec,
      opis: r.temat + '. Zleceniodawca: ' + r.zleceniodawca + '. Okres: ' + r.start + ' – ' + r.koniec + '.'}));
  })();
  const projById = {}; DATA.projects.forEach(p => projById[p.id] = p);
  const ROLES_PROJ = DATA.rolesProj;
  function projOptions(){
    const grp = (typ, label) => {
      const items = DATA.projects.filter(p => p.typ === typ);
      return items.length ? '<optgroup label="' + esc(label) + '">' + items.map(p => '<option value="' + esc(p.id) + '">' + esc(p.nazwa) + '</option>').join('') + '</optgroup>' : '';
    };
    return '<option value="">— wybierz nabór lub projekt —</option>' + grp('nabór', 'Nabory UE (tablica)') + grp('projekt', 'Trwające projekty (baza)');
  }
  function roleOptions(){ return ROLES_PROJ.map(r => '<option value="' + esc(r) + '">' + esc(r) + '</option>').join(''); }
  function showProj(){
    const p = projById[$('zp-nabor').value];
    $('zp-opis').textContent = p ? p.opis : 'Wybierz projekt, żeby zobaczyć jego opis. Opis trafi do zaproszenia.';
  }
  $('zp-nabor').innerHTML = projOptions();
  $('zp-rola').innerHTML = roleOptions();
  $('pp-proj').innerHTML = projOptions();
  $('pp-rola').innerHTML = roleOptions();
  $('zp-nabor').addEventListener('change', showProj);
  const SC = {'szkic': '#4f7fb0', 'zatwierdzone': '#5f9e80', 'wysłane': '#b08a4a', 'odpowiedź: tak': '#2f7d5b', 'odpowiedź: nie': '#b06464', 'brak odpowiedzi': '#8a94a6'};
  const CC = {'otwarty': '#5f9e80', 'planowany': '#4f7fb0', 'zamknięty': '#8a94a6', 'sprawdzić': '#b08a4a'};
  const pill = s => { const c = SC[s] || '#8a94a6'; return '<span class="pn-status" style="background:' + c + '22;color:' + c + ';border:1px solid ' + c + '">' + esc(s) + '</span>'; };
  const cpill = s => { const c = CC[s] || '#8a94a6'; return '<span class="pn-status" style="background:' + c + '22;color:' + c + ';border:1px solid ' + c + '">' + esc(s) + '</span>'; };
  const callLine = c => c ? esc(c.status) + ' · termin: ' + esc(c.deadlines.join(' · ') || 'brak') : 'brak danych';
  function computeCoverage(personName, projId){
    const p = people.find(x => x.name === personName);
    const pj = (DATA.projects || []).find(x => x.id === projId) || projById[projId] || {};
    const wymogi = pj.wymogi || [];
    if (!wymogi.length) return {items: [], met: 0, total: 0};
    const topics = (p && p.topics) || [];
    const tset = topics.join(' ').toLowerCase();
    const items = wymogi.map(w => {
      const n = (w.nazwa||'').toLowerCase();
      const hit = n && tset.indexOf(n.split(/\s+/)[0]) >= 0;
      return {name: w.nazwa, status: hit ? 'spełnione' : 'do potwierdzenia', required: w.wymagane || 'tak', evidence: hit ? 'na podstawie tematyki profilu' : 'brak bezpośredniego potwierdzenia'};
    });
    const met = items.filter(x => x.status === 'spełnione').length;
    return {items: items, met: met, total: items.length};
  }

  document.querySelectorAll('.seg-btn[data-view]').forEach(b => b.addEventListener('click', () => {
    document.querySelectorAll('.seg-btn[data-view]').forEach(x => x.classList.toggle('active', x === b));
    document.querySelectorAll('.pn-view').forEach(v => v.classList.toggle('active', v.id === 'view-' + b.dataset.view));
  }));
  document.querySelectorAll('.pn-sub button').forEach(b => b.addEventListener('click', () => {
    document.querySelectorAll('.pn-sub button').forEach(x => x.classList.toggle('active', x === b));
    document.querySelectorAll('.pn-pane').forEach(p => p.classList.toggle('active', p.id === 'pane-' + b.dataset.pane));
  }));

  /* ---------- NAUKOWIEC ---------- */
  function showOsoba(){
    const v = $('zp-osoba').value.trim();
    const p = people.find(x => x.name === v);
    $('zp-osoba-info').textContent = v === '' ? 'Wybierz osobę z podpowiedzi z listy pracowników WI.'
      : !p ? 'Nie ma takiej osoby na liście pracowników WI. Wybierz nazwisko z podpowiedzi.'
      : [p.field, (p.works || 0) + ' publikacji', p.topics.slice(0, 2).join(', ')].filter(Boolean).join(' · ');
  }
  function fillPeople(){
    const q = ($('pn-search').value || '').trim().toLowerCase();
    const base = NAUK && ME.name ? people.filter(p => p.name === ME.name) : people;
    const list = base.filter(p => !q || p.name.toLowerCase().includes(q));
    const cur = $('pn-person').value;
    const opts = list.map(p => '<option value="' + esc(p.name) + '">' + esc(p.name) + '</option>').join('');
    $('pn-person').innerHTML = opts;
    if (list.some(p => p.name === cur)) $('pn-person').value = cur;
    $('zp-osoba-list').innerHTML = people.map(p => '<option value="' + esc(p.name) + '"></option>').join('');

  }
  function showPerson(){
    const name = $('pn-person').value;
    const p = people.find(x => x.name === name); if (!p) return;
    const pr = st.profiles[name] || {};
    $('pn-person-card').innerHTML =
      '<div style="display:flex;gap:.8rem;align-items:center"><span class="pn-avatar" style="background:' + p.color + '">' + esc(initials(p.name)) + '</span><div><b style="color:var(--text)">' + esc(p.name) + '</b><div class="pn-small">' + p.works + ' prac od 2019' + (p.orcid ? ' · <a href="' + esc(p.orcid) + '" target="_blank" rel="noopener">ORCID</a>' : ' · ORCID brak') + '</div></div></div>' +
      '<div class="pn-chips">' + p.topics.map(t => '<span class="pn-chip">' + esc(t) + '</span>').join('') + '</div>' +
      '<div class="pn-small" style="margin-top:.8rem">Ostatnie prace:</div>' +
      (p.recent.length ? p.recent.map(t => '<div class="pn-small">• ' + esc(t) + '</div>').join('') : '<div class="pn-small">brak</div>');
    $('pf-wnosze').value = pr.wnosze || '';
    $('pf-szukam').value = pr.szukam || '';
    $('pf-dost').value = pr.dost || 'do ustalenia';
    $('pf-zain').value = pr.zain || 'nie wiem';
    $('pf-saved').textContent = '';
    renderNaukInvites();
  }
  function renderNaukInvites(){
    const name = $('pn-person').value;
    const mine = st.invites.map((i, idx) => Object.assign({}, i, {idx: idx})).filter(i => i.person === name && ['szkic', 'propozycja', 'zatwierdzone'].indexOf(i.status) === -1);
    if (!mine.length) { $('nk-invites').innerHTML = '<p class="pn-small">Brak zaproszeń. Biuro wysyła zaproszenia po zatwierdzeniu.</p>'; return; }
    $('nk-invites').innerHTML = mine.map(i => {
      const c = callsById[i.nabor];
      const answer = ANSWERS.includes(i.status) ? '' : '<div style="display:flex;gap:.4rem;margin-top:.6rem;flex-wrap:wrap"><button class="pn-btn" data-yes="' + i.idx + '" type="button">Chcę dołączyć</button><button class="pn-btn bad" data-no="' + i.idx + '" type="button">Nie w tym razie</button></div>';
      const pj = projById[i.nabor];
      return '<div class="pn-inv"><div class="pn-inv-head"><div><b style="color:var(--text)">' + esc(i.projekt || i.nabor) + '</b><div class="pn-small">' + (c ? callLine(c) : (pj ? 'termin: ' + esc(pj.termin) : '')) + '</div>' + (i.opis ? '<div class="pn-small" style="margin-top:.3rem">' + esc(i.opis) + '</div>' : '') + '<div class="pn-small" style="margin-top:.3rem">Rola w projekcie: ' + esc(i.rola) + (i.uzas ? ' · ' + esc(i.uzas) : '') + '</div>' + (i.answered ? '<div class="pn-small" role="status" style="color:#2f7d5b;margin-top:.3rem">✓ Odpowiedź zapisana: ' + (i.status === 'odpowiedź: tak' ? 'chcesz dołączyć' : 'nie w tym razie') + ' (' + esc(i.answered) + ')</div>' : '') + '</div>' + pill(i.status) + '</div>' + answer + '</div>';
    }).join('');
    $('nk-invites').querySelectorAll('[data-yes]').forEach(b => b.addEventListener('click', () => { const inv = st.invites[+b.dataset.yes]; inv.status = 'odpowiedź: tak'; inv.answered = new Date().toISOString().slice(0, 10); save(); toast('Dziękujemy. Biuro zobaczy, że chcesz dołączyć do naboru ' + inv.nabor + '.'); refresh(); }));
    $('nk-invites').querySelectorAll('[data-no]').forEach(b => b.addEventListener('click', () => { const inv = st.invites[+b.dataset.no]; inv.status = 'odpowiedź: nie'; inv.answered = new Date().toISOString().slice(0, 10); save(); toast('Dziękujemy za odpowiedź. Biuro zostanie poinformowane.'); refresh(); }));
  }

  /* ---------- BIURO ---------- */
  var BIURO_USER = localStorage.getItem('bm-biuro-user') || '';
  $('bi-me').value = BIURO_USER;
  if (location.protocol.indexOf('http') === 0) {
    fetch('/api/me', {cache: 'no-store'}).then(function (r) { return r.ok ? r.json() : null; }).then(function (v) {
      if (v && v.user && v.user.email) {
        BIURO_USER = v.user.email; $('bi-me').value = v.user.email; $('bi-me').readOnly = true; $('bi-me-save').disabled = true;
        refresh();
      }
    }).catch(function () {});
    fetch('/api/historia', {cache: 'no-store'}).then(function (r) { return r.ok ? r.json() : null; }).then(function (rows) {
      if (!rows) { $('bi-hist').textContent = 'Historia dostępna po zalogowaniu.'; return; }
      $('bi-hist').innerHTML = rows.length ? rows.slice(0, 50).map(function (x) {
        return '<div>' + esc(x.ts.slice(0, 16).replace('T', ' ')) + ' · ' + esc(x.email || '?') + ' · ' + esc(x.key) + ' · ' + esc(x.item) + ': ' + esc(x.before || '—') + ' → ' + esc(x.after || '—') + '</div>';
      }).join('') : 'Brak zmian.';
    }).catch(function () {});
  }
  $('bi-rola').value = localStorage.getItem('bm-biuro-rola') || 'biuro';
  $('bi-rola').addEventListener('change', function () { localStorage.setItem('bm-biuro-rola', $('bi-rola').value); toast('Rola zapisana. Odśwież Projekty, aby zobaczyć zmianę.'); });
  $('bi-me-save').addEventListener('click', function () {
    BIURO_USER = $('bi-me').value.trim();
    localStorage.setItem('bm-biuro-user', BIURO_USER);
    toast(BIURO_USER ? 'Zapisano: ' + BIURO_USER : 'Wyczyszczono nazwisko biura');
    refresh();
  });
  function canApprove(i){
    if (!BIURO_USER) { toast('Najpierw wpisz swoje nazwisko w polu u góry strony.'); return false; }
    if (i.autor && i.autor === BIURO_USER) { toast('Szkic utworzony przez Ciebie zatwierdzi inna osoba z biura (W11).'); return false; }
    return true;
  }
  var INV_FILTERS = ['wszystkie', 'propozycja', 'szkic', 'zatwierdzone', 'wysłane', 'odpowiedź: tak', 'odpowiedź: nie', 'brak odpowiedzi'];
  var invFilter = 'wszystkie';

  function renderBiuroCalls(){
    var q = ($('bi-q').value || '').trim().toLowerCase();
    var all = st.invites.map(function (i, idx) { return Object.assign({}, i, {idx: idx}); });
    var count = function (f) { return f === 'wszystkie' ? all.length : all.filter(function (i) { return i.status === f; }).length; };
    $('bi-chips').innerHTML = INV_FILTERS.map(function (f) {
      var on = f === invFilter;
      return '<button type="button" class="pn-chip-btn' + (on ? ' on' : '') + '" data-f="' + esc(f) + '" aria-pressed="' + on + '">' + esc(f) + ' · ' + count(f) + '</button>';
    }).join('');
    $('bi-chips').querySelectorAll('[data-f]').forEach(function (b) {
      b.addEventListener('click', function () { invFilter = b.dataset.f; renderBiuroCalls(); });
    });
    var rows = all.filter(function (i) {
      if (invFilter !== 'wszystkie' && i.status !== invFilter) return false;
      if (q && (i.person + ' ' + (i.projekt || '') + ' ' + i.nabor).toLowerCase().indexOf(q) === -1) return false;
      return true;
    });
    var callStatus = {};
    DATA.calls.forEach(function (c) { callStatus[c.id] = c.status; });
    if (!rows.length) {
      $('bi-list').innerHTML = '<div class="pn-empty">Brak zaproszeń w tym filtrze. Zmień filtr albo utwórz nowe zaproszenie.</div>';
    } else {
      $('bi-list').innerHTML = '<div style="overflow-x:auto"><table class="pn-table"><thead><tr><th>Osoba</th><th>Projekt lub nabór</th><th>Rola w projekcie</th><th>Status</th><th><span class="pn-small">Akcja</span></th></tr></thead><tbody>' +
        rows.map(function (i) {
          var act = '';
          if (i.status === 'propozycja') act = '<button class="pn-btn ghost" data-accept="' + i.idx + '" type="button">Przyjmij jako szkic</button>';
          else if (i.status === 'szkic') act = '<button class="pn-btn ghost" data-approve="' + i.idx + '" type="button">Zatwierdź</button>';
          else if (i.status === 'zatwierdzone') act = '<button class="pn-btn" data-send="' + i.idx + '" type="button">Otwórz e-mail</button>';
          if (i.status === 'wysłane' || i.status === 'brak odpowiedzi') act += ' <button class="pn-btn ghost" data-link="' + i.idx + '" type="button">Link do odpowiedzi</button>';
          var days = i.sent ? Math.floor((new Date(DATA.today) - new Date(i.sent)) / 86400000) : 0;
          if (i.status === 'wysłane' && days >= 7) act += ' <button class="pn-btn ghost" data-remind="' + i.idx + '" type="button">Przypomnij (' + days + ' dni)</button>';
          var cov = computeCoverage(i.person, i.nabor);
          var covHtml = cov.total ? '<div class="pn-small" style="margin-top:.2rem">Pokrycie wymogów: ' + cov.met + '/' + cov.total + ' (' + cov.items.map(function(x){return x.status === 'spełnione' ? '✓' : '△';}).join('') + ')</div>' : '';
          return '<tr><td><b>' + esc(i.person) + '</b>' + (i.zglosil ? '<div class="pn-small">propozycja od: ' + esc(i.zglosil) + '</div>' : '') + (i.autor ? '<div class="pn-small">szkic: ' + esc(i.autor) + (i.zatwierdzil ? ' · zatwierdził: ' + esc(i.zatwierdzil) : '') + '</div>' : '') + '</td>' +
            '<td>' + esc(i.projekt || i.nabor) + '<div class="pn-small">' + esc(callStatus[i.nabor] || (projById[i.nabor] || {}).typ || '') + '</div>' + (i.opis ? '<div class="pn-small">' + esc(i.opis) + '</div>' : '') + covHtml + '</td>' +
            '<td>' + esc(i.rola) + '</td>' +
            '<td>' + pill(i.status) + '</td>' +
            '<td style="text-align:right">' + act + '</td></tr>';
        }).join('') + '</tbody></table></div>';
    }
    $('bi-list').querySelectorAll('[data-accept]').forEach(function (b) {
      b.addEventListener('click', function () { st.invites[+b.dataset.accept].status = 'szkic'; st.invites[+b.dataset.accept].autor = BIURO_USER; save(); toast('Propozycja przyjęta jako szkic. Zatwierdź ją, zanim wyślesz.'); refresh(); });
    });
    $('bi-list').querySelectorAll('[data-approve]').forEach(function (b) {
      b.addEventListener('click', function () {
        const inv = st.invites[+b.dataset.approve];
        if (!canApprove(inv)) return;
        inv.status = 'zatwierdzone'; inv.zatwierdzil = BIURO_USER; save(); toast('Zaproszenie zatwierdzone'); refresh();
      });
    });
    $('bi-list').querySelectorAll('[data-remind]').forEach(function (b) {
      b.addEventListener('click', function () {
        var i = st.invites[+b.dataset.remind];
        var subj = encodeURIComponent('Przypomnienie: zaproszenie do udziału w ' + (i.projekt || i.nabor));
        var body = encodeURIComponent('Dzień dobry ' + i.person + ',\\n\\nprzypominamy o zaproszeniu do udziału w projekcie „' + (i.projekt || i.nabor) + '” w roli: ' + i.rola + '.\\nProsimy o odpowiedź, czy jest Pan/Pani zainteresowana/y.\\n\\nPozdrawiamy,\\nBiuro projektowe Wydziału Informatyki AGH');
        window.location.href = 'mailto:?subject=' + subj + '&body=' + body;
        toast('Otwarto przypomnienie. Status zaproszenia się nie zmienia.');
      });
    });
    $('bi-list').querySelectorAll('[data-link]').forEach(function (b) {
      b.addEventListener('click', async function () {
        var i = st.invites[+b.dataset.link];
        var key = (i.created || '') + '|' + (i.person || '') + '|' + (i.nabor || '');
        try {
          var r = await fetch('/api/zaproszenie-link', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({invite_key: key})});
          if (!r.ok) { toast('Nie udało się utworzyć linku (sprawdź logowanie).'); return; }
          var v = await r.json(); var url = location.origin + v.url;
          if (navigator.clipboard) navigator.clipboard.writeText(url).catch(function () {});
          prompt('Link do odpowiedzi (ważny do ' + v.wygasa + '). Skopiuj i wyślij osobie:', url);
        } catch (e) { toast('Brak połączenia z serwerem. Link działa tylko po uruchomieniu serwera.'); }
      });
    });
    $('bi-list').querySelectorAll('[data-send]').forEach(function (b) {
      b.addEventListener('click', function () {
        var i = st.invites[+b.dataset.send];
        if (!confirm('Otworzyć wiadomość do ' + i.person + '? Status zaproszenia zmieni się na „wysłane”.')) return;
        var subj = encodeURIComponent('Zaproszenie do udziału: ' + (i.projekt || i.nabor));
        var body = encodeURIComponent('Dzień dobry ' + i.person + ',\\n\\nzapraszamy do udziału w projekcie „' + (i.projekt || i.nabor) + '” w roli: ' + i.rola + '.\\n' + (i.opis ? 'Opis: ' + i.opis + '\\n' : '') + (i.uzas ? 'Uzasadnienie: ' + i.uzas + '.\\n' : '') + '\\nProsimy o odpowiedź, czy jest Pan/Pani zainteresowana/y.\\n\\nPozdrawiamy,\\nBiuro projektowe Wydziału Informatyki AGH');
        i.status = 'wysłane'; i.sent = new Date().toISOString().slice(0, 10); save();
        window.location.href = 'mailto:?subject=' + subj + '&body=' + body;
        refresh();
      });
    });
  }
  $('bi-q').addEventListener('input', renderBiuroCalls);
  $('zp-add').addEventListener('click', () => {
    const person = $('zp-osoba').value.trim(), nabor = $('zp-nabor').value;
    if (!people.some(x => x.name === person)) { toast('Wybierz osobę z listy podpowiedzi.'); return; }
    if (!nabor) { toast('Wybierz projekt lub nabór, zanim zapiszesz szkic.'); return; }
    const pj = projById[nabor];
    if (!BIURO_USER) { toast('Najpierw wpisz swoje nazwisko w polu u góry strony.'); return; }
    st.invites.push({person: person, nabor: nabor, projekt: pj.nazwa, opis: pj.opis, rola: $('zp-rola').value, uzas: $('zp-uzas').value.trim(), status: 'szkic', typ: 'zaproszenie', autor: BIURO_USER, created: DATA.today});
    toast('Szkic zapisany. Zatwierdź go, zanim wyślesz.');
    $('zp-osoba').value = ''; showOsoba(); showProj();
    $('zp-uzas').value = '';
    save(); refresh();
    document.querySelector('.pn-sub button[data-pane="nabory"]').click();
  });
  $('pn-person').addEventListener('change', showPerson);
  $('pn-search').addEventListener('input', () => { fillPeople(); showPerson(); });
  $('zp-osoba').addEventListener('input', showOsoba);
  function renderMyProposals(){
    const mine = st.invites.filter(i => i.typ === 'propozycja' && i.zglosil === ME.name);
    $('pp-mine').innerHTML = mine.length
      ? '<b>Twoje propozycje</b>' + mine.map(i => '<div>' + esc(i.person) + ' · ' + esc(i.projekt || i.nabor) + ' · ' + (i.status === 'propozycja' ? 'czeka na biuro' : 'biuro przyjęło propozycję') + '</div>').join('')
      : '';
  }
  $('pp-send').addEventListener('click', () => {
    const person = $('pp-osoba').value.trim(), nabor = $('pp-proj').value;
    if (!people.some(x => x.name === person) || person === ME.name) { toast('Wybierz współpracownika z listy podpowiedzi.'); return; }
    if (!nabor) { toast('Wybierz projekt lub nabór.'); return; }
    const pj = projById[nabor];
    st.invites.push({person: person, nabor: nabor, projekt: pj.nazwa, opis: pj.opis, rola: $('pp-rola').value, uzas: $('pp-uzas').value.trim(), status: 'propozycja', typ: 'propozycja', zglosil: ME.name, created: DATA.today, visibility: {internal: true, public: false}});
    save(); $('pp-osoba').value = ''; $('pp-uzas').value = '';
    toast('Propozycja wysłana do biura.'); renderMyProposals();
  });
  if (NAUK) renderMyProposals();
  $('pf-save').addEventListener('click', () => {
    const name = $('pn-person').value;
    st.profiles[name] = {wnosze: $('pf-wnosze').value.trim(), szukam: $('pf-szukam').value.trim(), dost: $('pf-dost').value, zain: $('pf-zain').value, zaktualizowano: DATA.today};
    save(); $('pf-saved').textContent = 'Zapisano lokalnie'; toast('Profil zapisany'); refresh();
  });

  function refresh(){ renderNaukInvites(); renderBiuroCalls(); }
  if (NAUK) {
    $('pn-change-me').addEventListener('click', function () {
      localStorage.setItem('bm-me', JSON.stringify({role: 'naukowiec', name: ''}));
      location.reload();
    });
  }
  if (NAUK && !ME.name) {
    $('pn-change-wrap').hidden = true;
    const view = document.getElementById('view-nauk');
    Array.from(view.children).forEach(function (c) { if (c.id !== 'pn-whois') c.hidden = true; });
    $('pn-whois').hidden = false;
    $('pn-whois-list').innerHTML = people.map(p => '<option value="' + esc(p.name) + '"></option>').join('');
    $('pn-whois-save').addEventListener('click', function () {
      const v = $('pn-whois-input').value.trim();
      if (!people.some(p => p.name === v)) { $('pn-whois-msg').textContent = 'Wybierz nazwisko z podpowiedzi.'; return; }
      localStorage.setItem('bm-me', JSON.stringify({role: 'naukowiec', name: v}));
      location.reload();
    });
  }
  fillPeople(); showPerson(); showOsoba(); refresh();
  setInterval(async () => {
    const v = await loadRemote(KEY);
    if (v && JSON.stringify(v) !== JSON.stringify(st)) { st = v; refresh(); }
  }, 15000);
})();
</script>"""


def main():
    out = ROOT / "panel.html"
    out.write_text(render(), encoding="utf-8")
    print(f"zapisano: {out}")


if __name__ == "__main__":
    main()
