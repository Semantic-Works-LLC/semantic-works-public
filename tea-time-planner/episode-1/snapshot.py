"""Save numbered screenshots of the app's views into screenshots/.

Run by server.py whenever the page's files settle after a change; can also be run by hand:
    python3 snapshot.py            # shoot every view, keep the ones that changed
    python3 snapshot.py --index    # just rebuild timeline.md and index.html

Files are numbered 001, 002, ... in the order they were taken. screenshots/timeline.json
is the record; timeline.md and index.html are generated from it. Times are relative to
the first prompt of the session (T0), so they line up with transcript.md.
"""
import hashlib
import html
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "screenshots")
TIMELINE = os.path.join(OUT, "timeline.json")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
URL = "http://localhost:8000/"
VIEWS = ["table", "food", "drinks", "plan"]
SIZE = "1400,850"


def load():
    with open(TIMELINE) as f:
        return json.load(f)


def save(tl):
    with open(TIMELINE, "w") as f:
        json.dump(tl, f, indent=1, ensure_ascii=False)


def rel(t, t0):
    s = max(0, int(t - t0))
    return f"T+{s // 3600}:{s // 60 % 60:02d}:{s % 60:02d}"


def file_hash(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def shoot(url, path, profile):
    subprocess.run(
        [CHROME, "--headless=new", "--hide-scrollbars", "--disable-gpu-sandbox",
         "--use-angle=swiftshader", "--enable-unsafe-swiftshader",
         f"--window-size={SIZE}", "--virtual-time-budget=6000",
         f"--user-data-dir={profile}", f"--screenshot={path}", url],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=90)


def write_index(tl):
    t0, shots = tl["t0"], tl["shots"]
    lines = ["# Screenshot timeline", "",
             "Times are relative to the first prompt (T+0:00:00), matching TRANSCRIPT.md.", "",
             "| # | Time | View | What | File |", "|---|---|---|---|---|"]
    for s in shots:
        lines.append(f"| {s['n']} | {rel(s['t'], t0)} | {s['view']} | {s.get('note', '')} | [{s['file']}]({s['file']}) |")
    with open(os.path.join(OUT, "timeline.md"), "w") as f:
        f.write("\n".join(lines) + "\n")

    cards = "".join(
        f'<a href="{s["file"]}"><img src="{s["file"]}" loading="lazy" alt="{s["view"]}">'
        f'<span><b>#{s["n"]}</b> {rel(s["t"], t0)} · {html.escape(s["view"])}</span>'
        f'<small>{html.escape(s.get("note", ""))}</small></a>'
        for s in reversed(shots))
    page = f"""<!doctype html><html><head><meta charset="utf-8"><title>Tea Time snapshots</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{{margin:0;padding:20px;font-family:-apple-system,sans-serif;background:#f8f0e2;color:#3a2e25}}
h1{{margin:0 0 4px}} p{{margin:0 0 16px;color:#8a7a6a}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px}}
.grid a{{display:flex;flex-direction:column;gap:3px;color:#3a2e25;text-decoration:none;font-size:.85rem}}
.grid img{{width:100%;border:1px solid #e8dccb;border-radius:8px;background:#fff}}
.grid small{{color:#8a7a6a}}
</style></head><body><h1>Tea Time: how the app looked</h1>
<p>Newest first. Times are from the first prompt (T+0:00:00), as in TRANSCRIPT.md.</p>
<div class="grid">{cards}</div></body></html>"""
    with open(os.path.join(OUT, "index.html"), "w") as f:
        f.write(page)


def snapshot():
    tl = load()
    last = {}
    for s in tl["shots"]:
        last[s["view"]] = s.get("hash")
    with tempfile.TemporaryDirectory() as tmp:
        procs = []
        for v in VIEWS:
            # each view gets a fresh browser profile, so it shows the default panel state
            procs.append((v, subprocess.Popen(
                [sys.executable, __file__, "--one", v, os.path.join(tmp, v + ".png"), os.path.join(tmp, "p-" + v)])))
        taken = time.time()
        for v, p in procs:
            p.wait()
        added = []
        for v, _ in procs:
            src = os.path.join(tmp, v + ".png")
            if not os.path.exists(src):
                continue
            h = file_hash(src)
            if h == last.get(v):
                continue  # this view looks exactly as before
            n = max((s["n"] for s in tl["shots"]), default=0) + 1   # numbers continue even after old shots are pruned
            name = f"{n:03d}-{v}.jpg"   # kept as JPEG: a tenth of the size of the PNG
            subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "82", src, "--out", os.path.join(OUT, name)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            tl["shots"].append({"n": n, "file": name, "t": taken, "view": v, "note": "auto, after page change", "hash": h})
            added.append(name)
    save(tl)
    write_index(tl)
    if added:
        print("screenshots saved:", ", ".join(added))


if __name__ == "__main__":
    if len(sys.argv) == 5 and sys.argv[1] == "--one":
        shoot(URL + "#" + sys.argv[2], sys.argv[3], sys.argv[4])
    elif "--index" in sys.argv:
        write_index(load())
    else:
        snapshot()
