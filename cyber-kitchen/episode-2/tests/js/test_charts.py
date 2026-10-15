"""js/charts.js: the two kinds of chart on a metrics card."""
import pytest

RECTS = "(svg => [...svg.querySelectorAll('rect:not(.chart-track)')].map(r => ['x', 'y', 'width', 'height', 'fill'].map(a => isNaN(r.getAttribute(a)) ? r.getAttribute(a) : Number(r.getAttribute(a)))))"


def test_all_time_charts_share_one_axis_with_now_in_the_same_place(page):
    page.evaluate("clock = 400")
    assert page.evaluate("[NOW_X, WINDOW, timeX(400)]") == [252, 180, 252]
    assert page.evaluate("timeX(400 - WINDOW)") == pytest.approx(0, abs=1e-9)
    assert page.evaluate("timeX(310)") == pytest.approx(252 - 90 * 1.4)


def test_a_time_chart_has_clock_marks_every_thirty_seconds_and_a_yellow_now_line(page):
    page.evaluate("clock = 400")
    chart = page.evaluate("""(() => { const svg = timeChart(40, () => {}); return {
        box: svg.getAttribute('viewBox'), labels: [...svg.querySelectorAll('text')].map(t => t.textContent),
        now: [...svg.querySelectorAll('path')].at(-1).getAttribute('stroke'), nowAt: [...svg.querySelectorAll('path')].at(-1).getAttribute('d') }; })()""")
    assert chart["box"] == "0 0 300 70"
    assert chart["labels"] == ["4:00", "4:30", "5:00", "5:30", "6:00", "6:30", "7:00", "now"]
    assert chart["now"] == "var(--menu)" and chart["nowAt"].startswith("M252 ")


def test_early_in_the_service_the_clock_marks_start_at_zero(page):
    page.evaluate("clock = 20")
    assert page.evaluate("[...timeChart(40, () => {}).querySelectorAll('text')].map(t => t.textContent)") == ["0:00", "0:30", "now"]


def test_spans_are_clipped_to_the_window_and_never_pass_now(page):
    page.evaluate("clock = 400")
    rects = page.evaluate(f"{RECTS}(timeChart(40, span => {{ span(100, 310, 0, 5, 'red'); span(390, null, 5, 5, 'blue'); span(399.9, 400, 0, 5, 'green'); span(50, 100, 0, 5, 'grey'); span(410, 420, 0, 5, 'grey'); }}))")
    assert rects[0] == [0, 12, pytest.approx(126), 5, "red"]            # started before the window: cut at the left edge
    assert rects[1] == [pytest.approx(238), 17, pytest.approx(14), 5, "blue"]   # still going: drawn up to now
    assert rects[2][2] == 1 and len(rects) == 3                          # a tiny span is still one unit wide; out-of-window spans are dropped


def test_a_reading_is_drawn_as_a_strip_that_is_filled_while_it_is_on(page):
    page.evaluate("clock = 400")
    rects = page.evaluate(f"{RECTS}(readingTimeline({{ changes: [[300, 1], [330, 0], [380, 1]] }}))")
    assert [(round(r[0]), round(r[2]), r[3], r[4]) for r in rects] == [(112, 42, 36, "#3987e5"), (224, 28, 36, "#3987e5")]


def test_a_queue_length_is_drawn_as_tall_as_the_queue_is_long(page):
    page.evaluate("clock = 400")
    rects = page.evaluate(f"{RECTS}(readingTimeline({{ changes: [[300, 1], [330, 4], [360, 2]] }}))")
    assert [r[3] for r in rects] == [9, 36, 18] and [r[1] for r in rects] == [39, 12, 30]
    assert page.evaluate(f"{RECTS}(readingTimeline({{ changes: [] }}))") == []


