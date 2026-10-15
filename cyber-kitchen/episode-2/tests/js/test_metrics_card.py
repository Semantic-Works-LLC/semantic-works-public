"""js/metrics-card.js: the metrics card under the about card."""
import re

from tests.support import click, metrics, run, show_service


def test_no_metrics_card_when_nothing_is_selected_or_the_panel_is_closed(page):
    page.click("#panel-toggle")
    assert metrics(page) is None
    click(page, "tables[0].g")
    assert metrics(page) is not None
    page.click("#panel-close")
    page.evaluate("renderMetrics()")
    assert metrics(page) is None


def test_metrics_card_has_objective_measure_number_verdict_notes_two_charts_and_numbers(page):
    run(page, 60)
    click(page, "tables[0].g")
    shown = metrics(page)
    assert page.locator("#metrics .kind").inner_text().upper() == "METRICS"
    assert shown["Objective"].startswith("To have guests at it") and shown["How it is measured"].startswith("Share of the time")
    assert re.fullmatch(r"\d+%", shown["value"]) and shown["unit"] == "of the time so far"
    assert shown["grade"] in ("good", "warn", "bad") and shown["verdict"]
    assert shown["notes"][0] == "Target: at least 70%." and len(shown["notes"]) == 4   # target, trend, and a caption under each chart
    assert shown["charts"] == 2
    assert list(shown["numbers"]) == ["Parties seated", "Guests seated", "Seats filled, on average"]
    assert "yellow line is now" in shown["notes"][3]


def test_a_card_without_extra_numbers_and_with_an_empty_note(page):
    click(page, "floorObject('Pass table').nodes[0]")
    shown = metrics(page)
    assert shown["notes"][0] == "Target: at most 0:10." and len(shown["notes"]) == 3   # the empty "latest" note is left out
    click(page, "stoves[1].info.nodes[0]")
    assert metrics(page)["numbers"] == {}


def test_the_card_is_refreshed_as_time_passes(page):
    page.evaluate("spawnParty(); nextArrival = 1e9; select(parties[0].table.info); __frame(last + 50)")
    before = metrics(page)["value"]
    run(page, 60)
    assert metrics(page)["value"] == before   # drawing alone does not refresh it
    page.evaluate("__frame(last + 1000)")
    assert metrics(page)["value"] != before


def test_the_same_card_is_shown_from_the_service_view(page):
    show_service(page)
    click(page, "kitchenG.querySelector('.flow-box')")
    assert metrics(page)["Objective"] == "Turn a ticket into food as fast as the kitchen can."
