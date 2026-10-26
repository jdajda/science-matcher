import json
import math
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KEY = "oyhcoVTirbvKXToBnvzbn0"
API = "https://api.openalex.org"
REF_YEAR = 2026
DECAY_YEARS = 6
POSITION_WEIGHT = {"first": 1.0, "last": 1.0, "middle": 0.6}


def get(path, params):
    params = dict(params, api_key=KEY)
    url = API + path + "?" + urllib.parse.urlencode(params)
    return json.load(urllib.request.urlopen(url, timeout=120))


def author_position(work, author_id):
    for a in work.get("authorships", []):
        aid = ((a.get("author") or {}).get("id") or "")
        if aid.endswith(author_id):
            return a.get("author_position") or "middle"
    return "middle"


def person_profile(author_id):
    data = get("/works", {
        "filter": f"authorships.author.id:{author_id},publication_year:>2018",
        "per-page": 200,
        "select": "id,title,publication_year,primary_topic,topics,authorships",
    })
    topics = {}
    for w in data.get("results", []):
        year = w.get("publication_year") or REF_YEAR
        recency = math.exp(-(REF_YEAR - year) / DECAY_YEARS)
        pos = POSITION_WEIGHT.get(author_position(w, author_id), 0.6)
        base = recency * pos
        seen = set()
        candidates = []
        if w.get("primary_topic"):
            candidates.append((w["primary_topic"], 1.0))
        for t in w.get("topics") or []:
            candidates.append((t, 0.5 * (t.get("score") or 0.5)))
        for t, mult in candidates:
            tid = (t.get("id") or "").split("/")[-1]
            if not tid or tid in seen:
                continue
            seen.add(tid)
            entry = topics.setdefault(tid, {
                "id": tid,
                "name": t.get("display_name"),
                "field": ((t.get("field") or {}).get("display_name")),
                "subfield": ((t.get("subfield") or {}).get("display_name")),
                "weight": 0.0,
                "works": [],
            })
            entry["weight"] += base * mult
            if len(entry["works"]) < 3:
                entry["works"].append({"title": w.get("title"), "year": year})
    ordered = sorted(topics.values(), key=lambda x: x["weight"], reverse=True)[:40]
    top = ordered[0]["weight"] if ordered else 1.0
    for t in ordered:
        t["weight"] = round(t["weight"] / top, 4)
    return ordered, len(data.get("results", []))


def main():
    profiles = json.loads((ROOT / "data/wi_profiles.json").read_text(encoding="utf-8"))
    out = []
    for p in profiles:
        if not p.get("id"):
            continue
        aid = p["id"].split("/")[-1]
        try:
            topics, n_works = person_profile(aid)
        except Exception as e:
            print("blad", p.get("wi_name"), str(e)[:80])
            continue
        out.append({
            "wi_name": p.get("wi_name"),
            "openalex_id": p["id"],
            "prac_brane_pod_uwage": n_works,
            "tematy": topics,
        })
        time.sleep(0.15)
    dest = ROOT / "data/wi_tematy_osob.json"
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"zapisano {len(out)} profili tematycznych: {dest}")


if __name__ == "__main__":
    main()
