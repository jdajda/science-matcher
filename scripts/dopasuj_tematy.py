import argparse
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KEY = "oyhcoVTirbvKXToBnvzbn0"
API = "https://api.openalex.org"
COVER_THRESHOLD = 0.05


def search_topics(text):
    url = API + "/topics?" + urllib.parse.urlencode({
        "search": text,
        "per-page": 3,
        "select": "id,display_name,subfield,works_count",
        "api_key": KEY,
    })
    data = json.load(urllib.request.urlopen(url, timeout=60))
    return [
        {
            "id": t["id"].split("/")[-1],
            "name": t["display_name"],
            "subfield": (t.get("subfield") or {}).get("display_name"),
            "zatwierdzone": False,
        }
        for t in data.get("results", [])
    ]


def propose(call_file):
    cfg = json.loads(call_file.read_text(encoding="utf-8"))
    for c in cfg["pojecia"]:
        if c.get("tematy"):
            continue
        c["tematy"] = search_topics(c["pojecie"])
        time.sleep(0.2)
    call_file.write_text(json.dumps(cfg, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"propozycje mapowania zapisane: {call_file} (zatwierdź pole 'zatwierdzone')")


def score(call_file, profiles_file, top_n):
    cfg = json.loads(call_file.read_text(encoding="utf-8"))
    profiles = json.loads(profiles_file.read_text(encoding="utf-8"))
    concepts = []
    for c in cfg["pojecia"]:
        approved = [t for t in c.get("tematy", []) if t.get("zatwierdzone")]
        concepts.append({"pojecie": c["pojecie"], "waga": float(c.get("waga", 1.0)), "tematy": approved})
    unmapped = [c["pojecie"] for c in concepts if not c["tematy"]]
    mapped = [c for c in concepts if c["tematy"]]
    total_w = sum(c["waga"] for c in mapped) or 1.0

    rows = []
    for p in profiles:
        weights = {t["id"]: t for t in p.get("tematy", [])}
        per_concept = []
        score_sum = 0.0
        covered = 0
        for c in mapped:
            best = None
            for t in c["tematy"]:
                hit = weights.get(t["id"])
                if hit and (best is None or hit["weight"] > best["weight"]):
                    best = {"temat": t["name"], "weight": hit["weight"], "prace": hit.get("works", [])}
            s = best["weight"] if best else 0.0
            score_sum += c["waga"] * s
            if s >= COVER_THRESHOLD:
                covered += 1
            per_concept.append({"pojecie": c["pojecie"], "wynik": round(s, 3), "dowod": best})
        if score_sum == 0:
            continue
        rows.append({
            "wi_name": p.get("wi_name"),
            "openalex_id": p.get("openalex_id"),
            "wynik": round(score_sum / total_w, 3),
            "pokrycie": round(covered / len(mapped), 3) if mapped else 0,
            "pojecia": per_concept,
        })
    rows.sort(key=lambda r: (r["wynik"], r["pokrycie"]), reverse=True)
    out = {
        "nabor": cfg.get("call"),
        "nieopisane_pojecia": unmapped,
        "osob_z_trafieniem": len(rows),
        "top": rows[:top_n],
        "uwaga": "Wynik to dowód z tematów OpenAlex, nie ocena kompetencji. Weryfikuje biuro.",
    }
    dest = ROOT / "data" / f"dopasowanie_tematy_{cfg.get('call')}.json"
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"osób z trafieniem: {len(rows)}; nieopisane pojęcia: {unmapped}")
    for r in out["top"][:10]:
        print(f"{r['wi_name']:<32} wynik={r['wynik']:<6} pokrycie={r['pokrycie']}")
    print(f"zapisano: {dest}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("propose")
    a.add_argument("call_file")
    b = sub.add_parser("score")
    b.add_argument("call_file")
    b.add_argument("--profiles", default=str(ROOT / "data/wi_tematy_osob.json"))
    b.add_argument("--top", type=int, default=20)
    args = ap.parse_args()
    if args.cmd == "propose":
        propose(Path(args.call_file))
    else:
        score(Path(args.call_file), Path(args.profiles), args.top)


if __name__ == "__main__":
    main()
