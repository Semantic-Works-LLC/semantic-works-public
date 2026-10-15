#!/usr/bin/env python3
"""Subway alerts recorder: serves ./site and keeps a history of MTA service alerts.

Standard library only. A background thread fetches the MTA's subway alerts feed
every 30 seconds, works out what changed since the last fetch and appends that
to data/alerts/history.jsonl. The page reads the history from /api/history and
replays it to show the alerts at any moment since recording began.

A second thread saves the MTA's other live subway feeds exactly as received,
each in its own folder under data/, one timestamped file per fetch: train
positions and predicted arrivals every 15 minutes, elevator and escalator
outages every 30 seconds when they have changed.

The browser also holds a Server-Sent Events connection to /__livereload;
whenever a file under ./site changes, the page refreshes itself.
"""
import calendar
import gzip
import hashlib
import json
import os
import ssl
import sys
import threading
import time
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HERE = Path(__file__).parent
ROOT = HERE / "site"
DATA = HERE / "data"
HISTORY = DATA / "alerts" / "history.jsonl"
FEEDS = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/"
FEED_URL = FEEDS + "camsys%2Fsubway-alerts.json"
DEFAULT_PORT = 8001
POLL_SECONDS = 30
TRAINS_SECONDS = 15 * 60
TIMESTAMP = "%Y-%m-%dT%H%M%SZ"
# Train positions and predicted arrivals: GTFS-realtime protobuf, one feed per group of lines.
TRAIN_FEEDS = {
    "1234567": "nyct%2Fgtfs",
    "ace": "nyct%2Fgtfs-ace",
    "bdfm": "nyct%2Fgtfs-bdfm",
    "g": "nyct%2Fgtfs-g",
    "jz": "nyct%2Fgtfs-jz",
    "nqrw": "nyct%2Fgtfs-nqrw",
    "l": "nyct%2Fgtfs-l",
    "si": "nyct%2Fgtfs-si",
}
ELEVATOR_FEEDS = {
    "elevator-outages": "nyct%2Fnyct_ene.json",
    "elevator-upcoming": "nyct%2Fnyct_ene_upcoming.json",
    "elevator-equipment": "nyct%2Fnyct_ene_equipments.json",
}
MERCURY = "transit_realtime.mercury_alert"
SYSTEM_CERTIFICATES = Path("/etc/ssl/cert.pem")  # python.org builds for macOS ship without any


RELOAD_POLL_SECONDS = 0.3
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


def tls_context():
    context = ssl.create_default_context()
    if SYSTEM_CERTIFICATES.exists():
        context.load_verify_locations(SYSTEM_CERTIFICATES)
    return context


def english(text):
    """The plain-English translation of a GTFS-realtime translated string."""
    for translation in (text or {}).get("translation", []):
        if translation.get("language") == "en":
            return translation.get("text", "")
    return ""


def compact(entity):
    """The parts of a feed entity the page uses."""
    alert = entity.get("alert", {})
    mercury = alert.get(MERCURY, {})
    routes, stops = [], []
    for informed in alert.get("informed_entity", []):
        route, stop = informed.get("route_id"), informed.get("stop_id")
        if route and route not in routes:
            routes.append(route)
        if stop and stop[:3] not in stops:  # platform ids are the station id plus N or S
            stops.append(stop[:3])
    return {
        "id": entity["id"],
        "type": mercury.get("alert_type", ""),
        "header": english(alert.get("header_text")),
        "description": english(alert.get("description_text")),
        "when": english(mercury.get("human_readable_active_period")),
        "routes": routes,
        "stops": stops,
        "periods": [[p.get("start", 0), p.get("end")] for p in alert.get("active_period", [])],
        "created": mercury.get("created_at"),
        "updated": mercury.get("updated_at"),
    }


def fetch_alerts():
    with urllib.request.urlopen(FEED_URL, timeout=20, context=tls_context()) as response:
        feed = json.load(response)
    return {entity["id"]: compact(entity) for entity in feed.get("entity", []) if "alert" in entity}


