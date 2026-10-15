"""js/metrics.js: the pieces every metrics card is built from."""
from tests.support import run, spec


def test_percent_rounds_a_share(page):
    assert page.evaluate("[0, 0.004, 0.5, 0.996, 1.2].map(percent)") == ["0%", "0%", "50%", "100%", "120%"]


def test_at_most_has_three_grades(page):
    assert page.evaluate("[10, 12, 13].map(v => atMost(v, 10))") == [["On target", "good"], ["A little over target", "warn"], ["Over target", "bad"]]


def test_at_least_has_three_grades(page):
    assert page.evaluate("[0.8, 0.7, 0.5].map(v => atLeast(v, 0.8))") == [["On target", "good"], ["A little under target", "warn"], ["Under target", "bad"]]


def test_trend_compares_the_latest_slice_with_the_average(page):
    said = page.evaluate("[[undefined, 0.5], [0.5, 0.5], [0.9, 0.5], [0.1, 0.5]].map(([latest, average]) => trend(latest, average, percent))")
    assert said[0] == "No full 15-second slice yet."
    assert said[1].endswith("the same as its average so far.") and said[2].endswith("above its average so far.") and said[3].endswith("below its average so far.")
    assert said[2].startswith("Latest 15 seconds: 90%")


def test_use_metrics_for_a_resource_that_should_stay_under_a_limit(page):
    run(page, 120)
    card = spec(page, "DES_RES.cooks.info")
    assert card["unit"] == "of the time so far" and card["notes"][0] == "Target: at most 85%."
    assert card["verdict"][0] in ("Within the limit", "Over the limit")
    assert card["chartTitle"] == "Use every 15 seconds" and card["timelineTitle"] == "Use on the clock"
    assert card["chart"] == card["timeline"] == "svg" and card["chartMarks"] == 8


def test_use_metrics_for_a_resource_that_should_be_used(page):
    run(page, 120)
    card = spec(page, "DES_RES.tables.info")
    assert card["notes"][0] == "Target: at least 70%." and card["verdict"][1] in ("good", "warn", "bad")


def test_both_verdicts_of_a_limit(page):
    run(page, 10)
    verdicts = page.evaluate("[0.2, 0.9].map(share => useMetrics({ sum: share * clock, history: [share], changes: [] }, 0.8, { lowIsFine: true }).verdict)")
    assert verdicts == [["Within the limit", "good"], ["Over the limit", "bad"]]


def test_before_the_clock_starts_the_average_is_zero(page):
    assert page.evaluate("useMetrics({ sum: 0, history: [], changes: [] }, 0.8, { lowIsFine: true }).value") == "0%"


def test_metrics_for_asks_the_object_itself(page):
    assert page.evaluate("metricsFor({ metrics: () => 'mine' })") == "mine"
