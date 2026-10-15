"""js/prefs.js: the page comes back the way it was left."""
from tests.conftest import open_page

KEY = "cyber-kitchen.ui"
STATE = """({ paused, speed, view, panel: $('panel').classList.contains('open'), folds: { ...folds }, tab: detailsTab,
              button: $('pause').title, speedLabel: $('speed-label').textContent, name: $('view-name').textContent })"""


def test_a_first_visit_starts_running_at_one_times_on_the_floor_plan_with_everything_folded(page):
    assert page.evaluate(STATE) == {"paused": False, "speed": 1, "view": "des", "panel": False, "folds": {"selection": False, "events": False, "legend": False},
                                    "tab": "about", "button": "Pause", "speedLabel": "1×", "name": "Floor Plan"}


def test_whatever_is_changed_is_kept_at_once(page):
    page.click("#pause")
    page.evaluate("setSpeed(4); setView('graph'); setPanel(true); setFold('legend', true); setTab('metrics')")
    assert page.evaluate(f"JSON.parse(localStorage.getItem('{KEY}'))") == {"speed": 4, "view": "graph", "folds": {"selection": False, "events": False, "legend": True},
                                                                           "tab": "metrics", "panel": True, "paused": True}


def test_a_page_left_paused_comes_back_paused(page):
    page.click("#pause")
    page.reload()
    assert page.evaluate("[paused, $('pause').title, $('icon-play').hasAttribute('hidden'), $('pause').getAttribute('aria-pressed')]") == [True, "Resume", False, "true"]
    page.evaluate("__frame(performance.now()); __frame(__advance(500))")
    assert page.evaluate("clock") == 0, "and the clock does not move"
    page.click("#pause")
    page.reload()
    assert page.evaluate("paused") is False


def test_the_whole_state_of_the_buttons_and_the_panel_comes_back(page):
    page.click("#pause")
    page.evaluate("setSpeed(8); setView('score'); setPanel(true); setFold('events', true); setFold('legend', true); setTab('actions'); history.replaceState(null, '', location.pathname)")
    page.reload()
    assert page.evaluate(STATE) == {"paused": True, "speed": 8, "view": "score", "panel": True, "folds": {"selection": False, "events": True, "legend": True},
                                    "tab": "actions", "button": "Resume", "speedLabel": "8×", "name": "Scorecard"}
    assert page.evaluate("[...document.querySelectorAll('.fold-body')].map(body => body.hidden)") == [True, False, False]
    assert page.evaluate("$('legend').children.length") == 1, "the legend of the remembered view is drawn"


def test_an_address_that_names_a_view_wins_over_the_remembered_one(page, browser, site_server):
    page.evaluate("setView('score')")
    page.goto(site_server[0] + "#graph")
    page.reload()   # going to the same page with another # does not load it again by itself
    assert page.evaluate("view") == "graph"


def test_the_simulation_itself_starts_again(page):
    page.evaluate("for (let i = 0; i < 2000; i++) tick(0.05)")
    page.reload()
    assert page.evaluate("[clock, desEngine.eventsProcessed, selected]") == [0, 0, None]


def test_nonsense_in_storage_is_ignored(page):
    for stored in ["not json", '{"speed": 3, "view": "nowhere", "tab": "objectives", "folds": {"legend": "yes"}, "panel": "open", "paused": 1}', "null", '{"folds": null}']:
        page.evaluate("stored => localStorage.setItem('cyber-kitchen.ui', stored)", stored)
        page.reload()
        assert page.evaluate(STATE)["speed"] == 1 and page.evaluate(STATE)["view"] == "des" and page.evaluate(STATE)["tab"] == "about", stored
        assert page.evaluate("[paused, $('panel').classList.contains('open'), folds.legend]") == [False, False, False], stored


def test_the_page_works_with_storage_switched_off(browser, site_server):
    page, finish = open_page(browser, site_server[0], init_script="Object.defineProperty(window, 'localStorage', { get() { throw new Error('storage is off'); } });")
    page.click("#pause")
    page.evaluate("setSpeed(2); setPanel(true)")
    assert page.evaluate("[paused, speed, prefs.paused, prefs.speed]") == [True, 2, True, 2], "it is still remembered for as long as the page is open"
    finish()
