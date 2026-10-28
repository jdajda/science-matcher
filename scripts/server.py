"""Wspólna baza i role dla portalu.

Uruchomienie:
  python3 scripts/server.py 8000          # serwer
  python3 scripts/server.py user add ana@agh.edu.pl biuro
  python3 scripts/server.py user list

Logowanie jest tymczasowe (dev): /api/dev-login?user=... ustawia ciasteczko,
działa tylko gdy BM_DEV=1 i serwer słucha na 127.0.0.1. Po wdrożeniu SSO AGH
endpoint dev-login zostanie zastąpiony logowaniem uczelnianym.
"""
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from http.cookies import SimpleCookie
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "baza.sqlite"
MAX_BODY = 2_000_000
ROLES = {"biuro", "koordynator", "naukowiec", "admin"}

# klucz -> role, które mogą czytać i zapisywać
PERMS = {
    "bm-projekty-v1": {"read": {"biuro", "koordynator"}, "write": {"biuro", "koordynator"}},
    "bm-panel-v2": {"read": {"biuro", "koordynator"}, "write": {"biuro", "koordynator"}},
    "bm-baza-nowe": {"read": {"biuro", "koordynator"}, "write": {"biuro", "koordynator"}},
    "bm-nabor-projekt": {"read": {"biuro", "koordynator"}, "write": {"biuro", "koordynator"}},
    "bm-projekt-opiekun": {"read": {"biuro", "koordynator"}, "write": {"koordynator"}},
}


def now():
    return datetime.now(timezone.utc).isoformat()


def db():
    conn = sqlite3.connect(DB)
    conn.execute("CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT NOT NULL, updated TEXT NOT NULL)")
    conn.execute("CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, role TEXT NOT NULL)")
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
        ts = now()
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
