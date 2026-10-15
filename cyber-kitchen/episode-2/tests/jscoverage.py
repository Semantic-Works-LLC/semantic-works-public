"""Line coverage for the JavaScript inside site/index.html.

Chromium's profiler reports, per script, which character ranges ran. Each test page
hands its report to JsCoverage.add(); the ranges are merged across all tests and
turned into a per-line report against the lines of index.html.
"""
import html
import re
from pathlib import Path

COMMENT = re.compile(r"(^|\s)//.*$")
BANNER = re.compile(r"// ===== js/([\w.-]+) =====$")   # written by build.py in front of each module


class JsCoverage:
    def __init__(self, html_path):
        self.html_path = Path(html_path)
        text = self.html_path.read_text(encoding="utf-8")
        start = text.index("<script>") + len("<script>")
        end = text.index("</script>", start)
        self.source = text[start:end]
        # Profiler offsets count UTF-16 units; they equal Python indexes only without astral characters.
        assert all(ord(ch) < 0x10000 for ch in self.source), "script contains characters outside the BMP"
        self.first_line = text[:start].count("\n") + 1
        self.covered = bytearray(len(self.source))
        self.pages = 0

    def add(self, script_coverage):
        """Merge one page's coverage entry (from Profiler.takePreciseCoverage) for this script."""
        ranges = [(r["startOffset"], r["endOffset"], r["count"])
                  for function in script_coverage["functions"] for r in function["ranges"]]
        ranges.sort(key=lambda r: (r[0], -r[1]))   # outer ranges first, so inner ones override them
        ran = bytearray(len(self.source))
        for start, end, count in ranges:
            ran[start:end] = (b"\x01" if count else b"\x00") * (end - start)
        self.covered = bytearray(a | b for a, b in zip(self.covered, ran))
        self.pages += 1

    def lines(self):
        """Yield (line number in index.html, text, status) for every line that holds code."""
        offset = 0
        for index, line in enumerate(self.source.split("\n")):
            code = COMMENT.sub("", line)
            marks = [self.covered[offset + i] for i, ch in enumerate(code) if not ch.isspace()]
            offset += len(line) + 1
            if marks:
                status = "covered" if all(marks) else "partial" if any(marks) else "missed"
                yield self.first_line + index, line, status

    def modules(self):
        """Coverage per inlined module: {file name: [covered lines, lines]}, in page order."""
        starts = [(self.first_line + index, match.group(1))
                  for index, line in enumerate(self.source.split("\n")) if (match := BANNER.match(line))]
        result = {}
        for number, _, status in self.lines():
            name = next((name for start, name in reversed(starts) if start <= number), "(before the first module)")
            counts = result.setdefault(name, [0, 0])
            counts[0] += status == "covered"
            counts[1] += 1
        return result

    def summary(self):
        lines = list(self.lines())
        covered = sum(1 for _, _, status in lines if status == "covered")
        return {
            "lines": len(lines),
            "covered": covered,
            "percent": 100.0 * covered / len(lines) if lines else 100.0,
            "modules": self.modules(),
            "missing": [(number, text.strip(), status) for number, text, status in lines if status != "covered"],
        }

    def write_report(self, directory):
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        result = self.summary()
        head = (f"JavaScript line coverage of {self.html_path.name}: "
                f"{result['covered']}/{result['lines']} lines = {result['percent']:.1f}%")
        text = [head, ""]
        text += [f"{number:5d}  {status:7s}  {line}" for number, line, status in result["missing"]] or ["No missing lines."]
        (directory / "js-coverage.txt").write_text("\n".join(text) + "\n", encoding="utf-8")

        colors = {"covered": "#e6f4e6", "partial": "#fff3c4", "missed": "#fbd5d5"}
        status_by_line = {number: status for number, _, status in self.lines()}
        rows = []
        for index, line in enumerate(self.source.split("\n")):
            number = self.first_line + index
            color = colors.get(status_by_line.get(number), "transparent")
            rows.append(f'<div style="background:{color}"><span class="n">{number}</span>{html.escape(line) or " "}</div>')
        (directory / "js-coverage.html").write_text(
            "<!doctype html><meta charset='utf-8'><title>JavaScript coverage</title>"
            "<style>body{font:13px/1.5 ui-monospace,Menlo,monospace;margin:16px;color:#111;background:#fff}"
            "div{white-space:pre}.n{display:inline-block;width:5ch;color:#888;margin-right:2ch;text-align:right}"
            "h1{font:600 16px system-ui}</style>"
            f"<h1>{html.escape(head)}</h1><p style='font-family:system-ui'>Green ran, yellow partly ran, red never ran.</p>"
            + "".join(rows), encoding="utf-8")
        return result
