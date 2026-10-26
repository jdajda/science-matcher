import collections
import html as h
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import dopasowanie as dp  # noqa: E402


def people():
    prof = {p.get("wi_name"): p for p in json.loads((ROOT / "data/wi_profiles.json").read_text(encoding="utf-8"))}
    tem = {t["wi_name"]: t for t in json.loads((ROOT / "data/wi_tematy_osob.json").read_text(encoding="utf-8"))}
    out = []
    for name in sorted(set(prof) | set(tem)):
        p = prof.get(name, {})
        t = tem.get(name, {})
        works = p.get("works") or []
        years = [w.get("year") for w in works if w.get("year")]
        out.append({
            "name": name,
            "orcid": p.get("orcid") or "",
            "works_count": p.get("works_count") or 0,
            "last_year": max(years) if years else 0,
            "field": ((t.get("tematy") or [{}])[0].get("field") or ""),
            "topics": [{"name": x["name"], "w": x.get("weight", 0), "field": x.get("field") or ""} for x in (t.get("tematy") or [])[:15]],
            "works": [{"title": w.get("title") or "", "year": w.get("year") or 0, "kw": w.get("keywords") or []} for w in works[:30]],
        })
    return out


def field_options(people_list):
    fields = sorted({p["field"] for p in people_list if p.get("field")})
    return "".join(f'<option value="{h.escape(f)}">{h.escape(f)}</option>' for f in fields)


