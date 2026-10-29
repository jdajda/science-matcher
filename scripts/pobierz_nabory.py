import argparse
import html as h
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "https://api.tech.ec.europa.eu/search-api/prod/rest/search"


def search(text, page, size=100):
    url = API + "?" + urllib.parse.urlencode({"apiKey": "SEDIA", "text": text, "pageSize": size, "pageNumber": page})
    body = {"bool": {"must": [{"terms": {"status": ["0", "1"]}}]}}
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}, method="POST")
    return json.load(urllib.request.urlopen(req, timeout=120))


def first(meta, key):
    v = meta.get(key) if isinstance(meta, dict) else None
    return v[0] if isinstance(v, list) and v else (v or "")


def plain(text):
    return h.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", str(text or "")))).strip()


PARTNER_RE = re.compile(
    r"seeking (new )?partners|looking for (new )?partners|partners? (are|is) (sought|needed|wanted)|"
    r"call for partners|partner search|expression of interest|consortium (partners|members) (are )?(sought|needed)",
    re.I,
)


def topic_status(tid, call, texts):
    for t in texts.get(call, ()):
        m = re.search(r"submission session is now available for:(.*)", t, re.I)
        if m and tid in m.group(1):
            return "otwarty"
        if re.search(r"has closed on|closed on", t, re.I):
            return "zamknięty"
    return "nieustalony (sprawdzić)"


def collect(prefix, pages, texts):
    found = {}
    for page in range(1, pages + 1):
        data = search(prefix, page)
        for r in data.get("results", []):
            url = r.get("url") or ""
            if "topic-details" not in url:
                continue
            meta = r.get("metadata") or {}
            call = first(meta, "callIdentifier")
            if not call.startswith(prefix):
                continue
            tid = url.rsplit("/", 1)[-1].replace(".json", "")
            desc = plain(first(meta, "description"))
            texts.setdefault(call, set()).add(desc)
            deadlines = sorted({d[:10] for d in (meta.get("deadlineDate") or []) if d})
            if tid in found:
                deadlines = sorted(set(deadlines) | set(found[tid]["terminy"]))
            found[tid] = {
                "id": tid,
                "call": call,
                "title": r.get("summary") or "",
                "start": first(meta, "startDate"),
                "terminy": deadlines,
                "model": first(meta, "deadlineModel"),
                "opis": desc[:200],
                "url": url,
                "szuka_partnerow": bool(PARTNER_RE.search(desc)),
            }
        if not data.get("results"):
            break
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prefixes", nargs="+", help="np. HORIZON-CL4-2027 HORIZON-CL5-2027")
    ap.add_argument("--pages", type=int, default=3)
    ap.add_argument("--out", default=str(ROOT / "data/nabory_sedia.json"))
    args = ap.parse_args()

    all_topics = {}
    texts = {}
    for prefix in args.prefixes:
        found = collect(prefix, args.pages, texts)
        print(f"{prefix}: tematów {len(found)}")
        all_topics.update(found)

    items = sorted(all_topics.values(), key=lambda t: (t["call"], t["id"]))
    for t in items:
        t["status"] = topic_status(t["id"], t["call"], texts)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"zapisano {len(items)} tematów: {args.out}")


if __name__ == "__main__":
    main()
