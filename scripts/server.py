import json
import sqlite3
import sys
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "baza.sqlite"
ALLOWED_KEYS = {"bm-projekty-v1", "bm-panel-v2"}
MAX_BODY = 2_000_000


def db():
    conn = sqlite3.connect(DB)
    conn.execute("CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT NOT NULL, updated TEXT NOT NULL)")
    return conn


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, fmt, *args):
        sys.stderr.write("%s %s\n" % (self.command, self.path))

    def _json(self, code, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _key(self):
        path = urlparse(self.path).path
        if not path.startswith("/api/kv/"):
            return None
        key = unquote(path[len("/api/kv/"):])
        return key if key in ALLOWED_KEYS else ""

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/health":
            return self._json(200, {"ok": True, "time": datetime.now(timezone.utc).isoformat()})
        if path.startswith("/api/"):
            key = self._key()
            if key is None:
                return self._json(404, {"error": "unknown endpoint"})
            if key == "":
                return self._json(403, {"error": "key not allowed"})
            with db() as conn:
                row = conn.execute("SELECT value FROM kv WHERE key = ?", (key,)).fetchone()
            return self._json(200, json.loads(row[0]) if row else None)
        return super().do_GET()

    def do_PUT(self):
        key = self._key()
        if key is None:
            return self._json(404, {"error": "unknown endpoint"})
        if key == "":
            return self._json(403, {"error": "key not allowed"})
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0 or length > MAX_BODY:
            return self._json(413, {"error": "bad body size"})
        raw = self.rfile.read(length).decode("utf-8")
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            return self._json(400, {"error": "invalid json"})
        now = datetime.now(timezone.utc).isoformat()
        with db() as conn:
            conn.execute(
                "INSERT INTO kv (key, value, updated) VALUES (?, ?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated = excluded.updated",
                (key, json.dumps(value, ensure_ascii=False), now),
            )
        return self._json(200, {"ok": True, "updated": now})


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    DB.parent.mkdir(parents=True, exist_ok=True)
    with db():
        pass
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Wspólna baza działa: http://127.0.0.1:{port}/biuro.html (Ctrl+C zatrzymuje serwer)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
