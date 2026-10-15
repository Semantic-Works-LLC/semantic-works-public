"""Print a short, readable summary of the last `make test` run."""
import json
from pathlib import Path

COVERAGE = Path(__file__).resolve().parent.parent / "coverage"


def main():
    run = json.loads((COVERAGE / "summary.json").read_text())
    python = json.loads((COVERAGE / "python.json").read_text())["totals"]
    suites = [
        ("Python server tests", run["tests"].get("server"),
         f"server.py {python['percent_covered']:.0f}%  "
         f"({python['covered_lines']}/{python['num_statements']} statements, "
         f"{python['covered_branches']}/{python['num_branches']} branches)"),
        ("Browser tests (JavaScript and UI)", run["tests"].get("browser"),
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
    for name, (covered, lines) in run["js"]["modules"].items():
        print(f"      js/{name:24s} {100 * covered / lines:4.0f}%  ({covered}/{lines})")
    shots = run["screenshots"]
    changed = [f"{name}  {state[8:]}" for name, state in shots if state.startswith("CHANGED")]
    new = [name for name, state in shots if state == "new"]
    print("UI screenshots (tests/screenshots, one folder per view)")
    print(f"    {len(shots)} taken: {len(shots) - len(changed) - len(new)} match, {len(changed)} do not match, {len(new)} new")
    for name in changed:
        print(f"    does not match: {name}")
    print("-" * 78)
    print(f"TOTAL: {total} tests, {total - failed} passed, {failed} failed")
    print("Reports: coverage/python/index.html and coverage/js-coverage.html")
    print("=" * 78)


if __name__ == "__main__":
    main()
