"""Wspólna baza i role dla portalu.

Uruchomienie:
  python3 scripts/server.py 8000          # serwer
  python3 scripts/server.py user add ana@agh.edu.pl biuro
  python3 scripts/server.py user list

Logowanie jest tymczasowe (dev): /api/dev-login?user=... ustawia ciasteczko,
działa tylko gdy BM_DEV=1 i serwer słucha na 127.0.0.1. Po wdrożeniu SSO AGH
endpoint dev-login zostanie zastąpiony logowaniem uczelnianym.
"""
import html as htmllib
import json
import os
import secrets
import sqlite3
import sys
import threading
from datetime import datetime, timedelta, timezone
from http.cookies import SimpleCookie
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

TOKEN_DAYS = 14
PANEL_KEY = "bm-panel-v3"
HISTORY_KEYS = {"bm-baza-stan", "bm-baza-pula", "bm-baza-kier", "bm-trl-v1", "bm-nabor-partner-v1", "bm-projekt-opiekun"}
LOCK = threading.Lock()

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "baza.sqlite"
MAX_BODY = 2_000_000
ROLES = {"biuro", "koordynator", "naukowiec", "admin"}

# klucz -> role, które mogą czytać i zapisywać
PERMS = {
    "bm-projekty-v1": {"read": {"biuro", "koordynator"}, "write": {"biuro", "koordynator"}},
    "bm-panel-v2": {"read": {"biuro", "koordynator"}, "write": {"biuro", "koordynator"}},
    "bm-panel-v3": {"read": {"biuro", "koordynator"}, "write": {"biuro", "koordynator"}},
    "bm-audit-v1": {"read": {"biuro", "koordynator"}, "write": {"biuro", "koordynator"}},
    "bm-baza-nowe": {"read": {"biuro", "koordynator"}, "write": {"biuro", "koordynator"}},
    "bm-nabor-projekt": {"read": {"biuro", "koordynator"}, "write": {"biuro", "koordynator"}},
    "bm-projekt-opiekun": {"read": {"biuro", "koordynator"}, "write": {"koordynator"}},
    "bm-trl-v1": {"read": {"biuro", "koordynator"}, "write": {"biuro", "koordynator"}},
    "bm-nabor-partner-v1": {"read": {"biuro", "koordynator"}, "write": {"biuro", "koordynator"}},
    "bm-partnerzy-v1": {"read": {"biuro", "koordynator"}, "write": {"biuro", "koordynator"}},
    "bm-baza-stan": {"read": {"biuro", "koordynator"}, "write": {"biuro", "koordynator"}},
    "bm-baza-pula": {"read": {"biuro", "koordynator"}, "write": {"biuro", "koordynator"}},
    "bm-baza-kier": {"read": {"biuro", "koordynator"}, "write": {"biuro", "koordynator"}},
}


def invite_key(inv):
    return str(inv.get("created") or "") + "|" + str(inv.get("person") or "") + "|" + str(inv.get("nabor") or "")


def now():
    return datetime.now(timezone.utc).isoformat()


def db():
    conn = sqlite3.connect(DB)
    conn.execute("CREATE TABLE IF NOT EXISTS tokens (token TEXT PRIMARY KEY, invite_key TEXT NOT NULL, created TEXT NOT NULL, expires TEXT NOT NULL, answered TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT NOT NULL, updated TEXT NOT NULL)")
    conn.execute("CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, role TEXT NOT NULL)")
    conn.execute("CREATE TABLE IF NOT EXISTS historia (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL, email TEXT, key TEXT NOT NULL, item TEXT NOT NULL, before TEXT, after TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS audit (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL, email TEXT, action TEXT NOT NULL, key TEXT, bytes INTEGER)")
    return conn


