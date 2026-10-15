"""js/picker.js: the magnifying-glass list of everything that can be selected."""
from tests.support import card, click, picker_groups, run, run_until


def test_picker_opens_from_the_magnifying_glass_and_lists_everything(page):
    assert page.locator("#picker").is_hidden()
    assert page.locator("#panel .actor").count() == 0
    page.click("#picker-toggle")
    assert page.locator("#picker").is_visible()
    assert page.locator("#picker-toggle").get_attribute("aria-expanded") == "true"
    assert page.evaluate("document.activeElement.id") == "picker-filter"
    groups = picker_groups(page)
    assert list(groups) == ["Order tickets, open (0)", "Order tickets, delivered (last 10) (0)", "Waiters (2)", "Cooks (2)",
                            "Guest parties (0)", "Tables (12)", "Hand-off points (3)", "Kitchen equipment (4)"]
    assert groups["Waiters (2)"] == ["Waiter 1", "Waiter 2"]
    assert groups["Tables (12)"] == [f"Table {n}" for n in range(1, 13)]
    assert groups["Hand-off points (3)"] == ["Front door", "Order rail", "Pass table"]
    assert groups["Kitchen equipment (4)"] == ["Stove 1", "Stove 2", "Pizza oven", "Coffee machine"]
    assert page.locator("#picker .none").all_text_contents() == ["No open orders.", "Nothing delivered yet.", "No guests at the moment."]
    assert page.evaluate("[...document.querySelectorAll('#picker details')].map(d => d.open)") == [True, False] + [True] * 6


def test_prep_counter_sink_and_fridge_are_not_offered(page):
    page.click("#picker-toggle")
    names = [name for group in picker_groups(page).values() for name in group]
    assert not {"Prep counter", "Sink", "Fridge"} & set(names)


def test_picker_buttons_are_plain_names_only(page):
    run(page, 60)
    page.click("#picker-toggle")
    assert page.evaluate("[...document.querySelectorAll('#picker .actor')].every(b => b.children.length === 0 && /^[A-Z][A-Za-z]+( [a-z]+)?( \\d+)?$/.test(b.textContent))")


def test_picking_a_name_selects_it_closes_the_picker_and_shows_its_card(page):
    page.click("#picker-toggle")
    page.click("#picker .actor:text-is('Pizza oven')")
    assert page.locator("#picker").is_hidden()
    assert page.locator("#picker-toggle").get_attribute("aria-expanded") == "false"
    assert card(page)["name"] == "Pizza oven"
    assert page.evaluate("$('panel').classList.contains('open') && pizzaOven.info.nodes[0].hasAttribute('data-selected')")
    page.click("#picker-toggle")
    assert page.locator("#picker .actor[aria-pressed='true']").all_inner_texts() == ["Pizza oven"]


def test_picker_lists_parties_and_tickets_as_they_come_and_go(page):
    page.click("#picker-toggle")
    page.evaluate("() => { const real = Math.random; Math.random = () => 0; spawnParty(); Math.random = real; nextArrival = 1e9; }")
    page.evaluate("__frame(last + 1000)")
    groups = picker_groups(page)
    assert groups["Guest parties (1)"] == ["Party 1"]
    assert "No guests at the moment." not in page.locator("#picker .none").all_text_contents()
    run_until(page, "tickets.length === 1")
    page.evaluate("updateActorList()")
    assert picker_groups(page)["Order tickets, open (1)"] == ["Ticket 1"]
    run_until(page, "delivered.length === 1")
    page.evaluate("updateActorList()")
    groups = picker_groups(page)
    assert groups["Order tickets, open (0)"] == [] and groups["Order tickets, delivered (last 10) (1)"] == ["Ticket 1"]
    assert "No open orders." in page.locator("#picker .none").all_text_contents()
    run_until(page, "parties.length === 0")
    page.evaluate("updateActorList()")
    assert picker_groups(page)["Guest parties (0)"] == []
    page.evaluate("document.querySelector('#picker details:nth-of-type(2)').open = true")
    page.click("#picker .actor:text-is('Ticket 1')")
    assert card(page)["kind"] == "Order ticket"


def test_picker_lists_staff_as_they_are_added_and_removed(page):
    page.click("#picker-toggle")
    page.evaluate("changeStaff('waiter', 1); changeStaff('cook', -1); tick(0.05); updateActorList()")
    groups = picker_groups(page)
    assert groups["Waiters (3)"] == ["Waiter 1", "Waiter 2", "Waiter 3"] and groups["Cooks (1)"] == ["Cook 1"]


def test_picker_filter_narrows_the_list(page):
    page.click("#picker-toggle")
    page.fill("#picker-filter", "cook")
    assert picker_groups(page) == {"Cooks (2)": ["Cook 1", "Cook 2"]}
    page.fill("#picker-filter", "TABLE 1")
    assert picker_groups(page) == {"Tables (12)": ["Table 1", "Table 10", "Table 11", "Table 12"]}
    page.fill("#picker-filter", "zzz")
    assert picker_groups(page) == {}
    page.fill("#picker-filter", "")
    assert len(picker_groups(page)) == 8
    page.fill("#picker-filter", "stove")
    page.click("#picker-toggle")
    page.click("#picker-toggle")
    assert page.input_value("#picker-filter") == "" and len(picker_groups(page)) == 8   # reopening clears the filter


def test_picker_closes_on_escape_outside_click_or_its_own_button(page):
    toggle, picker = page.locator("#picker-toggle"), page.locator("#picker")
    toggle.click()
    page.keyboard.press("a")
    page.click("#picker h3")
    assert picker.is_visible()
    page.keyboard.press("Escape")
    assert picker.is_hidden()
    toggle.click()
    page.click("h1")
    assert picker.is_hidden()
    toggle.click()
    toggle.click()
    assert picker.is_hidden()
    toggle.click()
    click(page, "tables[2].g")
    assert picker.is_hidden() and card(page)["name"] == "Table 3"


def test_picker_is_not_refreshed_while_hidden(page):
    run(page, 30)
    page.evaluate("__frame(last + 1000)")
    assert page.locator("#picker .actor").count() == 0


def test_clock_text(page):
    assert page.evaluate("[clockText(0), clockText(9.9), clockText(75), clockText(600)]") == ["0:00", "0:09", "1:15", "10:00"]
