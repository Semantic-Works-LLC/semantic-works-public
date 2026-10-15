"""Tests for server.py: static serving, live-reload snippet injection and the event stream."""
import http.client
import os
import runpy
import socket
import sys
import threading
import time
from http.server import ThreadingHTTPServer

import pytest

import server

INDEX = b"<!doctype html><html><body><h1>Hi</h1></body></html>"


@pytest.fixture
def site(tmp_path, monkeypatch):
    """A throwaway site directory that the server serves instead of the real one."""
    root = tmp_path / "site"
    root.mkdir()
    (root / "index.html").write_bytes(INDEX)
    (root / "bare.html").write_bytes(b"<p>no body tag</p>")
    (root / "style.css").write_bytes(b"body { color: red; }")
    (root / "sub").mkdir()
    (root / "sub" / "index.html").write_bytes(b"<body>sub</body>")
    monkeypatch.setattr(server, "ROOT", root)
    monkeypatch.setattr(server, "POLL_SECONDS", 0.02)
    return root


@pytest.fixture
def live(site):
    """The server running on a free port; yields (host, port)."""
    httpd = server.make_server(0)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield "127.0.0.1", httpd.server_port
    httpd.shutdown()
    httpd.server_close()
    thread.join(timeout=5)


def get(live, path):
    conn = http.client.HTTPConnection(*live, timeout=5)
    conn.request("GET", path)
    response = conn.getresponse()
    body = response.read()
    conn.close()
    return response, body


def open_stream(live):
    """Connect to the live-reload stream and return the socket's file once headers are read."""
    sock = socket.create_connection(live, timeout=5)
    sock.sendall(b"GET /__livereload HTTP/1.1\r\nHost: test\r\n\r\n")
    stream = sock.makefile("rb")
    headers = []
    while (line := stream.readline()) not in (b"\r\n", b""):
        headers.append(line.decode().strip())
    return sock, stream, headers


# ---------- site_fingerprint ----------

def test_fingerprint_counts_files_and_tracks_newest_change(site):
    newest, count = server.site_fingerprint()
    assert count == 4
    future = time.time() + 100
    os.utime(site / "style.css", (future, future))
    assert server.site_fingerprint() == (future, 4)


def test_fingerprint_changes_when_a_file_is_added_or_removed(site):
    before = server.site_fingerprint()
    (site / "new.js").write_text("1")
    added = server.site_fingerprint()
    assert added[1] == before[1] + 1
    (site / "new.js").unlink()
    assert server.site_fingerprint()[1] == before[1]


def test_fingerprint_skips_files_that_vanish_mid_scan(site, monkeypatch):
    real_stat = os.stat

    def flaky_stat(path, *args, **kwargs):
        if str(path).endswith("style.css"):
            raise FileNotFoundError(path)
        return real_stat(path, *args, **kwargs)

    monkeypatch.setattr(server.os, "stat", flaky_stat)
    assert server.site_fingerprint()[1] == 3


def test_fingerprint_of_missing_directory_is_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "ROOT", tmp_path / "nowhere")
    assert server.site_fingerprint() == (0.0, 0)


# ---------- serving pages ----------

def test_index_gets_the_reload_snippet_just_before_body_end(live):
    response, body = get(live, "/")
    assert response.status == 200
    assert response.getheader("Content-Type") == "text/html; charset=utf-8"
    assert response.getheader("Content-Length") == str(len(body))
    assert body == INDEX.replace(b"</body>", server.LIVERELOAD_SNIPPET + b"</body>")


def test_html_without_body_tag_gets_the_snippet_appended(live):
    _, body = get(live, "/bare.html")
    assert body == b"<p>no body tag</p>" + server.LIVERELOAD_SNIPPET


def test_directory_request_serves_its_index_page(live):
    _, body = get(live, "/sub/")
    assert body.startswith(b"<body>sub") and b"EventSource" in body


def test_other_files_are_served_untouched(live):
    response, body = get(live, "/style.css")
    assert response.status == 200
    assert body == b"body { color: red; }"