def test_stays_are_thin_bars_stacked_when_they_overlap_and_coloured_by_target(page):
    page.evaluate("clock = 400")
    stays = "[{ start: 300, end: 310 }, { start: 305, end: 345 }, { start: 320, end: 330 }, { start: 390, end: null }]"
    rects = page.evaluate(f"{RECTS}(staysTimeline({stays}, 15))")
    assert [r[1] for r in rects] == [14, 21, 14, 14]   # the second overlaps the first, so it goes on the next row
    assert [r[4] for r in rects] == ["var(--eating)", "var(--waiting)", "var(--eating)", "var(--eating)"]
    assert [r[4] for r in page.evaluate(f"{RECTS}(staysTimeline({stays}, undefined))")] == ["#8d949b"] * 4
    assert page.evaluate(f"staysTimeline({stays}, 15).getAttribute('viewBox')") == "0 0 300 60"   # never fewer than four rows high


def test_more_than_nine_overlapping_stays_share_the_last_row(page):
    page.evaluate("clock = 400")
    rects = page.evaluate(f"{RECTS}(staysTimeline(Array.from({{ length: 12 }}, (_, i) => ({{ start: 300 + i, end: null }})), 15))")
    assert sorted(set(r[1] for r in rects)) == [14 + 7 * row for row in range(9)]
    assert [r[1] for r in rects[8:]] == [70, 70, 70, 70]


def test_parts_are_drawn_end_to_end_and_empty_parts_are_skipped(page):
    page.evaluate("clock = 400")
    rects = page.evaluate(f"{RECTS}(partsTimeline(300, [[20, 'orange'], [0, 'grey'], [30, 'green']]))")
    assert [(round(r[0]), round(r[2]), r[4]) for r in rects] == [(112, 28, "orange"), (140, 42, "green")]


def test_bar_chart_shows_history_against_a_dashed_target_line(page):
    empty = page.evaluate("barChart([], 10, v => v <= 10, clockText).textContent")
    assert empty == "No history yet."
    chart = page.evaluate(f"""(() => {{ const svg = barChart([5, 10, 20], 10, v => v <= 10, clockText); return {{
        fills: {RECTS}(svg).map(r => r[4]), heights: {RECTS}(svg).map(r => r[3]), label: svg.querySelector('text').textContent,
        dashed: [...svg.querySelectorAll('path')].at(-1).getAttribute('stroke-dasharray') }}; }})()""")
    assert chart["fills"] == ["var(--eating)", "var(--eating)", "var(--waiting)"]
    assert chart["heights"][2] == pytest.approx(4 * chart["heights"][0], rel=0.05)
    assert chart["label"] == "0:10" and chart["dashed"] == "5 4"


def test_bar_chart_without_a_target_is_grey_and_has_no_line(page):
    chart = page.evaluate(f"(() => {{ const svg = barChart([5, 7], undefined, () => true, clockText); return [{RECTS}(svg).map(r => r[4]), svg.querySelectorAll('text').length, svg.querySelectorAll('path').length]; }})()")
    assert chart == [["#8d949b", "#8d949b"], 0, 1]


def test_bars_get_narrower_once_there_are_more_than_twenty(page):
    widths = page.evaluate(f"[5, 20, 40].map(n => {RECTS}(barChart(Array(n).fill(1), 2, () => true, percent))[0][2])")
    assert widths == [13, 13, 5.5]


def test_row_chart_has_a_bar_per_part_with_marks_for_average_and_target(page):
    rows = "[{ label: 'On the rail', value: 20, average: 12, target: 15 }, { label: 'To the rail', value: 4, average: 0 }, { label: 'Cooking', value: 10, average: 8, target: 25 }]"
    chart = page.evaluate(f"""(() => {{ const svg = rowChart({rows}); return {{
        box: svg.getAttribute('viewBox'), texts: [...svg.querySelectorAll('text')].map(t => t.textContent),
        fills: {RECTS}(svg).map(r => r[4]), marks: [...svg.querySelectorAll('path')].map(p => p.getAttribute('stroke')) }}; }})()""")
    assert chart["box"] == "0 0 300 78"
    assert chart["texts"] == ["On the rail", "0:20", "To the rail", "0:04", "Cooking", "0:10"]
    assert chart["fills"] == ["var(--waiting)", "#8d949b", "var(--eating)"]   # over target, no target, within target
    assert chart["marks"] == ["var(--ready)", "#fff", "var(--ready)", "#fff"]   # the part with no target and no average has no marks
