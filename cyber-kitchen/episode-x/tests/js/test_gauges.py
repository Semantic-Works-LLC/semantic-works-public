"""js/gauges.js: a gauge keeps the average of one reading, over the run and per 15-second slice."""
import pytest

from tests.support import run


def test_a_gauge_averages_its_reading_over_the_run(page):
    page.evaluate("window.probe = gauge(() => clock >= 30)")   # off for the first 30 seconds, then on
    run(page, 60)
    assert page.evaluate("probe.sum / clock") == pytest.approx(0.5, abs=0.01)


def test_a_slice_of_history_is_added_every_fifteen_seconds(page):
    page.evaluate("window.probe = gauge(() => clock >= 30)")
    run(page, 61)
    assert page.evaluate("probe.history.map(v => Math.round(v * 100) / 100)") == [0, 0, 1, 1]


def test_history_keeps_only_the_latest_forty_slices(page):
    page.evaluate("window.probe = gauge(() => 1)")
    run(page, 15 * 45 + 1, dt=0.5)
    assert page.evaluate("[probe.history.length, KEEP]") == [40, 40]


def test_changes_are_remembered_with_their_time_and_trimmed_to_the_window(page):
    page.evaluate("window.probe = gauge(() => Math.floor(clock / 10) % 2)")   # flips every 10 seconds
    run(page, 35)
    changes = page.evaluate("probe.changes")
    assert [value for _, value in changes] == [0, 1, 0, 1] and [round(t / 10) for t, _ in changes] == [0, 1, 2, 3]
    run(page, 400)
    assert page.evaluate("probe.changes[1][0] >= clock - WINDOW && probe.changes.length < 25")


def test_readings_are_taken_as_numbers(page):
    page.evaluate("window.probe = gauge(() => true)")
    run(page, 1)
    assert page.evaluate("[probe.last, Math.round(probe.sum)]") == [1, 1]
