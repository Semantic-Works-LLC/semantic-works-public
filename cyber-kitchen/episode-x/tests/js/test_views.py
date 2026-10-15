"""js/views.js: the three views of the one engine, and switching between them."""
from tests.conftest import open_page
from tests.support import legend, run, show


def shown(page):
    return page.evaluate("VIEWS.filter(one => !$(one.node).hasAttribute('hidden')).map(one => one.key)")


def test_there_are_three_views_and_the_floor_plan_shows_first(page):
    assert page.evaluate("VIEWS.map(one => [one.key, one.short])") == [["des", "Floor Plan"], ["graph", "Process Map"], ["score", "Scorecard"]]
    assert shown(page) == ["des"] and page.evaluate("view") == "des" and page.locator("#view-name").inner_text() == "Floor Plan"


def test_the_blue_button_in_the_middle_names_the_view_and_opens_the_menu(page):
    style = page.evaluate("(() => { const s = getComputedStyle($('view-toggle')); return [s.backgroundColor, s.color]; })()")
    assert style == ["rgb(37, 99, 235)", "rgb(255, 255, 255)"]
    box, header = page.locator("#view-toggle").bounding_box(), page.locator("main > header").bounding_box()
    assert abs(box["x"] + box["width"] / 2 - (header["x"] + header["width"] / 2)) < 1.5
    page.click("#view-toggle")
    assert page.evaluate("[$('view-menu').hidden, $('view-toggle').getAttribute('aria-expanded')]") == [False, "true"]
    assert page.evaluate("[...$('view-menu').children].map(item => item.textContent)") == ["1Floor Plan", "2Process Map", "3Scorecard"]
    menu = page.locator("#view-menu").bounding_box()
    assert menu["y"] > box["y"] + box["height"] and abs(menu["x"] + menu["width"] / 2 - (box["x"] + box["width"] / 2)) < 1.5


def test_choosing_a_view_shows_only_it_and_closes_the_menu(page):
    page.click("#view-toggle")
    page.click("#view-menu [data-view=graph]")
    assert shown(page) == ["graph"] and page.evaluate("$('view-menu').hidden")
    assert page.locator("#view-name").inner_text() == "Process Map" and page.evaluate("$('view-toggle').title") == "View 2: Process Map. Choose a view"
    assert page.evaluate("[...$('view-menu').children].map(item => item.getAttribute('aria-checked'))") == ["false", "true", "false"]


def test_the_address_remembers_the_view(page, browser, site_server):
    show(page, "score")
    assert page.evaluate("location.hash") == "#score"
    show(page, "des")
    assert page.evaluate("location.hash") == ""
    other, finish = open_page(browser, site_server[0] + "#graph")
    assert other.evaluate("view") == "graph" and other.locator("#view-name").inner_text() == "Process Map"
    finish()
    wrong, finish = open_page(browser, site_server[0] + "#nonsense")
    assert wrong.evaluate("view") == "des"
    finish()


def test_the_legend_follows_the_view(page):
    assert legend(page)[0] == "- Free table"
    show(page, "score")
    assert legend(page)[0] == "Figures"


def test_tokens_are_started_afresh_when_the_view_changes(page):
    run(page, 60)
    assert page.evaluate("desTokens.size") > 0
    show(page, "graph")
    assert page.evaluate("[desTokens.size, document.querySelectorAll('#des-floor-tokens > g').length]") == [0, 0] and page.evaluate("graphTokens.size") > 0
    show(page, "des")
    assert page.evaluate("[graphTokens.size, document.querySelectorAll('#graph-parties > g').length]") == [0, 0]


def test_each_view_keeps_its_own_zoom(page):
    page.click("#zoom-in")
    show(page, "graph")
    assert page.evaluate("zoomState().zoom.k") == 1
    show(page, "des")
    assert page.evaluate("zoomState().zoom.k") == 1.5
