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
    src = (ROOT / "index.html").read_text(encoding="utf-8").splitlines()
    head = "\n".join(src[0:409])
    header = "\n".join(src[411:430])
    theme_js = "\n".join(src[1802:1818])
    head = re.sub(r"<title>.*?</title>", "<title>Dopasowanie do naboru · Mapa badawcza WI AGH</title>", head, count=1)
    header = re.sub(r"<nav class=\"tabs\">.*?</nav>", "", header, flags=re.S)
    return head, header, theme_js


def card(i, r):
    orcid = r.get("orcid")
    link = (
        f"<a class='s-link' href='{h.escape(orcid)}' target='_blank' rel='noopener'>ORCID →</a>"
        if orcid else "<span class='s-link'>ORCID brak</span>"
    )
    hits = "".join(
        f"<li><b>{h.escape(x['token'])}</b> ← {SOURCE_LABEL[x['source']]}: {h.escape(x['evidence'])}</li>"
        for x in r["hits"][:8]
    ) or "<li>brak trafień</li>"
    pct = round(r["coverage"] * 100)
    color = person_color(r.get("field"))
    return f"""
    <article class="staff-card" style="border-left:3px solid {color}88">
      <div class="s-head">
        <div class="s-av" style="background:{color}cc;color:#fff">{h.escape(initials(r['wi_name']))}</div>
        <div class="s-id">
          <h3>{i}. {h.escape(r['wi_name'])}</h3>
          <div class="s-sub">{h.escape(r.get('openalex_name') or '')}</div>
        </div>
      </div>
      <div class="s-pills">
        <span class="s-pill" style="--c:{SCORE_COLOR}">wynik {r['score']}</span>
        <span class="s-pill" style="--c:{coverage_color(r['coverage'])}">pokrycie {pct}%</span>
        <span class="s-pill" style="--c:{color}">{h.escape(r.get('field') or '')}</span>
      </div>
      <ul class="s-kw" style="padding-left:1.1rem">{hits}</ul>
      <div class="s-foot"><span>{r['score']} trafień z tematu</span>{link}</div>
    </article>"""


def section(call_id, nabor, out):
    terms = "".join(f"<span class='s-pill'>{h.escape(t)}</span>" for t in out["topic_terms"])
    cards = "".join(card(i, r) for i, r in enumerate(out["top"], 1))
    return f"""
  <section class="call-section" id="{h.escape(call_id)}" style="margin-bottom:2.2rem">
    <div class="eyebrow">Nabór Horyzont Europa</div>
    <h2 class="hero-title" style="font-size:1.5rem">{h.escape(call_id)}</h2>
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


def render_html(sections):
    head, header, theme_js = site_parts()
    tabs = """
<nav class="tabs">
  <div class="container tabs-row">
    <a class="tab" href="index.html#staff">Naukowcy</a>
    <a class="tab" href="index.html#areas">Obszary badawcze</a>
    <a class="tab" href="index.html#match">Dobierz zespół</a>
    <a class="tab" href="index.html#graph">Graf współpracy</a>
    <a class="tab active" href="dopasowanie.html">Dopasowanie do naboru</a>
  </div>
</nav>"""
    body = "".join(section(*sec) for sec in sections)
    return f"""{head}
<style>a.tab, a.tab:hover {{ text-decoration: none; }}</style>
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
{body}
</main>

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
