"""Shared fixtures: a served copy of the site, a headless browser, and JavaScript coverage."""
import json
import os
import shutil
import threading
from pathlib import Path

import pytest

import server
from tests.jscoverage import JsCoverage

PROJECT = Path(__file__).resolve().parent.parent
JS_COVERAGE = JsCoverage(PROJECT / "site" / "index.html")
JS_COVERAGE_MIN = float(os.environ.get("JS_COVERAGE_MIN", "100"))


class SCREENSHOTS:
    """Where UI screenshots are written (one folder per view), and what happened to each one in this run."""
    directory = PROJECT / "tests" / "screenshots"
    results = []


SCREENSHOTS.directory.mkdir(exist_ok=True)

# Runs before the page's own script. It makes the page deterministic. The simulation itself is
# already seeded (the engine has its own random streams), so what is left is time:
# - the animation loop only advances when a test says so (window.__frame holds the next frame);
# - the page's stopwatch, performance.now(), only moves when a test calls window.__advance(ms),
#   so the easing of tokens and the zoom glide come out the same on every run;
# - requestAnimationFrame callbacks that are not the main loop (the zoom glide) are kept in
#   window.__frames, and window.__runFrames() runs them.
INIT_SCRIPT = """
(() => {
  let now = 1000;
  performance.now = () => now;
  window.__advance = ms => { now += ms; return now; };
  window.__frames = [];
  let handle = 0;
  window.requestAnimationFrame = callback => {
    if (callback.name === "frame") window.__frame = callback;   // the page's main loop: a test runs it by hand
    else window.__frames.push([++handle, callback]);
    return ++handle;
  };
  window.cancelAnimationFrame = id => { window.__frames = window.__frames.filter(([one]) => one !== id); };
  window.__runFrames = (ms = 16) => { const due = window.__frames; window.__frames = []; now += ms; for (const [, callback] of due) callback(now); return due.length; };
})();
"""


@pytest.fixture(scope="module")
def site_server(tmp_path_factory):
    """Serve a temporary copy of ./site so tests can edit files without touching the real ones."""
    root = tmp_path_factory.mktemp("served") / "site"
    shutil.copytree(PROJECT / "site", root)
    saved = server.ROOT, server.POLL_SECONDS
    server.ROOT, server.POLL_SECONDS = root, 0.05
    httpd = server.make_server(0)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{httpd.server_port}/", root
    httpd.shutdown()
    httpd.server_close()
    thread.join(timeout=5)
    server.ROOT, server.POLL_SECONDS = saved


@pytest.fixture(scope="module")
def browser():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as playwright:
        # BROWSER_CHANNEL=chrome uses an installed Google Chrome instead of Playwright's Chromium.
        browser = playwright.chromium.launch(channel=os.environ.get("BROWSER_CHANNEL") or None)
        yield browser
        browser.close()


def open_page(browser, url, width=1400, height=900, init_script=INIT_SCRIPT):
    """Open the app with coverage recording on. Returns (page, finish); call finish() when done."""
    context = browser.new_context(viewport={"width": width, "height": height})
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    cdp = context.new_cdp_session(page)
    cdp.send("Debugger.enable")
    cdp.send("Profiler.enable")
    cdp.send("Profiler.startPreciseCoverage", {"callCount": True, "detailed": True})
    if init_script:
        page.add_init_script(init_script)
    page.goto(url)

    def finish():
        for entry in cdp.send("Profiler.takePreciseCoverage")["result"]:
            if entry["url"].startswith(url.split("#")[0]):
                try:
                    source = cdp.send("Debugger.getScriptSource", {"scriptId": entry["scriptId"]})["scriptSource"]
                except Exception:   # the script of a page that has since been reloaded: its text is gone, and what it ran is not counted
                    continue
                if source == JS_COVERAGE.source:
                    JS_COVERAGE.add(entry)
        context.close()
        assert not errors, f"JavaScript errors on the page: {errors}"

    return page, finish


@pytest.fixture
def page(browser, site_server):
    """The app, loaded and frozen at simulated time zero."""
    page, finish = open_page(browser, site_server[0])
    yield page
    finish()


OUTCOMES = {}   # test id -> "passed" or "failed", for the summary printed by `make test`


def pytest_runtest_logreport(report):
    if report.failed or report.nodeid not in OUTCOMES:
        OUTCOMES[report.nodeid] = "failed" if report.failed else "passed"


def write_summary(js):
    tests = {}
    for nodeid, outcome in OUTCOMES.items():
        suite = "server" if Path(nodeid.split("::")[0]).name == "test_server.py" else "browser"
        counts = tests.setdefault(suite, {"passed": 0, "failed": 0})
        counts[outcome] += 1
    (PROJECT / "coverage").mkdir(exist_ok=True)
    (PROJECT / "coverage" / "summary.json").write_text(json.dumps(
        {"tests": tests, "js": js, "screenshots": SCREENSHOTS.results}, indent=2))


def pytest_sessionfinish(session, exitstatus):
    reporter = session.config.pluginmanager.get_plugin("terminalreporter")
    if SCREENSHOTS.results:
        reporter.write_sep("-", "UI screenshots (tests/screenshots)")
        for name, state in SCREENSHOTS.results:
            reporter.write_line(f"  {state:9s} {name}")
    if not JS_COVERAGE.pages:
        return write_summary({"lines": 0, "covered": 0, "percent": 0.0, "modules": {}})
    result = JS_COVERAGE.write_report(PROJECT / "coverage")
    write_summary({key: result[key] for key in ("lines", "covered", "percent", "modules")})
    reporter.write_sep("-", "JavaScript coverage (site/index.html, by module in js/)")
    for name, (covered, lines) in result["modules"].items():
        reporter.write_line(f"  {name:24s} {covered:4d}/{lines:<4d} {100.0 * covered / lines:5.1f}%")
    reporter.write_line(f"{result['covered']}/{result['lines']} lines covered = {result['percent']:.1f}%")
    for number, text, status in result["missing"][:40]:
        reporter.write_line(f"  index.html:{number}  {status}: {text}")
    reporter.write_line("Full report: coverage/js-coverage.html")
    if result["percent"] < JS_COVERAGE_MIN and exitstatus == 0:
        reporter.write_line(f"FAILED: JavaScript coverage is below {JS_COVERAGE_MIN:.0f}%")
        session.exitstatus = 1
