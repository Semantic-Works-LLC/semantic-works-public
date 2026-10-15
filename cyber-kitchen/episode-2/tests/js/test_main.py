"""js/main.js: the clock, the animation loop and the buttons in the header."""
import pytest

from tests.support import click, run


def test_frame_advances_time_and_caps_long_gaps(page):
    page.evaluate("__frame(last + 50)")
    assert page.evaluate("clock") == pytest.approx(0.05)
    page.evaluate("__frame(last + 5000)")
    assert page.evaluate("clock") == pytest.approx(0.15)


def test_pause_button_stops_and_resumes_time(page):
    page.click("#pause")
    assert page.locator("#pause").inner_text() == "Resume"
    assert page.locator("#pause").get_attribute("aria-pressed") == "true"
    page.evaluate("__frame(last + 50)")
    assert page.evaluate("clock") == 0
    page.click("#pause")
    assert page.locator("#pause").inner_text() == "Pause"
    page.evaluate("__frame(last + 50)")
    assert page.evaluate("clock") == pytest.approx(0.05)


def test_speed_buttons_run_time_faster(page):
    assert page.locator(".speed").all_inner_texts() == ["1×", "2×", "4×", "8×", "16×"]
    elapsed = 0
    for times in (4, 2, 8, 16, 1):
        page.click(f".speed[data-speed='{times}']")
        assert page.locator(".speed[aria-pressed='true']").all_inner_texts() == [f"{times}×"]
        page.evaluate("__frame(last + 50)")
        elapsed += 0.05 * times
        assert page.evaluate("clock") == pytest.approx(elapsed)


def test_a_tick_moves_the_clock_and_lets_guests_arrive(page):
    page.evaluate("tick(0.3)")
    assert page.evaluate("[clock, parties.length]") == [0.3, 0]
    page.evaluate("tick(0.3)")
    assert page.evaluate("parties.length") == 1
    assert 5 <= page.evaluate("nextArrival") < 10
    run(page, 60)
    assert page.evaluate("partyCount") >= 6


def test_a_tick_sends_off_staff_who_are_leaving_and_free(page):
    page.evaluate("waiters[1].leaving = true; cooks[0].leaving = true; tick(0.05)")
    assert page.evaluate("[waiters.map(w => w.name), cooks.map(c => c.name)]") == [["Waiter 1"], ["Cook 2"]]


def test_the_page_starts_with_free_tables_an_empty_card_and_a_running_loop(page):
    assert page.evaluate("tables.every(t => t.g.getAttribute('class') === 'table free')")
    assert "Nothing selected" in page.evaluate("$('about').textContent")
    assert page.evaluate("typeof __frame") == "function"


def test_metrics_and_picker_are_refreshed_a_few_times_a_second_not_every_frame(page):
    page.click("#picker-toggle")
    page.evaluate("__frame(last + 1000); spawnParty(); __frame(last + 50)")
    assert page.locator("#picker .actor:text-is('Party 1')").count() == 0
    page.evaluate("__frame(last + 500)")
    assert page.locator("#picker .actor:text-is('Party 1')").count() == 1


def test_clicking_the_floor_background_clears_the_selection(page):
    click(page, "tables[0].g")
    click(page, "$('view')")
    assert page.evaluate("selected") is None
