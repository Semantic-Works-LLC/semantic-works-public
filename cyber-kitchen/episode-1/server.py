#!/usr/bin/env python3
"""Cyber Kitchen dev server: serves ./site and live-reloads the browser on change.

Standard library only. The browser holds a Server-Sent Events connection to
/__livereload; whenever a file under ./site changes, the server pushes a
"reload" event and the page refreshes itself.
"""
import os
import sys
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).parent / "site"
DEFAULT_PORT = 8000
POLL_SECONDS = 0.3
PING_EVERY = 50  # polls between keep-alive comments

LIVERELOAD_SNIPPET = b"""
<script>
(function () {
  var source = new EventSource("/__livereload");
  source.addEventListener("reload", function () { location.reload(); });
})();
</script>
"""


def site_fingerprint():
    """Newest mtime plus file count, so edits, additions and deletions all register."""
    newest, count = 0.0, 0
    for dirpath, _, filenames in os.walk(ROOT):
        for name in filenames:
            try:
                newest = max(newest, os.stat(os.path.join(dirpath, name)).st_mtime)
                count += 1
            except OSError:
                pass
    return newest, count


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        if self.path == "/__livereload":
            return self.stream_reload_events()
        path = Path(self.translate_path(self.path))
        if path.is_dir():
            path = path / "index.html"
        if path.suffix == ".html" and path.is_file():
            return self.send_html(path)
        return super().do_GET()

    def send_html(self, path):
        body = path.read_bytes()
        marker = b"</body>"
        if marker in body:
            body = body.replace(marker, LIVERELOAD_SNIPPET + marker, 1)
        else:
            body += LIVERELOAD_SNIPPET
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def stream_reload_events(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        last = site_fingerprint()
        ticks = 0
        try:
            while True:
                time.sleep(POLL_SECONDS)
                current = site_fingerprint()
                if current != last:
                    last = current
                    self.wfile.write(b"event: reload\ndata: changed\n\n")
                    self.wfile.flush()
                ticks += 1
                if ticks % PING_EVERY == 0:  # keep-alive comment, also detects closed tabs
                    self.wfile.write(b": ping\n\n")
                    self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, fmt, *args):
        if "/__livereload" not in (str(args[0]) if args else ""):
            super().log_message(fmt, *args)


def make_server(port=DEFAULT_PORT):
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.daemon_threads = True
    return server


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    port = int(argv[0]) if argv else DEFAULT_PORT
    ROOT.mkdir(exist_ok=True)
    server = make_server(port)
    print(f"Cyber Kitchen serving {ROOT} at http://localhost:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