def render():
    head, header, theme_js = dp.site_parts()
    head = head.replace("Dopasowanie do naboru · Mapa badawcza WI AGH", "Wyszukiwarka · Mapa badawcza WI AGH")
    tabs = dp.nav_html("wyszukiwarka") + dp.local_nav([("ws-results", "Wyniki"), ("ws-team-box", "Zespół")])
    ppl = people()
    head_html = head
    field_counts = collections.Counter(p["field"] for p in ppl if p.get("field"))
    topic_counts = collections.Counter()
    for p in ppl:
        for t in p["topics"][:3]:
            topic_counts[t["name"]] += 1
    hints = {
        "needs": [
            "analiza szeregów czasowych",
            "optymalizacja i algorytmy ewolucyjne",
            "uczenie maszynowe w predykcji",
            "przetwarzanie danych w chmurze",
            "zarządzanie projektem badawczym",
        ],
        "fields": field_counts.most_common(8),
        "topics": topic_counts.most_common(8),
    }
    data = json.dumps({"people": ppl, "stop": sorted(dp.STOP), "hints": hints}, ensure_ascii=False).replace("</", "<\\/")
    script = SCRIPT.replace("__DATA__", data)
    body_fields = field_options(ppl)
    return f"""{head}
<style>a.tab, a.tab:hover {{ text-decoration: none; }} 
.ws-layout {{ display: grid; grid-template-columns: 300px minmax(0, 1fr); gap: 1.2rem; align-items: start; }}
.ws-side {{ background: var(--surface); border: 1px solid var(--border); border-radius: 14px; padding: 1rem 1.1rem; position: sticky; top: 1rem; font-size: .88rem; }}
.ws-side .side-block {{ border-top: 1px solid var(--border); padding: .8rem 0; display: flex; flex-direction: column; gap: .35rem; }}
.ws-side .side-label {{ font-weight: 600; color: var(--text); display: block; }}
.ws-side textarea, .ws-side input, .ws-side select {{ width: 100%; box-sizing: border-box; padding: .45rem .6rem; border-radius: 8px; border: 1px solid var(--border); background: var(--bg); color: var(--text); font: inherit; font-size: .86rem; }}
.ws-side .f-check {{ display: flex; align-items: center; gap: .5rem; }}
.ws-side .f-check input {{ width: 15px; height: 15px; margin: 0; }}
.ws-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 14px; padding: 1rem 1.1rem; margin-bottom: .8rem; }}
.ws-head {{ display: flex; justify-content: space-between; gap: .8rem; align-items: flex-start; flex-wrap: wrap; }}
.ws-name {{ font-weight: 700; color: var(--text); font-size: .98rem; }}
.ws-small {{ font-size: .8rem; color: var(--text2); line-height: 1.45; }}
.ws-pill {{ font-size: .75rem; font-weight: 600; border-radius: 999px; padding: .15rem .6rem; border: 1px solid var(--border); background: var(--surface2); color: var(--text2); white-space: nowrap; }}
.ws-pill.ok {{ color: #2f7d5b; border-color: #2f7d5b; }} .ws-pill.part {{ color: #b08a4a; border-color: #b08a4a; }} .ws-pill.miss {{ color: #b06464; border-color: #b06464; }} .ws-pill.unk {{ color: #8a94a6; border-color: #8a94a6; }}
.ws-needs {{ margin-top: .6rem; display: grid; gap: .35rem; }}
.ws-need {{ display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: .5rem; align-items: start; font-size: .84rem; border-top: 1px solid var(--border); padding-top: .35rem; }}
.ws-need small {{ color: var(--text2); display: block; line-height: 1.4; }}
.ws-bar {{ height: 6px; border-radius: 3px; background: var(--surface2); overflow: hidden; margin-top: .5rem; }}
.ws-bar i {{ display: block; height: 100%; background: var(--accent); }}
.ws-team {{ position: sticky; top: 1rem; }}
.ws-chip {{ display: inline-block; font-size: .75rem; color: var(--text2); background: var(--surface2); border-radius: 999px; padding: .1rem .55rem; margin: .15rem .2rem .15rem 0; }}
@media (max-width: 1000px) {{ .ws-layout {{ grid-template-columns: 1fr; }} .ws-side, .ws-team {{ position: static; }} }}
</style>
</head>
<body>
{header}
{tabs}

<main class="container">
  <section class="hero-simple">
    <div class="eyebrow">Wyszukiwarka</div>
    <h1 class="hero-title">Szukaj osób po potrzebach</h1>
    <p class="hero-sub">Wpisz potrzeby projektu, jedną na wiersz. Dla każdej osoby system pokazuje, które potrzeby są spełnione, częściowo spełnione, niespełnione lub do potwierdzenia. Liczba publikacji nie decyduje o wyniku.</p>
  </section>

  <div class="ws-layout">
    <aside class="ws-side">
      <div class="side-block">
        <span class="side-label">Potrzeby (jedna na wiersz)</span>
        <textarea id="ws-needs" rows="6" placeholder="np. optymalizacja z użyciem uczenia maszynowego&#10;analiza szeregów czasowych&#10;zarządzanie projektem"></textarea>
        <button id="ws-run" class="link-btn" type="button" style="text-align:left">Szukaj</button>
      </div>
      <div class="side-block">
        <span class="side-label">Aktualność</span>
        <select id="ws-recent">
          <option value="0">bez ograniczeń</option>
          <option value="2022">prace od 2022</option>
          <option value="2024">prace od 2024</option>
        </select>
      </div>
      <div class="side-block">
        <span class="side-label">Pokrycie potrzeb (min.)</span>
        <select id="ws-min">
          <option value="0">dowolne</option>
          <option value="0.5">co najmniej 50%</option>
          <option value="0.75">co najmniej 75%</option>
        </select>
      </div>
      <div class="side-block">
        <span class="side-label">Dziedzina badawcza</span>
        <select id="ws-field"><option value="">wszystkie</option>{body_fields}</select>
      </div>
      <div class="side-block">
        <span class="side-label">Minimalna liczba prac</span>
        <select id="ws-minw">
          <option value="0">bez ograniczeń</option>
          <option value="10">co najmniej 10</option>
          <option value="30">co najmniej 30</option>
          <option value="100">co najmniej 100</option>
        </select>
      </div>
      <div class="side-block">
        <span class="side-label">Identyfikatory</span>
        <label class="f-check"><input type="checkbox" id="ws-orcid"> tylko osoby z ORCID</label>
      </div>
      <div class="side-block">
        <span class="side-label">Dane, których brak nie wyklucza</span>
        <label class="f-check"><input type="checkbox" id="ws-unk" checked> pokaż osoby z potrzebami do potwierdzenia</label>
      </div>
      <div class="side-block">
        <span class="side-label">Wkrótce (wymaga danych)</span>
        <select disabled title="Wymaga danych z CWP"><option>Rola w projekcie</option></select>
        <select disabled title="Wymaga rejestru szkoleń"><option>Certyfikat</option></select>
        <select disabled title="Wymaga profilu dostępności"><option>Dostępność</option></select>
      </div>
      <div class="side-block">
        <button id="ws-reset" class="link-btn" type="button" style="text-align:left">Wyczyść</button>
      </div>
    </aside>

    <div>
      <div id="ws-results"></div>
      <div class="ws-card ws-team" id="ws-team-box" style="margin-top:1rem">
        <div class="ws-head"><div><div class="ws-name">Zespół i łączne pokrycie</div><div class="ws-small">Zaznacz osoby z listy wyników. Pokazujemy, które potrzeby zespół pokrywa razem.</div></div></div>
        <div id="ws-team"></div>
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
  const STOP = new Set(DATA.stop);
  const PEOPLE = DATA.people;
  const $ = id => document.getElementById(id);
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const W = {topic: 1.0, keyword: 0.8, work: 0.6};
  const LABEL = {ok: 'spełnione', part: 'częściowo', miss: 'niespełnione', unk: 'do potwierdzenia'};
  let lastRows = [];
  let selected = new Set();

  function fold(s){ return String(s).normalize('NFD').replace(/[\\u0300-\\u036f]/g, '').toLowerCase(); }
  function toks(s){ return (fold(s).match(/[a-z0-9]{3,}/g) || []).filter(t => !STOP.has(t)); }

  function index(person, recentFrom){
    const idx = {};
    const put = (tok, kind, label) => { if (!idx[tok] || idx[tok].w < W[kind]) idx[tok] = {w: W[kind], kind: kind, label: label}; };
    person.topics.forEach(t => toks(t.name).forEach(tok => put(tok, 'topic', t.name)));
    person.works.filter(w => !recentFrom || w.year >= recentFrom).forEach(w => {
      w.kw.forEach(k => toks(k).forEach(tok => put(tok, 'keyword', k)));
      toks(w.title).forEach(tok => put(tok, 'work', w.title));
    });
    return idx;
  }

  function needStatus(need, person, recentFrom){
    const words = toks(need);
    if (!words.length) return {status: 'unk', score: 0, evidence: []};
    if (!person.works.length && !person.topics.length) return {status: 'unk', score: 0, evidence: []};
    const idx = index(person, recentFrom);
    let sum = 0; const ev = [];
    words.forEach(w => { const h = idx[w]; if (h) { sum += h.w; ev.push({token: w, kind: h.kind, label: h.label}); } });
    const score = sum / words.length;
    const status = score >= 0.5 ? 'ok' : (score > 0 ? 'part' : 'miss');
    return {status: status, score: score, evidence: ev};
  }

  function evaluate(needs, recentFrom){
    return PEOPLE.map(p => {
      if (recentFrom && p.last_year < recentFrom) return null;
      const per = needs.map(n => Object.assign({need: n}, needStatus(n, p, recentFrom)));
      const pts = per.map(x => x.status === 'ok' ? 1 : x.status === 'part' ? 0.5 : 0);
      const cov = needs.length ? pts.reduce((a, b) => a + b, 0) / needs.length : 0;
      const unk = per.filter(x => x.status === 'unk').length;
      return {p: p, per: per, cov: cov, unk: unk};
    }).filter(Boolean);
  }

  function pill(st){ return '<span class="ws-pill ' + st + '">' + LABEL[st] + '</span>'; }

  function run(){
    const needs = $('ws-needs').value.split('\\n').map(s => s.trim()).filter(Boolean);
    if (!needs.length) { $('ws-results').innerHTML = '<p class="ws-small">Dodaj co najmniej jedną potrzebę.</p>'; return; }
    const recentFrom = parseInt($('ws-recent').value, 10) || 0;
    const minCov = parseFloat($('ws-min').value) || 0;
    const allowUnk = $('ws-unk').checked;
    const fld = $('ws-field').value, minW = parseInt($('ws-minw').value, 10) || 0, needOrcid = $('ws-orcid').checked;
    let rows = evaluate(needs, recentFrom).filter(r => r.cov >= minCov || (allowUnk && r.unk > 0 && r.cov + r.unk / needs.length >= minCov))
      .filter(r => (!fld || r.p.field === fld) && r.p.works_count >= minW && (!needOrcid || r.p.orcid));
    rows.sort((a, b) => (b.cov - a.cov) || (b.p.last_year - a.p.last_year) || a.p.name.localeCompare(b.p.name));
    lastRows = rows.slice(0, 60);
    if (!lastRows.length) { $('ws-results').innerHTML = '<p class="ws-small">Brak osób spełniających kryteria. Zmień potrzeby albo filtry.</p>'; renderTeam(needs); return; }
    $('ws-results').innerHTML = '<p class="ws-small" style="margin-bottom:.6rem">Pokazano ' + lastRows.length + ' osób. Kolejność: pokrycie potrzeb, potem aktualność.</p>' + lastRows.map((r, i) => {
      const pct = Math.round(r.cov * 100);
      const tops = r.p.topics.slice(0, 4).map(t => '<span class="ws-chip">' + esc(t.name) + '</span>').join('');
      const rowsHtml = r.per.map(x => '<div class="ws-need"><div>' + esc(x.need) + (x.evidence.length ? '<small>dowód: ' + esc(x.evidence.slice(0, 3).map(e => e.token + ' (' + e.kind + ': ' + e.label + ')').join('; ')) + '</small>' : '<small>brak dowodu w tematach i pracach</small>') + '</div>' + pill(x.status) + '</div>').join('');
      return '<div class="ws-card"><div class="ws-head"><div><label class="f-check ws-name"><input type="checkbox" data-team="' + esc(r.p.name) + '" ' + (selected.has(r.p.name) ? 'checked' : '') + '> ' + (i + 1) + '. ' + esc(r.p.name) + '</label><div class="ws-small">ostatnia praca: ' + (r.p.last_year || 'brak danych') + ' · prac: ' + r.p.works_count + (r.p.orcid ? ' · <a href="' + esc(r.p.orcid) + '" target="_blank" rel="noopener">ORCID</a>' : ' · ORCID brak') + '</div></div><div><span class="ws-pill ' + (pct >= 75 ? 'ok' : pct >= 40 ? 'part' : 'miss') + '">pokrycie ' + pct + '%</span></div></div><div class="ws-bar"><i style="width:' + pct + '%"></i></div><div style="margin-top:.4rem">' + tops + '</div><div class="ws-needs">' + rowsHtml + '</div></div>';
    }).join('');
    document.querySelectorAll('[data-team]').forEach(c => c.addEventListener('change', e => {
      const n = e.target.dataset.team;
      if (e.target.checked) selected.add(n); else selected.delete(n);
      renderTeam(needs);
    }));
    renderTeam(needs);
  }

  function renderTeam(needs){
    if (!needs || !needs.length) { $('ws-team').innerHTML = '<p class="ws-small">Najpierw wpisz potrzeby.</p>'; return; }
    const members = lastRows.filter(r => selected.has(r.p.name));
    if (!members.length) { $('ws-team').innerHTML = '<p class="ws-small">Zaznacz osoby na liście wyników, żeby zobaczyć łączne pokrycie.</p>'; return; }
    const recentFrom = parseInt($('ws-recent').value, 10) || 0;
    const per = needs.map((n, i) => {
      let best = {status: 'miss', score: 0, who: ''};
      members.forEach(m => {
        const x = needStatus(n, m.p, recentFrom);
        if (x.status === 'unk') { if (best.status === 'miss') best = {status: 'unk', score: 0, who: ''}; return; }
        if (x.score > best.score) best = {status: x.status, score: x.score, who: m.p.name};
      });
      return {need: n, status: best.status, who: best.who};
    });
    const cov = Math.round(per.reduce((a, x) => a + (x.status === 'ok' ? 1 : x.status === 'part' ? 0.5 : 0), 0) / needs.length * 100);
    const gaps = per.filter(x => x.status !== 'ok');
    $('ws-team').innerHTML = '<div class="ws-head"><div class="ws-small">Członkowie: ' + members.map(m => esc(m.p.name)).join(', ') + '</div><span class="ws-pill ' + (cov >= 75 ? 'ok' : cov >= 40 ? 'part' : 'miss') + '">zespół pokrywa ' + cov + '%</span></div>' +
      '<div class="ws-needs">' + per.map(x => '<div class="ws-need"><div>' + esc(x.need) + (x.who ? '<small>pokrywa: ' + esc(x.who) + '</small>' : '') + '</div>' + pill(x.status) + '</div>').join('') + '</div>' +
      (gaps.length ? '<p class="ws-small" style="margin-top:.6rem">Luki do uzupełnienia: ' + gaps.map(g => esc(g.need)).join('; ') + '. Brak dowodu nie oznacza braku kompetencji.</p>' : '');
  }

  function showHints(){
    const H = DATA.hints;
    $('ws-results').innerHTML =
      '<div class="ws-card"><div class="ws-name">Zacznij od potrzeby</div><div class="ws-small" style="margin:.3rem 0 .6rem">Kliknij przykład, żeby wypełnić pole i od razu zobaczyć wyniki.</div>' +
      H.needs.map(n => { const c = evaluate([n], 0).filter(r => r.per[0].status !== 'miss').length; return '<button class="ws-chip ws-pick" type="button" data-need="' + esc(n) + '">' + esc(n) + ' · ' + c + ' os.</button>'; }).join('') + '</div>' +
      '<div class="ws-card"><div class="ws-name">Dziedziny w bazie</div><div class="ws-small" style="margin:.3rem 0 .6rem">Ile osób z WI ma profil w danej dziedzinie. Kliknij, żeby zawęzić.</div>' +
      H.fields.map(f => '<button class="ws-chip ws-pick" type="button" data-field="' + esc(f[0]) + '">' + esc(f[0]) + ' · ' + f[1] + '</button>').join('') + '</div>' +
      '<div class="ws-card"><div class="ws-name">Najczęstsze tematy zespołu</div><div class="ws-small" style="margin:.3rem 0 .6rem">Tematy pojawiające się u największej liczby osób. Kliknij, żeby dodać do potrzeb.</div>' +
      H.topics.map(t => '<button class="ws-chip ws-pick" type="button" data-need="' + esc(t[0]) + '">' + esc(t[0]) + ' · ' + t[1] + '</button>').join('') + '</div>';
    $('ws-results').querySelectorAll('[data-need]').forEach(b => b.addEventListener('click', () => {
      const cur = $('ws-needs').value.trim();
      $('ws-needs').value = cur ? cur + '\\n' + b.dataset.need : b.dataset.need;
      run();
    }));
    $('ws-results').querySelectorAll('[data-field]').forEach(b => b.addEventListener('click', () => {
      $('ws-field').value = b.dataset.field;
      if ($('ws-needs').value.trim()) run(); else showFieldList(b.dataset.field);
    }));
  }
  function showFieldList(field){
    const list = PEOPLE.filter(p => p.field === field).sort((a, b) => b.works_count - a.works_count);
    $('ws-results').innerHTML = '<div class="ws-card"><div class="ws-name">' + esc(field) + ' · ' + list.length + ' osób</div><div class="ws-small" style="margin:.3rem 0 .6rem">Dodaj potrzeby po lewej, żeby zobaczyć pokrycie.</div>' +
      list.slice(0, 40).map(p => '<div class="ws-need"><div>' + esc(p.name) + '<small>prac: ' + p.works_count + (p.orcid ? ' · ORCID' : '') + '</small></div></div>').join('') + '</div>';
  }

  $('ws-run').addEventListener('click', run);
  $('ws-field').addEventListener('change', () => { if ($('ws-needs').value.trim()) run(); else showFieldList($('ws-field').value); });
  $('ws-needs').addEventListener('keydown', e => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) run(); });
  $('ws-reset').addEventListener('click', () => { $('ws-needs').value = ''; $('ws-field').value = ''; $('ws-minw').value = '0'; $('ws-orcid').checked = false; selected = new Set(); lastRows = []; showHints(); renderTeam([]); });
  showHints();
  renderTeam([]);
})();
</script>"""


def main():
    out = ROOT / "wyszukiwarka.html"
    out.write_text(render(), encoding="utf-8")
    print(f"zapisano: {out}")


if __name__ == "__main__":
    main()
