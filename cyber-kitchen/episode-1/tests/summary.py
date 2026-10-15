"""Print a short, readable summary of the last `make test` run."""
import json
from pathlib import Path

COVERAGE = Path(__file__).resolve().parent.parent / "coverage"


def main():
    run = json.loads((COVERAGE / "summary.json").read_text())
    python = json.loads((COVERAGE / "python.json").read_text())["totals"]
    suites = [
        ("Python server tests", run["tests"].get("test_server.py"),
         f"server.py {python['percent_covered']:.0f}%  "
         f"({python['covered_lines']}/{python['num_statements']} statements, "
         f"{python['covered_branches']}/{python['num_branches']} branches)"),
        ("Browser tests (JavaScript and UI)", run["tests"].get("test_page.py"),
         f"index.html script {run['js']['percent']:.0f}%  ({run['js']['covered']}/{run['js']['lines']} lines)"),
    ]
    total = failed = 0
    print()
    print("=" * 78)
    print("SUMMARY")
    print("=" * 78)
    for title, counts, coverage in suites:
        counts = counts or {"passed": 0, "failed": 0}
        total += counts["passed"] + counts["failed"]
        failed += counts["failed"]
        print(f"{title}")
        print(f"    tests:     {counts['passed']} passed, {counts['failed']} failed")
        print(f"    coverage:  {coverage}")
    shots = run["screenshots"]
    changed = [name for name, state in shots if state == "CHANGED"]
    new = [name for name, state in shots if state == "new"]
    print("UI screenshots (tests/screenshots)")
    print(f"    {len(shots)} written: {len(shots) - len(changed) - len(new)} unchanged, {len(changed)} changed, {len(new)} new")
    for name in changed:
        print(f"    changed: {name}")
    print("-" * 78)
    print(f"TOTAL: {total} tests, {total - failed} passed, {failed} failed")
    print("Reports: coverage/python/index.html and coverage/js-coverage.html")
    print("=" * 78)


if __name__ == "__main__":
    main()
