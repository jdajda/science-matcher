import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import dopasowanie as dp  # noqa: E402
import panel as pn  # noqa: E402


def render():
    head, header, theme_js = dp.site_parts()
    head = head.replace("Dopasowanie do naboru · Mapa badawcza WI AGH", "Profil osoby · Mapa badawcza WI AGH")
    tabs = dp.nav_html("naukowcy")
    local = ""
    people = pn.people()
    data = json.dumps({"people": people}, ensure_ascii=False).replace("</", "<\\/")
    script = SCRIPT.replace("__DATA__", data)
    return f"""{head}
<style>a.tab, a.tab:hover {{ text-decoration: none; }} .tab {{ white-space: normal; }}
.pf-top {{ display: flex; gap: 1rem; align-items: center; flex-wrap: wrap; margin: 1rem 0; }}
.pf-pick {{ min-width: 260px; padding: .5rem .7rem; border-radius: 8px; border: 1px solid var(--border); background: var(--bg); color: var(--text); font: inherit; font-size: .9rem; }}
.pf-view {{ display: none; }} .pf-view.active {{ display: block; }}
.pf-grid {{ display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 1rem; align-items: start; }}
.pf-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 14px; padding: 1rem 1.1rem; min-width: 0; }}
.pf-card h3 {{ font-size: .95rem; margin-bottom: .5rem; }}
.pf-head {{ display: flex; gap: .8rem; align-items: center; }}
.pf-av {{ width: 56px; height: 56px; border-radius: 50%; color: #fff; font-weight: 700; display: inline-flex; align-items: center; justify-content: center; flex-shrink: 0; }}
.pf-name {{ font-size: 1.05rem; font-weight: 700; color: var(--text); overflow-wrap: anywhere; }}
.pf-small {{ font-size: .82rem; color: var(--text2); line-height: 1.5; overflow-wrap: anywhere; }}
.pf-chips {{ display: flex; flex-wrap: wrap; gap: .35rem; margin-top: .5rem; }}
.pf-chip {{ font-size: .78rem; background: var(--surface2); color: var(--text2); border-radius: 999px; padding: .15rem .6rem; }}
.pf-row {{ display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: .6rem; align-items: center; padding: .55rem 0; border-top: 1px solid var(--border); font-size: .88rem; }}
.pf-row:first-child {{ border-top: none; }}
.pf-status {{ font-size: .75rem; font-weight: 600; border-radius: 999px; padding: .15rem .6rem; border: 1px solid var(--border); color: var(--text2); white-space: nowrap; }}
.pf-form label {{ display: block; font-size: .8rem; font-weight: 600; color: var(--text); margin: .6rem 0 .2rem; }}
.pf-form textarea, .pf-form select {{ width: 100%; box-sizing: border-box; padding: .5rem .65rem; border-radius: 8px; border: 1px solid var(--border); background: var(--bg); color: var(--text); font: inherit; font-size: .88rem; }}
.pf-btn {{ padding: .5rem 1rem; border-radius: 8px; border: 1px solid var(--accent); background: var(--accent); color: var(--on-accent); font: inherit; font-size: .86rem; font-weight: 600; cursor: pointer; }}
.pf-btn.ghost {{ background: transparent; color: var(--accent); }}
.pf-timeline {{ border-left: 2px solid var(--border); margin-left: .4rem; padding-left: .9rem; }}
.pf-tl {{ position: relative; padding: .3rem 0; font-size: .85rem; color: var(--text2); }}
.pf-tl::before {{ content: ''; position: absolute; left: -1.23rem; top: .55rem; width: 9px; height: 9px; border-radius: 50%; background: var(--accent); }}
@media (max-width: 900px) {{ .pf-grid {{ grid-template-columns: 1fr; }} }}
</style>
</head>
<body>
{header}
{tabs}
{local}

<main class="container">
  <section class="hero-simple">
    <div class="eyebrow">Profil osoby</div>
    <h1 class="hero-title">Profil osoby</h1>
    <p class="hero-sub">Ten sam profil w dwóch widokach: naukowca (co sam widzi i zmienia) i biura (projekty, zaproszenia, historia). Dane zapisują się tak samo jak w Panelu.</p>
  </section>

  <div class="pf-top">
    <select id="pf-person" class="pf-pick" aria-label="Wybór osoby"></select>
  </div>

  <div class="pf-view active" id="view-naukowiec" data-role-only="naukowiec">
    <div class="pf-grid">
      <div class="pf-card">
        <div class="pf-head"><span class="pf-av" id="nk-av"></span><div><div class="pf-name" id="nk-name"></div><div class="pf-small" id="nk-meta"></div></div></div>
        <h3 style="margin-top:.8rem">Obszary i tematy</h3>
        <div class="pf-chips" id="nk-topics"></div>
        <h3 style="margin-top:.9rem">Ostatnie prace</h3>
        <div class="pf-small" id="nk-works"></div>
      </div>
      <div class="pf-stack">
        <div class="pf-card pf-form">
          <h3>Mój opis</h3>
          <label for="nk-wnosze">Co wnoszę do projektu</label>
          <textarea id="nk-wnosze" rows="3"></textarea>
          <label for="nk-szukam">Jakich kompetencji lub partnerów szukam</label>
          <textarea id="nk-szukam" rows="3"></textarea>
          <label for="nk-dost">Dostępność</label>
          <select id="nk-dost"><option>do ustalenia</option><option>tak</option><option>nie</option></select>
          <label for="nk-zain">Zainteresowanie nowymi projektami</label>
          <select id="nk-zain"><option>nie wiem</option><option>tak</option><option>nie</option></select>
          <div style="margin-top:.8rem"><button class="pf-btn" id="nk-save" type="button">Zapisz</button> <span class="pf-small" id="nk-saved"></span></div>
        </div>
        <div class="pf-card">
          <h3>Zaproszenia do naborów</h3>
          <div id="nk-invites"></div>
        </div>
      </div>
    </div>
  </div>

  <div class="pf-view" id="view-biuro" data-role-only="biuro">
    <div class="pf-grid">
      <div class="pf-card">
        <div class="pf-head"><span class="pf-av" id="bi-av"></span><div><div class="pf-name" id="bi-name"></div><div class="pf-small" id="bi-meta"></div></div></div>
        <h3 style="margin-top:.8rem">Opis z profilu</h3>
        <div class="pf-small" id="bi-desc"></div>
        <h3 style="margin-top:.9rem">Tematy</h3>
        <div class="pf-chips" id="bi-topics"></div>
      </div>
      <div class="pf-stack">
        <div class="pf-card">
          <h3>Projekty z zespołem</h3>
          <div id="bi-projects"></div>
        </div>
        <div class="pf-card">
          <h3>Zaproszenia i historia</h3>
          <div id="bi-invites"></div>
          <h3 style="margin-top:.9rem">Historia</h3>
          <div class="pf-timeline" id="bi-timeline"></div>
        </div>
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
  const initials = n => n.split(/\\s+/).filter(Boolean).slice(0,2).map(p => p[0]).join('').toUpperCase();
  const people = DATA.people;
  const ANSWERS = ['odpowiedź: tak', 'odpowiedź: nie', 'brak odpowiedzi'];
  const LABEL = {'szkic': 'szkic', 'zatwierdzone': 'zatwierdzone', 'wysłane': 'wysłane', 'odpowiedź: tak': 'dołącza', 'odpowiedź: nie': 'nie dołącza', 'brak odpowiedzi': 'brak odpowiedzi'};
  let panel = {profiles: {}, invites: []};
  let biuro = {cards: {}, custom: []};
  let current = new URLSearchParams(location.search).get('osoba') || (people[0] && people[0].name);

  function saveLocal(key, v){ try { localStorage.setItem(key, JSON.stringify(v)); } catch(e) {} }
  function loadLocal(key, fb){ try { return JSON.parse(localStorage.getItem(key) || 'null') || fb; } catch(e) { return fb; } }
  async function loadRemote(key){ try { const r = await fetch('/api/kv/' + encodeURIComponent(key), {cache: 'no-store'}); return r.ok ? await r.json() : null; } catch(e) { return null; } }
  function persist(key, v){
    saveLocal(key, v);
    fetch('/api/kv/' + encodeURIComponent(key), {method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(v)}).catch(() => {});
  }

  document.querySelectorAll('button.seg-btn[data-view]').forEach(b => b.addEventListener('click', () => {
    document.querySelectorAll('button.seg-btn[data-view]').forEach(x => { x.classList.toggle('active', x === b); x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
    document.querySelectorAll('.pf-view').forEach(v => v.classList.toggle('active', v.id === 'view-' + b.dataset.view));
  }));

  function fillPicker(){
    $('pf-person').innerHTML = people.map(p => '<option value="' + esc(p.name) + '"' + (p.name === current ? ' selected' : '') + '>' + esc(p.name) + '</option>').join('');
  }
  function color(name){ const p = people.find(x => x.name === name); return (p && p.color) || '#4f7fb0'; }

  function renderNaukowiec(){
    const p = people.find(x => x.name === current); if (!p) return;
    const pr = panel.profiles[current] || {};
    $('nk-av').style.background = color(current); $('nk-av').textContent = initials(current);
    $('nk-name').textContent = current;
    $('nk-meta').textContent = p.works + ' prac od 2019' + (p.orcid ? ' · ORCID' : ' · ORCID brak');
    $('nk-topics').innerHTML = p.topics.map(t => '<span class="pf-chip">' + esc(t) + '</span>').join('') || '<span class="pf-small">Brak tematów</span>';
    $('nk-works').innerHTML = p.recent.length ? p.recent.map(t => '• ' + esc(t)).join('<br>') : 'Brak prac';
    $('nk-wnosze').value = pr.wnosze || ''; $('nk-szukam').value = pr.szukam || '';
    $('nk-dost').value = pr.dost || 'do ustalenia'; $('nk-zain').value = pr.zain || 'nie wiem';
    $('nk-saved').textContent = '';
    const inv = panel.invites.map((i, idx) => Object.assign({}, i, {idx: idx})).filter(i => i.person === current && i.status !== 'szkic');
    $('nk-invites').innerHTML = inv.length ? inv.map(i => '<div class="pf-row"><div><b style="color:var(--text)">' + esc(i.nabor) + '</b><div class="pf-small">rola: ' + esc(i.rola) + (i.uzas ? ' · ' + esc(i.uzas) : '') + '</div>' +
      (ANSWERS.includes(i.status) ? '' : '<div style="display:flex;gap:.4rem;margin-top:.5rem"><button class="pf-btn" data-yes="' + i.idx + '" type="button">Chcę dołączyć</button><button class="pf-btn ghost" data-no="' + i.idx + '" type="button">Nie w tym razie</button></div>') +
      '</div><span class="pf-status">' + esc(LABEL[i.status] || i.status) + '</span></div>').join('') : '<p class="pf-small">Brak zaproszeń. Biuro wysyła je po zatwierdzeniu.</p>';
    $('nk-invites').querySelectorAll('[data-yes]').forEach(b => b.addEventListener('click', () => answer(+b.dataset.yes, 'odpowiedź: tak')));
    $('nk-invites').querySelectorAll('[data-no]').forEach(b => b.addEventListener('click', () => answer(+b.dataset.no, 'odpowiedź: nie')));
  }
  function answer(idx, status){ panel.invites[idx].status = status; persist(PANEL_KEY, panel); renderAll(); }

  function allProjects(){
    const base = DATA.projects.map(p => Object.assign({}, p, biuro.cards[p.id] || {}));
    const custom = biuro.custom.map(p => Object.assign({}, p, biuro.cards[p.id] || {}));
    return base.concat(custom);
  }
  function renderBiuro(){
    const p = people.find(x => x.name === current); if (!p) return;
    const pr = panel.profiles[current] || {};
    $('bi-av').style.background = color(current); $('bi-av').textContent = initials(current);
    $('bi-name').textContent = current;
    $('bi-meta').textContent = (p.field || 'dziedzina nieznana') + ' · prac: ' + p.works + (p.orcid ? ' · ORCID' : '');
    $('bi-desc').innerHTML = pr.wnosze ? esc(pr.wnosze) + '<br><br><b style="color:var(--text)">Szuka:</b> ' + esc(pr.szukam || '–') : 'Osoba nie uzupełniła profilu.';
    $('bi-topics').innerHTML = p.topics.map(t => '<span class="pf-chip">' + esc(t) + '</span>').join('') || '<span class="pf-small">Brak tematów</span>';
    const projects = allProjects().filter(x => (x.people || []).includes(current));
    $('bi-projects').innerHTML = projects.length ? projects.map(x => '<div class="pf-row"><div><b style="color:var(--text)">' + esc(x.title) + '</b><div class="pf-small">' + esc(x.status || '') + (x.deadlines && x.deadlines.length ? ' · termin: ' + esc(x.deadlines.join(' · ')) : '') + '</div></div><span class="pf-status">' + esc(x.column || '') + '</span></div>').join('') : '<p class="pf-small">Nie jest przypisana do żadnego projektu.</p>';
    const inv = panel.invites.filter(i => i.person === current);
    $('bi-invites').innerHTML = inv.length ? inv.map(i => '<div class="pf-row"><div><b style="color:var(--text)">' + esc(i.nabor) + '</b><div class="pf-small">rola: ' + esc(i.rola) + '</div></div><span class="pf-status">' + esc(LABEL[i.status] || i.status) + '</span></div>').join('') : '<p class="pf-small">Brak zaproszeń.</p>';
    const events = [];
    inv.forEach(i => {
      if (i.created) events.push([i.created, 'Utworzono szkic zaproszenia do ' + i.nabor]);
      if (i.sent) events.push([i.sent, 'Wysłano zaproszenie do ' + i.nabor]);
      if (ANSWERS.includes(i.status)) events.push([i.sent || i.created || '', 'Odpowiedź: ' + (LABEL[i.status] || i.status) + ' (' + i.nabor + ')']);
    });
    if (pr.zaktualizowano) events.push([pr.zaktualizowano, 'Profil zaktualizowany przez osobę']);
    events.sort((a, b) => (b[0] || '').localeCompare(a[0] || ''));
    $('bi-timeline').innerHTML = events.length ? events.map(e => '<div class="pf-tl">' + esc(e[0]) + ' · ' + esc(e[1]) + '</div>').join('') : '<div class="pf-small">Brak zdarzeń.</div>';
  }

  function renderAll(){ renderNaukowiec(); renderBiuro(); }

  $('pf-person').addEventListener('change', e => { current = e.target.value; history.replaceState(null, '', '?osoba=' + encodeURIComponent(current)); renderAll(); });
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
