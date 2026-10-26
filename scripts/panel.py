import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import dopasowanie as dp  # noqa: E402

import datetime
TODAY = datetime.date.today().isoformat()


AREA_COLORS = dp.person_area_colors()


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
        g = groups.setdefault(t["call"], {"id": t["call"], "deadlines": set(), "starts": [], "topics": 0})
        g["topics"] += 1
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
        out.append({"id": g["id"], "status": status, "deadlines": dl, "topics": g["topics"]})
    out.sort(key=lambda x: (x["status"] != "otwarty", x["deadlines"][0] if x["deadlines"] else "9999"))
    return out


def render():
    head, header, theme_js = dp.site_parts()
    head = head.replace("Dopasowanie do naboru · Mapa badawcza WI AGH", "Panel · Mapa badawcza WI AGH")
    tabs = dp.nav_html("panel") + dp.local_nav([("nauk", "Naukowiec"), ("biuro", "Biuro projektowe")], mode="button")
    payload = {"people": people(), "calls": calls(), "today": TODAY}
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
  <div class="pn-view active" id="view-nauk">
    <div class="pn-grid2">
      <div class="pn-stack">
        <div class="pn-card">
          <h3>Kto korzysta</h3>
          <input id="pn-search" class="pn-pick" type="search" placeholder="Szukaj osoby po nazwisku…" style="margin-bottom:.5rem">
          <select id="pn-person" class="pn-pick"></select>
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
        <select id="pf-dost"><option>do ustalenia</option><option>tak</option><option>nie</option></select>
        <label for="pf-zain">Zainteresowanie nowymi projektami</label>
        <select id="pf-zain"><option>nie wiem</option><option>tak</option><option>nie</option></select>
        <div style="margin-top:.9rem"><button class="pn-btn" id="pf-save" type="button">Zapisz profil</button> <span class="pn-small" id="pf-saved"></span></div>
        <p class="pn-note">Bez logowania zmiany są zapisywane lokalnie. Przed publikacją profil wymaga potwierdzenia właściciela (W1).</p>
      </div>
    </div>
  </div>

  <!-- BIURO -->
  <div class="pn-view" id="view-biuro">
    <div class="pn-sub">
      <button class="active" data-pane="przeglad">Przegląd</button>
      <button data-pane="nabory">Nabory i zaproszenia</button>
      <button data-pane="nowe">Nowe zaproszenie</button>
    </div>

    <div class="pn-pane active" id="pane-przeglad">
      <div class="pn-kpi" id="bi-kpi"></div>
      <div class="pn-grid2">
        <div class="pn-card"><h3>Zaproszenia wg statusu</h3><div id="bi-status"></div></div>
        <div class="pn-card"><h3>Najczęstsze tematy w zespole</h3><div id="bi-topics"></div></div>
      </div>
    </div>

    <div class="pn-pane" id="pane-nabory">
      <div class="pn-grid2" style="margin-bottom:.8rem">
        <input id="bi-q" class="pn-pick" type="search" placeholder="Szukaj naboru (np. CL5-2027)…">
        <select id="bi-status" class="pn-pick">
          <option value="">Wszystkie statusy</option>
          <option value="otwarty">otwarty</option>
          <option value="planowany">planowany</option>
          <option value="zamknięty">zamknięty</option>
          <option value="sprawdzić">sprawdzić</option>
        </select>
      </div>
      <div id="bi-calls"></div>
    </div>

    <div class="pn-pane" id="pane-nowe">
      <div class="pn-card pn-form" style="max-width:720px">
        <h3>Nowe zaproszenie (szkic)</h3>
        <label for="zp-osoba">Osoba</label><select id="zp-osoba"></select>
        <label for="zp-nabor">Nabór</label><select id="zp-nabor"></select>
        <label for="zp-rola">Proponowana rola</label><select id="zp-rola"><option>badawcza</option><option>zarządcza</option><option>wdrożeniowa</option><option>komunikacja</option></select>
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
  const KEY = 'bm-panel-v2';
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
  const SC = {'szkic': '#4f7fb0', 'zatwierdzone': '#5f9e80', 'wysłane': '#b08a4a', 'odpowiedź: tak': '#2f7d5b', 'odpowiedź: nie': '#b06464', 'brak odpowiedzi': '#8a94a6'};
  const CC = {'otwarty': '#5f9e80', 'planowany': '#4f7fb0', 'zamknięty': '#8a94a6', 'sprawdzić': '#b08a4a'};
  const pill = s => { const c = SC[s] || '#8a94a6'; return '<span class="pn-status" style="background:' + c + '22;color:' + c + ';border:1px solid ' + c + '">' + esc(s) + '</span>'; };
  const cpill = s => { const c = CC[s] || '#8a94a6'; return '<span class="pn-status" style="background:' + c + '22;color:' + c + ';border:1px solid ' + c + '">' + esc(s) + '</span>'; };
  const callLine = c => c ? esc(c.status) + ' · termin: ' + esc(c.deadlines.join(' · ') || 'brak') : 'brak danych';

  document.querySelectorAll('.seg-btn[data-view]').forEach(b => b.addEventListener('click', () => {
    document.querySelectorAll('.seg-btn[data-view]').forEach(x => x.classList.toggle('active', x === b));
    document.querySelectorAll('.pn-view').forEach(v => v.classList.toggle('active', v.id === 'view-' + b.dataset.view));
  }));
  document.querySelectorAll('.pn-sub button').forEach(b => b.addEventListener('click', () => {
    document.querySelectorAll('.pn-sub button').forEach(x => x.classList.toggle('active', x === b));
    document.querySelectorAll('.pn-pane').forEach(p => p.classList.toggle('active', p.id === 'pane-' + b.dataset.pane));
  }));

  /* ---------- NAUKOWIEC ---------- */
  function fillPeople(){
    const q = ($('pn-search').value || '').trim().toLowerCase();
    const list = people.filter(p => !q || p.name.toLowerCase().includes(q));
    const cur = $('pn-person').value;
    const opts = list.map(p => '<option value="' + esc(p.name) + '">' + esc(p.name) + '</option>').join('');
    $('pn-person').innerHTML = opts;
    if (list.some(p => p.name === cur)) $('pn-person').value = cur;
    $('zp-osoba').innerHTML = opts;
    $('zp-nabor').innerHTML = DATA.calls.map(c => '<option value="' + esc(c.id) + '">' + esc(c.id) + ' · ' + esc(c.status) + '</option>').join('');
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
    const mine = st.invites.map((i, idx) => Object.assign({}, i, {idx: idx})).filter(i => i.person === name && i.status !== 'szkic');
    if (!mine.length) { $('nk-invites').innerHTML = '<p class="pn-small">Brak zaproszeń. Biuro wysyła zaproszenia po zatwierdzeniu.</p>'; return; }
    $('nk-invites').innerHTML = mine.map(i => {
      const c = callsById[i.nabor];
      const answer = ANSWERS.includes(i.status) ? '' : '<div style="display:flex;gap:.4rem;margin-top:.6rem;flex-wrap:wrap"><button class="pn-btn" data-yes="' + i.idx + '" type="button">Chcę dołączyć</button><button class="pn-btn bad" data-no="' + i.idx + '" type="button">Nie w tym razie</button></div>';
      return '<div class="pn-inv"><div class="pn-inv-head"><div><b style="color:var(--text)">' + esc(i.nabor) + '</b><div class="pn-small">' + callLine(c) + '</div><div class="pn-small">Rola: ' + esc(i.rola) + (i.uzas ? ' · ' + esc(i.uzas) : '') + '</div></div>' + pill(i.status) + '</div>' + answer + '</div>';
    }).join('');
    $('nk-invites').querySelectorAll('[data-yes]').forEach(b => b.addEventListener('click', () => { st.invites[+b.dataset.yes].status = 'odpowiedź: tak'; save(); refresh(); }));
    $('nk-invites').querySelectorAll('[data-no]').forEach(b => b.addEventListener('click', () => { st.invites[+b.dataset.no].status = 'odpowiedź: nie'; save(); refresh(); }));
  }

  /* ---------- BIURO ---------- */
  function renderBiuroKpi(){
    const inv = st.invites;
    const cnt = s => inv.filter(i => i.status === s).length;
    const done = Object.values(st.profiles).filter(p => p.wnosze && p.wnosze.trim()).length;
    const open = DATA.calls.filter(c => c.status === 'otwarty').length;
    const answered = inv.filter(i => ANSWERS.includes(i.status)).length;
    $('bi-kpi').innerHTML = [
      [DATA.calls.length, 'naborów w bazie'],
      [open, 'naborów otwartych'],
      [inv.length, 'zaproszeń łącznie'],
      [answered + ' / ' + inv.length, 'z odpowiedzią']
    ].map(([v, l]) => '<div class="pn-card"><span class="pn-big">' + esc(v) + '</span><span class="pn-small">' + esc(l) + '</span></div>').join('');
    $('bi-status').innerHTML = STATUSES.map(s => '<div class="pn-row"><span>' + esc(s) + '</span><b>' + cnt(s) + '</b></div>').join('') +
      '<div class="pn-row"><span>profile uzupełnione</span><b>' + done + '</b></div>';
    const topicCount = {};
    people.forEach(p => p.topics.slice(0, 3).forEach(t => topicCount[t] = (topicCount[t] || 0) + 1));
    const top = Object.entries(topicCount).sort((a, b) => b[1] - a[1]).slice(0, 8);
    const max = top.length ? top[0][1] : 1;
    $('bi-topics').innerHTML = top.map(([t, n]) => '<div class="pn-bar"><div><div class="pn-small" style="color:var(--text)">' + esc(t) + '</div><div class="track"><i style="width:' + Math.round(n / max * 100) + '%"></i></div></div><span>' + n + '</span></div>').join('') || '<p class="pn-small">Brak danych</p>';
  }
  function renderBiuroCalls(){
    const q = ($('bi-q').value || '').trim().toLowerCase();
    const sf = $('bi-status').value;
    const calls = DATA.calls.filter(c => (!q || c.id.toLowerCase().includes(q)) && (!sf || c.status === sf));
    const html = calls.map(c => {
      const list = st.invites.map((i, idx) => Object.assign({}, i, {idx: idx})).filter(i => i.nabor === c.id);
      const count = s2 => list.filter(i => i.status === s2).length;
      const chips = '<div class="pn-chips" style="margin-top:.4rem">' + [
        ['szkic', count('szkic')], ['zatwierdzone', count('zatwierdzone')], ['wysłane', count('wysłane')],
        ['odpowiedź: tak', count('odpowiedź: tak')], ['odpowiedź: nie', count('odpowiedź: nie')], ['brak odpowiedzi', count('brak odpowiedzi')]
      ].filter(x => x[1] > 0).map(x => '<span class="pn-chip">' + esc(x[0]) + ': ' + x[1] + '</span>').join('') + '</div>';
      const rows = list.map(i => {
        let act = '';
        if (i.status === 'szkic') act = '<button class="pn-btn ghost" data-approve="' + i.idx + '" type="button">Zatwierdź</button>';
        else if (i.status === 'zatwierdzone') act = '<button class="pn-btn" data-send="' + i.idx + '" type="button">Otwórz e-mail</button>';
        return '<tr><td>' + esc(i.person) + '</td><td>' + esc(i.rola) + '</td><td>' + pill(i.status) + '</td><td>' + act + '</td></tr>';
      }).join('');
      const table = list.length ? '<table class="pn-table"><thead><tr><th>Osoba</th><th>Rola</th><th>Status</th><th>Akcja</th></tr></thead><tbody>' + rows + '</tbody></table>' : '<p class="pn-small">Brak zaproszeń do tego naboru.</p>';
      const batch = count('szkic') ? '<button class="pn-btn ghost" data-batch="' + esc(c.id) + '" type="button" style="margin-top:.5rem">Zatwierdź wszystkie szkice (' + count('szkic') + ')</button>' : '';
      return '<div class="pn-card" style="margin-bottom:.8rem"><div class="pn-inv-head"><div><b style="color:var(--text)">' + esc(c.id) + '</b><div class="pn-small">' + callLine(c) + ' · tematów: ' + c.topics + '</div></div>' + cpill(c.status) + '</div>' + chips + '<div style="margin-top:.6rem">' + table + '</div>' + batch + '</div>';
    }).join('');
    $('bi-calls').innerHTML = html || '<p class="pn-small">Brak naborów dla tych filtrów.</p>';
    $('bi-calls').querySelectorAll('[data-approve]').forEach(b => b.addEventListener('click', () => { st.invites[+b.dataset.approve].status = 'zatwierdzone'; save(); refresh(); }));
    $('bi-calls').querySelectorAll('[data-batch]').forEach(b => b.addEventListener('click', () => {
      st.invites.forEach(i => { if (i.nabor === b.dataset.batch && i.status === 'szkic') i.status = 'zatwierdzone'; });
      save(); refresh();
    }));
    $('bi-calls').querySelectorAll('[data-send]').forEach(b => b.addEventListener('click', () => {
      const i = st.invites[+b.dataset.send];
      const subj = encodeURIComponent('Zaproszenie do udziału: ' + i.nabor);
      const body = encodeURIComponent('Dzień dobry ' + i.person + ',\\n\\nzapraszamy do udziału w zespole dla naboru ' + i.nabor + ' w roli: ' + i.rola + '.\\n' + (i.uzas ? 'Uzasadnienie: ' + i.uzas + '.\\n' : '') + '\\nProsimy o odpowiedź, czy jest Pan/Pani zainteresowana/y.\\n\\nPozdrawiamy,\\nBiuro projektowe Wydziału Informatyki AGH');
      if (!confirm('Otworzyć wiadomość do ' + i.person + '? Status zaproszenia zmieni się na „wysłane”.')) return;
      i.status = 'wysłane'; i.sent = new Date().toISOString().slice(0, 10); save();
      window.location.href = 'mailto:?subject=' + subj + '&body=' + body;
      refresh();
    }));
  }
  $('bi-q').addEventListener('input', renderBiuroCalls);
  $('bi-status').addEventListener('change', renderBiuroCalls);

  $('zp-add').addEventListener('click', () => {
    const person = $('zp-osoba').value, nabor = $('zp-nabor').value;
    if (!person || !nabor) return;
    st.invites.push({person: person, nabor: nabor, rola: $('zp-rola').value, uzas: $('zp-uzas').value.trim(), status: 'szkic', created: DATA.today});
    toast('Szkic zapisany. Zatwierdź go, zanim wyślesz.');
    $('zp-uzas').value = '';
    save(); refresh();
    document.querySelector('.pn-sub button[data-pane="nabory"]').click();
  });
  $('pn-person').addEventListener('change', showPerson);
  $('pn-search').addEventListener('input', () => { fillPeople(); showPerson(); });
  $('pf-save').addEventListener('click', () => {
    const name = $('pn-person').value;
    st.profiles[name] = {wnosze: $('pf-wnosze').value.trim(), szukam: $('pf-szukam').value.trim(), dost: $('pf-dost').value, zain: $('pf-zain').value, zaktualizowano: DATA.today};
    save(); $('pf-saved').textContent = 'Zapisano lokalnie'; toast('Profil zapisany'); refresh();
  });

  function refresh(){ renderNaukInvites(); renderBiuroKpi(); renderBiuroCalls(); }
  fillPeople(); showPerson(); refresh();
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