def test_nothing_is_cached(live):
    for path in ("/", "/style.css", "/missing.html"):
        response, _ = get(live, path)
        assert response.getheader("Cache-Control") == "no-store"


def test_missing_page_is_404(live):
    response, _ = get(live, "/missing.html")
    assert response.status == 404


def test_the_page_on_disk_is_never_modified(live, site):
    get(live, "/")
    assert (site / "index.html").read_bytes() == INDEX


# ---------- live reload stream ----------

def test_stream_sends_reload_when_a_file_changes(live, site, monkeypatch):
    monkeypatch.setattr(server, "PING_EVERY", 10_000)
    sock, stream, headers = open_stream(live)
    assert "Content-Type: text/event-stream" in headers
    time.sleep(0.1)
    (site / "index.html").write_bytes(INDEX + b"<!-- edited -->")
    future = time.time() + 50
    os.utime(site / "index.html", (future, future))
    assert stream.readline() == b"event: reload\n"
    assert stream.readline() == b"data: changed\n"
    sock.close()


def test_stream_sends_keep_alive_pings(live, monkeypatch):
    monkeypatch.setattr(server, "PING_EVERY", 1)
    sock, stream, _ = open_stream(live)
    assert stream.readline() == b": ping\n"
    sock.close()


def test_stream_ends_quietly_when_the_browser_goes_away(live, monkeypatch):
    monkeypatch.setattr(server, "PING_EVERY", 1)
    finished = threading.Event()
    original = server.Handler.stream_reload_events

    def watched(self):
        original(self)
        finished.set()

    monkeypatch.setattr(server.Handler, "stream_reload_events", watched)
    sock, stream, _ = open_stream(live)
    stream.readline()
    stream.close()
    sock.close()
    assert finished.wait(timeout=5), "stream handler did not stop after the client disconnected"


# ---------- logging ----------

def test_page_requests_are_logged_but_stream_requests_are_not(live, capfd, monkeypatch):
    monkeypatch.setattr(server, "PING_EVERY", 1)
    get(live, "/style.css")
    sock, stream, _ = open_stream(live)
    stream.readline()
    sock.close()
    time.sleep(0.1)
    logged = capfd.readouterr().err
    assert "GET /style.css" in logged
    assert "__livereload" not in logged


def test_log_message_without_arguments_still_logs(site, capfd):
    handler = server.Handler.__new__(server.Handler)
    handler.client_address = ("127.0.0.1", 1)
    handler.log_message("plain message")
    assert "plain message" in capfd.readouterr().err


# ---------- start-up ----------

def test_make_server_uses_daemon_threads(site):
    httpd = server.make_server(0)
    try:
        assert httpd.daemon_threads is True
        assert httpd.server_address[0] == "127.0.0.1"
    finally:
        httpd.server_close()


@pytest.fixture
def interrupted(monkeypatch):
    """Make serve_forever stop immediately, as if the user pressed Ctrl-C."""
    def serve_forever(self, *args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(ThreadingHTTPServer, "serve_forever", serve_forever)


def test_main_creates_the_site_folder_and_announces_the_address(tmp_path, monkeypatch, capsys, interrupted):
    root = tmp_path / "fresh-site"
    monkeypatch.setattr(server, "ROOT", root)
    server.main(["0"])
    assert root.is_dir()
    assert "Cyber Kitchen serving" in capsys.readouterr().out


def test_main_falls_back_to_the_default_port(site, monkeypatch, capsys, interrupted):
    monkeypatch.setattr(server, "DEFAULT_PORT", 0)
    monkeypatch.setattr(sys, "argv", ["server.py"])
    server.main()
    assert "http://localhost:" in capsys.readouterr().out


def test_running_the_file_as_a_script_starts_the_server(monkeypatch, capsys, interrupted):
    monkeypatch.setattr(sys, "argv", ["server.py", "0"])
    runpy.run_path(server.__file__, run_name="__main__")
    assert "Cyber Kitchen serving" in capsys.readouterr().out
