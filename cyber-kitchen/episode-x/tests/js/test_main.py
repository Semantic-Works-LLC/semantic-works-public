"""js/main.js: the clock, the frame loop, and the buttons that are wired up here."""
import pytest

from tests.conftest import open_page
from tests.support import about, click, run


def test_a_tick_moves_the_clock_runs_the_engine_up_to_it_and_samples_the_gauges(page):
    page.evaluate("for (let i = 0; i < 400; i++) tick(0.05)")
    assert page.evaluate("[Math.round(clock), Math.round(desEngine.currentTime), desEngine.eventsProcessed > 2, DES_RES.tables.gauge.history.length]") == [20, 20, True, 1]


def test_draw_draws_only_the_view_on_screen(page):
    run(page, 30)
    assert page.evaluate("[desTokens.size > 0, graphTokens.size, SCORE[2].text.textContent]") == [True, 0, ""]
    page.evaluate("setView('score'); draw()")
    assert page.evaluate("SCORE[2].text.textContent") != ""


def test_a_frame_advances_time_by_the_speed_and_asks_for_the_next_frame(page):
    page.evaluate("__frame(performance.now())")
    start = page.evaluate("clock")
    page.evaluate("__frame(__advance(50))")
    assert page.evaluate("clock") - start == pytest.approx(0.05)
    page.evaluate("setSpeed(4); __frame(__advance(50))")
    assert page.evaluate("clock") - start == pytest.approx(0.25)
    assert page.evaluate("__frame.name") == "frame"


def test_a_long_gap_between_frames_counts_as_a_tenth_of_a_second(page):
    page.evaluate("__frame(performance.now())")
    start = page.evaluate("clock")
    page.evaluate("__frame(__advance(5000))")
    assert page.evaluate("clock") - start == pytest.approx(0.1)


def test_pause_stops_the_clock_and_the_button_shows_what_a_click_will_do(page):
    page.evaluate("__frame(performance.now())")
    page.click("#pause")
    start = page.evaluate("clock")
    page.evaluate("__frame(__advance(50))")
    assert page.evaluate("clock") == start
    assert page.evaluate("[paused, $('pause').title, $('pause').getAttribute('aria-pressed'), $('icon-pause').hasAttribute('hidden'), $('icon-play').hasAttribute('hidden')]") == [True, "Resume", "true", True, False]
    page.click("#pause")
    page.evaluate("__frame(__advance(50))")
    assert page.evaluate("clock") > start and page.evaluate("[$('pause').title, $('icon-play').hasAttribute('hidden')]") == ["Pause", True]


def test_the_panel_is_refreshed_a_few_times_a_second(page):
    run(page, 30)
    page.evaluate("select(DES_RES.tables.info); setTab('metrics'); setFold('events', true); setPicker(true); __frame(__advance(10))")
    before = page.evaluate("[$('metrics').firstChild, $('events').textContent]")
    page.evaluate("for (let i = 0; i < 200; i++) tick(0.05); __frame(__advance(100))")
    assert page.evaluate("$('events').textContent") == before[1], "too soon: the lists are not redrawn on every frame"
    page.evaluate("__frame(__advance(500))")
    assert page.evaluate("$('events').textContent") != before[1]


def test_clicking_empty_space_in_a_view_clears_the_selection(page):
    for view, node in [("des", "desview"), ("graph", "desgraph"), ("score", "scoreview")]:
        page.evaluate(f"setView('{view}'); select(DES_RES.tables.info)")
        click(page, f"$('{node}')")
        assert about(page) is None, view


def test_clicking_elsewhere_or_pressing_escape_closes_the_menus(page):
    for close in ["document.body.click()", "document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))"]:
        for toggle, menu in [("picker-toggle", "picker"), ("view-toggle", "view-menu"), ("speed-toggle", "speed-menu")]:
            page.click(f"#{toggle}")
            assert page.evaluate(f"$('{menu}').hidden") is False
            page.evaluate(close)
            assert page.evaluate(f"$('{menu}').hidden"), (toggle, close)
    page.click("#picker-toggle")
    page.evaluate("document.dispatchEvent(new KeyboardEvent('keydown', { key: 'a' }))")
    assert page.evaluate("$('picker').hidden") is False


def test_clicking_inside_a_menu_keeps_it_open(page):
    page.click("#picker-toggle")
    page.click("#picker-filter")
    page.click("#view-toggle")
    page.evaluate("$('view-menu').click()")
    page.click("#speed-toggle")
    page.evaluate("$('speed-menu').click()")
    assert page.evaluate("[$('view-menu').hidden, $('speed-menu').hidden]") == [True, False]


def test_the_real_loop_runs_by_itself(browser, site_server):
    page, finish = open_page(browser, site_server[0], init_script=None)
    page.wait_for_timeout(400)
    assert page.evaluate("clock") > 0.1 and page.evaluate("desEngine.currentTime") > 0.1
    finish()