class Archive:
    """Saves raw feeds as data/<feed>/<timestamp>.<ext>.gz."""

    def __init__(self, root=DATA):
        self.root = root
        self.context = tls_context()
        self.last = {}  # elevator feed -> digest of the content last saved
        saved = sorted((root / "trains").glob("*.gz"))
        self.trains_at = calendar.timegm(time.strptime(saved[-1].name[:18], TIMESTAMP)) if saved else 0

    def fetch(self, path):
        with urllib.request.urlopen(FEEDS + path, timeout=20, context=self.context) as response:
            return response.read()

    def save(self, folder, name, body):
        (self.root / folder).mkdir(parents=True, exist_ok=True)
        with gzip.open(self.root / folder / name, "wb") as handle:
            handle.write(body)

    def poll_trains(self, stamp):
        for group, path in TRAIN_FEEDS.items():
            try:
                self.save("trains", f"{stamp}-{group}.pb.gz", self.fetch(path))
            except Exception as problem:  # one feed failing must not stop the others
                print(f"Train feed {group} failed: {type(problem).__name__}: {problem}", flush=True)

    def poll_elevators(self, stamp):
        for folder, path in ELEVATOR_FEEDS.items():
            try:
                body = self.fetch(path)
                digest = hashlib.sha1(body).digest()
                if self.last.get(folder) != digest:
                    self.save(folder, f"{stamp}.json.gz", body)
                    self.last[folder] = digest
            except Exception as problem:
                print(f"Feed {folder} failed: {type(problem).__name__}: {problem}", flush=True)

    def poll_forever(self):
        while True:
            started = time.time()
            stamp = time.strftime(TIMESTAMP, time.gmtime(started))
            if started - self.trains_at >= TRAINS_SECONDS:
                self.trains_at = started
                self.poll_trains(stamp)
            self.poll_elevators(stamp)
            time.sleep(max(1, POLL_SECONDS - (time.time() - started)))


class Recorder:
    """The change log, in memory and on disk, and the alerts as of the last fetch."""

    def __init__(self, path=HISTORY):
        self.path = path
        self.lock = threading.Lock()
        self.events = []  # {"t": seconds, "add": [alert, ...], "del": [id, ...]}
        self.current = {}
        self.checked = None  # when the feed was last fetched successfully
        self.error = None
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    self.apply(json.loads(line))

    def apply(self, event):
        for alert in event["add"]:
            self.current[alert["id"]] = alert
        for alert_id in event["del"]:
            self.current.pop(alert_id, None)
        self.events.append(event)

    def record(self, alerts, now):
        added = [alert for alert_id, alert in alerts.items() if self.current.get(alert_id) != alert]
        removed = [alert_id for alert_id in self.current if alert_id not in alerts]
        with self.lock:
            self.checked, self.error = now, None
            if added or removed:
                event = {"t": now, "add": added, "del": removed}
                self.path.parent.mkdir(parents=True, exist_ok=True)
                with self.path.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(event, separators=(",", ":")) + "\n")
                self.apply(event)

    def poll_forever(self):
        while True:
            try:
                self.record(fetch_alerts(), int(time.time()))
            except Exception as problem:  # keep recording whatever one fetch does
                with self.lock:
                    self.error = f"{type(problem).__name__}: {problem}"
                print(f"Feed fetch failed: {self.error}", flush=True)
            time.sleep(POLL_SECONDS)

    def since(self, index):
        with self.lock:
            return {
                "events": self.events[index:],
                "next": len(self.events),
                "checked": self.checked,
                "error": self.error,
                "now": int(time.time()),
            }


class Handler(SimpleHTTPRequestHandler):
    recorder = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        url = urlparse(self.path)
        if url.path == "/api/history":
            since = parse_qs(url.query).get("since", ["0"])[0]
            return self.send_json(self.recorder.since(int(since) if since.isdigit() else 0))
        if url.path == "/__livereload":
            return self.stream_reload_events()
        path = Path(self.translate_path(self.path))
        if path.is_dir():
            path = path / "index.html"
        if path.suffix == ".html" and path.is_file():
            return self.send_html(path)
        return super().do_GET()

    def send_html(self, path):
        body = path.read_bytes().replace(b"</body>", LIVERELOAD_SNIPPET + b"</body>", 1)
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
                time.sleep(RELOAD_POLL_SECONDS)
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

    def send_json(self, payload):
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, fmt, *args):
        if not any(quiet in (str(args[0]) if args else "") for quiet in ("/api/history", "/__livereload")):
            super().log_message(fmt, *args)


def make_server(port=DEFAULT_PORT, recorder=None):
    Handler.recorder = recorder or Recorder()
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.daemon_threads = True
    return server


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    port = int(argv[0]) if argv else DEFAULT_PORT
    recorder = Recorder()
    threading.Thread(target=recorder.poll_forever, daemon=True).start()
    threading.Thread(target=Archive().poll_forever, daemon=True).start()
    server = make_server(port, recorder)
    print(f"Subway alerts serving {ROOT} at http://localhost:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
