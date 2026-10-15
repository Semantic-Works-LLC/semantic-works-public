"""js/charts.js: the bar charts, and the charts on the clock that share one sliding time axis."""
from tests.support import run


def test_now_is_at_the_same_place_in_every_chart(page):
    run(page, 100)
    assert page.evaluate("[timeX(clock), NOW_X, timeX(clock - WINDOW)].map(Math.round)") == [252, 252, 0]


def test_a_time_chart_has_a_track_gridlines_every_thirty_seconds_and_a_now_line(page):
    run(page, 100)
    chart = page.evaluate("""() => { const svg = timeChart(36, () => {});
        return { box: svg.getAttribute('viewBox'), labels: [...svg.querySelectorAll('text')].map(t => t.textContent), track: svg.querySelector('.chart-track').getAttribute('height') }; }""")
    assert chart["box"] == "0 0 300 66" and chart["track"] == "36"
    assert chart["labels"] == ["0:00", "0:30", "1:00", "1:30", "2:00", "now"]


def test_spans_are_clipped_to_the_window_and_to_now(page):
    run(page, 300)
    widths = page.evaluate("""() => { const svg = timeChart(36, span => { span(0, 10, 0, 5, 'red'); span(200, 230, 0, 5, 'red'); span(280, null, 0, 5, 'red'); span(100, 500, 0, 5, 'red'); });
        return [...svg.querySelectorAll('rect[fill=red]')].map(r => [Math.round(r.getAttribute('x')), Math.round(r.getAttribute('width'))]); }""")
    assert widths == [[112, 42], [224, 28], [0, 252]], "the span that ended before the window is not drawn; an open one runs to now"


def test_a_reading_timeline_is_as_tall_as_the_reading(page):
    run(page, 60)
    bars = page.evaluate("""() => { const svg = readingTimeline({ changes: [[0, 0], [10, 2], [20, 1], [30, 0], [40, 2]] });
        return [...svg.querySelectorAll('rect:not(.chart-track)')].map(r => Math.round(r.getAttribute('height'))); }""")
    assert bars == [36, 18, 36]


def test_stays_are_stacked_when_they_overlap_and_coloured_by_the_target(page):
    run(page, 100)
    bars = page.evaluate("""() => { const svg = staysTimeline([{ start: 10, end: 30 }, { start: 20, end: 25 }, { start: 40, end: 90 }, { start: 95, end: null }], 15);
        return [...svg.querySelectorAll('rect:not(.chart-track)')].map(r => [r.getAttribute('y'), r.getAttribute('fill')]); }""")
    assert [y for y, _ in bars] == ["14", "21", "14", "14"]
    assert [fill for _, fill in bars] == ["var(--waiting)", "var(--eating)", "var(--waiting)", "var(--eating)"]


def test_stays_without_a_target_are_grey_and_more_than_nine_share_the_last_row(page):
    run(page, 100)
    rows = page.evaluate("""() => { const svg = staysTimeline(Array.from({ length: 12 }, () => ({ start: 50, end: 80 })), 0);
        return [...svg.querySelectorAll('rect:not(.chart-track)')].map(r => [Number(r.getAttribute('y')), r.getAttribute('fill')]); }""")
    assert len({y for y, _ in rows}) == 9 and {fill for _, fill in rows} == {"#8d949b"}


def test_parts_timeline_lays_the_parts_end_to_end(page):
    run(page, 100)
    parts = page.evaluate("""() => { const svg = partsTimeline(40, [[10, 'a'], [0, 'b'], [20, 'c']]);
        return [...svg.querySelectorAll('rect:not(.chart-track)')].map(r => [r.getAttribute('fill'), Math.round(r.getAttribute('width'))]); }""")
    assert parts == [["a", 14], ["c", 28]]


def test_a_bar_chart_with_no_values_says_so(page):
    assert page.evaluate("barChart([], 10, () => true, String).textContent") == "No history yet."


def test_bars_are_green_or_red_against_a_target_with_a_dashed_line(page):
    chart = page.evaluate("""() => { const svg = barChart([5, 15], 10, v => v <= 10, v => v + 's');
        return { fills: [...svg.querySelectorAll('rect')].map(r => r.getAttribute('fill')), dashed: svg.querySelectorAll('path[stroke-dasharray]').length, label: svg.querySelector('text').textContent }; }""")
    assert chart == {"fills": ["var(--eating)", "var(--waiting)"], "dashed": 1, "label": "10s"}


def test_bars_without_a_target_are_grey_and_have_no_line(page):
    chart = page.evaluate("(() => { const svg = barChart([1, 2, 3], 0, () => true, String); return [[...svg.querySelectorAll('rect')].map(r => r.getAttribute('fill')), svg.querySelectorAll('path[stroke-dasharray]').length]; })()")
    assert chart == [["#8d949b"] * 3, 0]


def test_a_row_chart_marks_the_average_and_the_target(page):
    chart = page.evaluate("""() => { const svg = rowChart([{ label: 'For a table', value: 20, average: 10, target: 30 }, { label: 'To order', value: 40, average: 0, target: 15 }, { label: 'Other', value: 5, average: 0 }]);
        return { box: svg.getAttribute('viewBox'), texts: [...svg.querySelectorAll('text')].map(t => t.textContent),
                 fills: [...svg.querySelectorAll('rect:not(.chart-track)')].map(r => r.getAttribute('fill')), marks: svg.querySelectorAll('path').length }; }""")
    assert chart["box"] == "0 0 300 78" and chart["texts"] == ["For a table", "0:20", "To order", "0:40", "Other", "0:05"]
    assert chart["fills"] == ["var(--eating)", "var(--waiting)", "#8d949b"] and chart["marks"] == 3
