"""js/views.js: switching between the restaurant floor and the service view."""
from tests.conftest import open_page
from tests.support import card, click, run, show_service


def state(page):
    return page.evaluate("""({ view, floor: !$('view').hasAttribute('hidden'), service: !$('loop').hasAttribute('hidden'),
        iconService: !$('icon-loop').hasAttribute('hidden'), iconFloor: !$('icon-floor').hasAttribute('hidden'),
        label: $('view-toggle').getAttribute('aria-label'), title: $('view-toggle').title, subtitle: $('subtitle').textContent, hash: location.hash })""")


def test_starts_on_the_restaurant_floor(page):
    assert state(page) == {"view": "floor", "floor": True, "service": False, "iconService": True, "iconFloor": False,
                           "label": "Show the service: party states, queues and staff", "title": "Show the service: party states, queues and staff",
                           "subtitle": "Live view of the restaurant floor — simulated", "hash": ""}


def test_the_button_flips_the_view_and_shows_where_the_next_click_goes(page):
    page.click("#view-toggle")
    assert state(page) == {"view": "loop", "floor": False, "service": True, "iconService": False, "iconFloor": True,
                           "label": "Show the restaurant floor", "title": "Show the restaurant floor",
                           "subtitle": "Live view of the service: party states, queues and staff — simulated", "hash": "#loop"}
    page.click("#view-toggle")
    assert state(page)["view"] == "floor" and state(page)["hash"] == "" and state(page)["floor"] is True


def test_both_views_show_the_one_same_legend(page):
    assert page.locator(".legend").count() == 1
    before = page.locator(".legend").inner_text()
    page.click("#view-toggle")
    assert page.locator(".legend").is_visible() and page.locator(".legend").inner_text() == before
    assert "Free table" in before and "Waiter" in before and "Cook" in before


def test_the_page_opens_on_the_service_view_when_the_address_says_so(browser, site_server):
    page, finish = open_page(browser, site_server[0] + "#loop")
    assert state(page)["view"] == "loop" and state(page)["service"] is True
    finish()


def test_the_selection_carries_over_between_views(page):
    click(page, "stoves[0].info.nodes[0]")
    show_service(page)
    assert card(page)["name"] == "Stove 1"
    assert page.evaluate("stoves[0].info.nodes[1].hasAttribute('data-selected')")


def test_the_simulation_runs_the_same_under_either_view(page):
    run(page, 30)
    show_service(page)
    run(page, 30)
    page.click("#view-toggle")
    assert page.evaluate("clock") > 59.9 and page.evaluate("parties.length") > 0


def test_leaving_the_service_view_clears_its_tokens(page):
    run(page, 40)
    show_service(page)
    assert page.locator("#loop-tokens > g").count() == page.evaluate("loopTokens.size") > 4
    page.click("#view-toggle")
    assert page.locator("#loop-tokens > g").count() == 0 and page.evaluate("[loopTokens.size, loopFresh]") == [0, True]
    run(page, 5)
    assert page.locator("#loop-tokens > g").count() == 0   # the hidden view is not drawn