def cli(argv):
    with db() as conn:
        if argv[:2] == ["user", "add"] and len(argv) == 4:
            email, role = argv[2].lower(), argv[3]
            if role not in ROLES:
                print(f"nieznana rola: {role}. Dozwolone: {', '.join(sorted(ROLES))}")
                return 1
            conn.execute("INSERT INTO users (email, role) VALUES (?, ?) ON CONFLICT(email) DO UPDATE SET role = excluded.role", (email, role))
            print(f"dodano: {email} ({role})")
            return 0
        if argv[:2] == ["user", "list"]:
            for email, role in conn.execute("SELECT email, role FROM users ORDER BY email"):
                print(f"{email}\t{role}")
            return 0
    print(__doc__)
    return 1


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, fmt, *args):
        sys.stderr.write("%s %s\n" % (self.command, self.path))

    def _json(self, code, payload, cookie=None):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()
        self.wfile.write(body)

    def _user(self):
        raw = self.headers.get("Cookie")
        if not raw:
            return None
        c = SimpleCookie()
        c.load(raw)
        if "bm_user" not in c:
            return None
        email = unquote(c["bm_user"].value).lower()
        with db() as conn:
            row = conn.execute("SELECT role FROM users WHERE email = ?", (email,)).fetchone()
        return {"email": email, "role": row[0]} if row else None

    def _audit(self, user, action, key=None, size=None):
        with db() as conn:
            conn.execute("INSERT INTO audit (ts, email, action, key, bytes) VALUES (?, ?, ?, ?, ?)",
                         (now(), user["email"] if user else None, action, key, size))

    def _key(self):
        path = urlparse(self.path).path
        if not path.startswith("/api/kv/"):
            return None
        key = unquote(path[len("/api/kv/"):])
        return key if key in PERMS else ""

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/health":
            return self._json(200, {"ok": True, "time": now()})
        if path == "/api/dev-login":
            return self._dev_login()
        if path == "/api/me":
            user = self._user()
            return self._json(200, {"user": user})
        if path == "/odpowiedz":
            return self._answer_page(parse_qs(urlparse(self.path).query).get("t", [""])[0])
        if path == "/api/historia":
            user = self._user()
            if not user or user["role"] not in {"biuro", "koordynator"}:
                return self._json(401 if not user else 403, {"error": "brak dostępu"})
            with db() as conn:
                rows = conn.execute("SELECT ts, email, key, item, before, after FROM historia ORDER BY id DESC LIMIT 200").fetchall()
            return self._json(200, [dict(zip(["ts", "email", "key", "item", "before", "after"], r)) for r in rows])
        if path == "/api/audit":
            user = self._user()
            if not user or user["role"] not in {"koordynator", "admin"}:
                return self._json(403, {"error": "brak uprawnień"})
            with db() as conn:
                rows = conn.execute("SELECT ts, email, action, key, bytes FROM audit ORDER BY id DESC LIMIT 200").fetchall()
            return self._json(200, [dict(zip(["ts", "email", "action", "key", "bytes"], r)) for r in rows])
        if path.startswith("/api/"):
            key = self._key()
            if key is None:
                return self._json(404, {"error": "unknown endpoint"})
            if key == "":
                return self._json(403, {"error": "key not allowed"})
            user = self._user()
            if not user or user["role"] not in PERMS[key]["read"]:
                return self._json(401 if not user else 403, {"error": "brak dostępu"})
            with db() as conn:
                row = conn.execute("SELECT value FROM kv WHERE key = ?", (key,)).fetchone()
            return self._json(200, json.loads(row[0]) if row else None)
        return super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/api/zaproszenie-link":
            return self._make_link()
        if path == "/odpowiedz":
            return self._save_answer()
        return self._json(404, {"error": "unknown endpoint"})

    def _read_body(self):
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0 or length > MAX_BODY:
            return None
        return self.rfile.read(length).decode("utf-8")

    def _make_link(self):
        user = self._user()
        if not user or user["role"] not in {"biuro", "koordynator"}:
            return self._json(401 if not user else 403, {"error": "brak uprawnień"})
        raw = self._read_body()
        try:
            key = str(json.loads(raw or "{}").get("invite_key", ""))
        except Exception:
            return self._json(400, {"error": "invalid json"})
        if not key:
            return self._json(400, {"error": "brak klucza zaproszenia"})
        token = secrets.token_urlsafe(24)
        t = datetime.now(timezone.utc)
        with db() as conn:
            conn.execute("INSERT INTO tokens (token, invite_key, created, expires) VALUES (?, ?, ?, ?)",
                         (token, key, t.isoformat(), (t + timedelta(days=TOKEN_DAYS)).isoformat()))
        self._audit(user, "link", key)
        return self._json(200, {"url": "/odpowiedz?t=" + token, "wygasa": (t + timedelta(days=TOKEN_DAYS)).date().isoformat()})

    def _find_invite(self, token):
        with db() as conn:
            row = conn.execute("SELECT invite_key, expires FROM tokens WHERE token = ?", (token,)).fetchone()
            if not row:
                return None, "Link jest nieprawidłowy."
            if datetime.fromisoformat(row[1]) < datetime.now(timezone.utc):
                return None, "Link wygasł. Poproś biuro o nowy."
            pr = conn.execute("SELECT value FROM kv WHERE key = ?", (PANEL_KEY,)).fetchone()
        panel = json.loads(pr[0]) if pr and pr[0] else {"invites": []}
        for inv in panel.get("invites", []):
            if isinstance(inv, dict) and invite_key(inv) == row[0]:
                return inv, None
        return None, "Zaproszenie nie istnieje albo zostało zmienione."

    def _answer_page(self, token):
        inv, err = self._find_invite(token) if token else (None, "Brak linku.")
        if err:
            body = f"<h1>Odpowiedź na zaproszenie</h1><p>{htmllib.escape(err)}</p>"
        else:
            e = htmllib.escape
            body = (f"<h1>Odpowiedź na zaproszenie</h1>"
                    f"<p><b>{e(inv.get('projekt') or inv.get('nabor') or '')}</b></p>"
                    f"<p>Rola w projekcie: {e(inv.get('rola') or '')}</p>"
                    f"<p>{e(inv.get('opis') or '')}</p>"
                    f"<form method=\"post\" action=\"/odpowiedz\">"
                    f"<input type=\"hidden\" name=\"t\" value=\"{e(token)}\">"
                    f"<button name=\"odp\" value=\"tak\">Chcę dołączyć</button> "
                    f"<button name=\"odp\" value=\"nie\">Nie w tym razie</button></form>")
        page = ("<!doctype html><html lang=\"pl\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
                "<title>Odpowiedź na zaproszenie</title><style>body{font-family:system-ui,sans-serif;max-width:560px;margin:3rem auto;padding:0 1rem;color:#1d2433}"
                "button{font:inherit;padding:.6rem 1rem;border-radius:8px;border:1px solid #5f7fa8;background:#eef3fa;cursor:pointer;margin-right:.5rem}</style></head>"
                f"<body>{body}</body></html>")
        data = page.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _save_answer(self):
        raw = self._read_body() or ""
        form = parse_qs(raw)
        token = form.get("t", [""])[0]
        odp = form.get("odp", [""])[0]
        if odp not in {"tak", "nie"}:
            return self._json(400, {"error": "nieprawidłowa odpowiedź"})
        with LOCK:
            inv, err = self._find_invite(token)
            if err:
                return self._json(403, {"error": err})
            with db() as conn:
                key = conn.execute("SELECT invite_key FROM tokens WHERE token = ?", (token,)).fetchone()[0]
                pr = conn.execute("SELECT value FROM kv WHERE key = ?", (PANEL_KEY,)).fetchone()
                panel = json.loads(pr[0]) if pr and pr[0] else {"invites": []}
                today = datetime.now(timezone.utc).date().isoformat()
                for it in panel.get("invites", []):
                    if isinstance(it, dict) and invite_key(it) == key:
                        it["status"] = "odpowiedź: tak" if odp == "tak" else "odpowiedź: nie"
                        it["answered"] = today
                conn.execute("INSERT INTO kv (key, value, updated) VALUES (?, ?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated = excluded.updated",
                             (PANEL_KEY, json.dumps(panel, ensure_ascii=False), now()))
                conn.execute("UPDATE tokens SET answered = ? WHERE token = ?", (now(), token))
            self._audit(None, "odpowiedz", key, None)
        self.send_response(303)
        self.send_header("Location", "/odpowiedz?t=" + token)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _dev_login(self):
        if os.environ.get("BM_DEV") != "1" or self.client_address[0] != "127.0.0.1":
            return self._json(404, {"error": "not available"})
        q = parse_qs(urlparse(self.path).query)
        email = (q.get("user", [""])[0]).lower()
        with db() as conn:
            row = conn.execute("SELECT role FROM users WHERE email = ?", (email,)).fetchone()
        if not row:
            return self._json(403, {"error": "nieznany użytkownik, dodaj go przez: user add"})
        cookie = f"bm_user={email}; Path=/; HttpOnly; SameSite=Strict"
        self._audit({"email": email}, "login")
        return self._json(200, {"user": {"email": email, "role": row[0]}}, cookie=cookie)

    def do_PUT(self):
        key = self._key()
        if key is None:
            return self._json(404, {"error": "unknown endpoint"})
        if key == "":
            return self._json(403, {"error": "key not allowed"})
        user = self._user()
        if not user:
            return self._json(401, {"error": "zaloguj się"})
        if user["role"] not in PERMS[key]["write"]:
            return self._json(403, {"error": "brak uprawnień do zapisu"})
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0 or length > MAX_BODY:
            return self._json(413, {"error": "bad body size"})
        raw = self.rfile.read(length).decode("utf-8")
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            return self._json(400, {"error": "invalid json"})
        if key == PANEL_KEY and isinstance(value, dict):
            with db() as conn:
                row = conn.execute("SELECT value FROM kv WHERE key = ?", (key,)).fetchone()
            old = json.loads(row[0]).get("invites", []) if row and row[0] else []
            omap = {invite_key(i): i for i in old if isinstance(i, dict)}
            for inv in value.get("invites", []):
                if not isinstance(inv, dict):
                    continue
                prev = omap.get(invite_key(inv))
                prev_status = prev.get("status") if prev else None
                if inv.get("status") == "szkic" and prev_status != "szkic":
                    inv["autor_email"] = user["email"]
                if prev and prev_status == "szkic" and inv.get("status") == "zatwierdzone":
                    if prev.get("autor_email") and prev["autor_email"] == user["email"]:
                        return self._json(403, {"error": "zatwierdzenie musi wykonać inna osoba niż autor szkicu"})
                    inv["zatwierdzil_email"] = user["email"]
                    if prev.get("autor_email"):
                        inv["autor_email"] = prev["autor_email"]
        ts = now()
        if key in HISTORY_KEYS and isinstance(value, dict):
            with db() as conn:
                row = conn.execute("SELECT value FROM kv WHERE key = ?", (key,)).fetchone()
                old = json.loads(row[0]) if row and row[0] else {}
                if not isinstance(old, dict):
                    old = {}
                for item in sorted(set(old) | set(value), key=str):
                    before, after = old.get(item), value.get(item)
                    if before != after:
                        conn.execute("INSERT INTO historia (ts, email, key, item, before, after) VALUES (?, ?, ?, ?, ?, ?)",
                                     (ts, user["email"], key, str(item),
                                      json.dumps(before, ensure_ascii=False) if before is not None else None,
                                      json.dumps(after, ensure_ascii=False) if after is not None else None))
        with db() as conn:
            conn.execute(
                "INSERT INTO kv (key, value, updated) VALUES (?, ?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated = excluded.updated",
                (key, json.dumps(value, ensure_ascii=False), ts),
            )
        self._audit(user, "save", key, len(raw))
        return self._json(200, {"ok": True, "updated": ts, "by": user["email"]})


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ("user",):
        sys.exit(cli(sys.argv[1:]))
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    DB.parent.mkdir(parents=True, exist_ok=True)
    with db():
        pass
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Serwer działa: http://127.0.0.1:{port}/index.html (Ctrl+C zatrzymuje)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
