"""js/selection.js: selecting one object, the details panel, and the static about card."""
from tests.support import card, click, metrics, run_until, show_service


def test_details_button_and_close_button_toggle_the_panel(page):
    toggle = page.locator("#panel-toggle")
    assert toggle.inner_text() == "Show details" and not page.evaluate("$('panel').classList.contains('open')")
    toggle.click()
    assert toggle.inner_text() == "Hide details" and toggle.get_attribute("aria-pressed") == "true"
    assert "Nothing selected" in page.locator("#about .empty").inner_text()
    toggle.click()
    assert toggle.inner_text() == "Show details"
    toggle.click()
    page.click("#panel-close")
    assert not page.evaluate("$('panel').classList.contains('open')")


def test_every_fixed_object_is_selected_in_both_views_and_shows_one_card(page):
    names = page.evaluate("fixedObjects.map(o => o.name)")
    assert names == ["Front door", "Order rail", "Pass table", "Stove 1", "Stove 2", "Pizza oven", "Coffee machine"] + [f"Table {n}" for n in range(1, 13)]
    for index, name in enumerate(names):
        click(page, f"fixedObjects[{index}].nodes[0]")
        shown = card(page)
        assert shown["name"] == name
        assert list(shown)[:5] == ["kind", "name", "What it is", "Purpose", "Why it is here"]
        assert all(shown.values())
        assert page.locator("#about .about").count() == 1
        # one object, drawn on the floor and in the service view: both drawings are marked
        marked = page.evaluate(f"[document.querySelectorAll('[data-selected]').length, fixedObjects[{index}].nodes.every(n => n.hasAttribute('data-selected')), fixedObjects[{index}].nodes.length]")
        assert marked == [2, True, 2]
    assert page.evaluate("$('panel').classList.contains('open')")


def test_selecting_another_object_unmarks_the_first(page):
    click(page, "tables[0].g")
    click(page, "tables[1].g")
    assert page.evaluate("[tables[0].g.hasAttribute('data-selected'), tables[1].g.hasAttribute('data-selected')]") == [False, True]


def test_clicking_the_floor_clears_the_selection_but_leaves_the_panel_open(page):
    click(page, "tables[0].g")
    assert card(page)["name"] == "Table 1"
    click(page, "$('view')")
    assert card(page) is None and metrics(page) is None
    assert page.locator("[data-selected]").count() == 0
    assert "Nothing selected" in page.locator("#about .empty").inner_text()
    assert page.evaluate("$('panel').classList.contains('open')")


def test_clicking_the_service_view_background_clears_the_selection(page):
    show_service(page)
    click(page, "tables[3].mini")
    assert card(page)["name"] == "Table 4"
    click(page, "$('loop')")
    assert card(page) is None


def test_about_card_is_static_and_has_no_live_rows(page):
    page.evaluate("spawnParty(); window.t = parties[0].table")
    click(page, "t.g")
    before = card(page)
    assert set(before) == {"kind", "name", "What it is", "Purpose", "Why it is here"}
    run_until(page, "t.status === 'eating'")
    assert card(page) == before   # nothing on it follows the service
    click(page, "parties[0].members[0].el")
    assert set(card(page)) == {"kind", "name", "What it is", "Purpose", "Why it is here"}


def test_a_ticket_card_keeps_its_fixed_list_of_dishes(page):
    run_until(page, "tickets.length > 0")
    page.evaluate("select(tickets[0].info)")
    shown = card(page)
    assert shown["kind"] == "Order ticket" and shown["On the ticket"] == page.evaluate("tickets[0].lines")
    assert "Time since the order was taken" not in shown and "Right now" not in shown


def test_selecting_opens_the_panel_closes_the_picker_and_scrolls_to_the_top(page):
    page.click("#picker-toggle")
    page.evaluate("select(tables[0].info); document.querySelector('.panel-inner').scrollTop = 200; select(tables[1].info)")
    assert page.evaluate("[$('panel').classList.contains('open'), $('picker').hidden, document.querySelector('.panel-inner').scrollTop]") == [True, True, 0]


def test_a_row_given_as_a_function_is_kept_up_to_date(page):
    # the card can show a value that is worked out afresh on every draw
    page.evaluate("window.n = 1; select({ ...tables[0].info, why: () => 'count ' + n })")
    assert card(page)["Why it is here"] == "count 1"
    page.evaluate("n = 2; updateNow()")
    assert card(page)["Why it is here"] == "count 2"
    page.evaluate("updateNow()")
    assert card(page)["Why it is here"] == "count 2"


def test_opening_the_panel_fills_in_the_metrics_of_what_is_selected(page):
    page.evaluate("select(tables[0].info)")
    page.click("#panel-close")
    assert metrics(page) is None
    page.click("#panel-toggle")
    assert metrics(page)["Objective"].startswith("To have guests at it")
