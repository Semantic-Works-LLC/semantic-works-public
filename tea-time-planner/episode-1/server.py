"""Tiny static server with live reload: pages poll /__version and reload on change.

Also saves screenshots of the app (via snapshot.py) a few seconds after the page's files settle.
"""
import http.server
import os
import socketserver
import subprocess
import sys
import threading
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
PORT = 8000


def latest_mtime():
    newest = 0.0
    for dirpath, dirnames, filenames in os.walk(ROOT):
        # screenshots change on their own; they must not reload the page
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d != "screenshots"]
        for name in filenames:
            # only files the page loads should reload it (not notes, scripts or screenshots)
            if not name.endswith((".html", ".js", ".css")):
                continue
            try:
                newest = max(newest, os.path.getmtime(os.path.join(dirpath, name)))
            except OSError:
                pass
    return newest


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def do_GET(self):
        if self.path == "/__version":
            body = str(latest_mtime()).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, fmt, *args):
        if "/__version" not in (args[0] if args else ""):
            super().log_message(fmt, *args)


def snapshot_watcher(settle=5.0):
    """Run snapshot.py once the page's files have stopped changing for `settle` seconds."""
    script = os.path.join(ROOT, "snapshot.py")
    sources = [os.path.join(ROOT, n) for n in ("index.html", "scenes3d.js")]

    def stamp():
        return max((os.path.getmtime(p) for p in sources if os.path.exists(p)), default=0)

    seen = None
    changed_at = time.time()  # take one snapshot shortly after startup
    while True:
        time.sleep(1)
        now = stamp()
        if now != seen:
            seen, changed_at = now, time.time()
        elif changed_at and time.time() - changed_at > settle:
            changed_at = 0
            subprocess.run([sys.executable, script], cwd=ROOT)


class Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    with Server(("127.0.0.1", PORT), Handler) as httpd:
        print(f"Serving {ROOT} at http://localhost:{PORT}")
        threading.Thread(target=snapshot_watcher, daemon=True).start()
        httpd.serve_forever()
