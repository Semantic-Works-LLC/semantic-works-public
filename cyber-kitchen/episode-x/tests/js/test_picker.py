"""js/picker.js: the list behind the target button, everything that has a card, by name."""
from tests.support import about, picker_groups, run, run_until


def open_picker(page):
    page.click("#picker-toggle")


def test_the_list_is_built_only_while_the_picker_is_open(page):
    page.evaluate("updateActorList()")
    assert page.evaluate("$('actor-list').children.length") == 0
    open_picker(page)
    assert page.evaluate("$('actor-list').children.length") == 9


def test_everything_with_a_card_is_listed_in_groups_with_counts(page):
    open_picker(page)
    groups = picker_groups(page)
    assert list(groups) == ["Parties (0)", "Steps (10)", "Tables (12)", "Waiters (2)", "Cooks (2)", "Kitchen equipment (4)", "Resource pools (6)", "Outcomes (6)", "Scorecard (9)"]
    assert groups["Outcomes (6)"] == ["Parties", "Parties arriving", "Turned away", "Left: slow waiter", "Left: slow kitchen", "Dined"]
    assert groups["Kitchen equipment (4)"] == ["Stove 1", "Stove 2", "Pizza oven", "Coffee machine"]
    assert page.locator("#picker [data-group=parties] .none").inner_text() == "No parties at the moment."


def test_parties_come_and_go_from_the_list(page):
    open_picker(page)
    run(page, 60)
    page.evaluate("updateActorList()")
    names = picker_groups(page)[f"Parties ({page.evaluate('desEngine.parties.size')})"]
    assert names[0].startswith("Party ") and page.evaluate("document.querySelector('#picker [data-group=parties] .none')") is None
    first = names[0]
    run_until(page, f"![...desEngine.parties.values()].some(party => 'Party ' + party.number + ':' === '{first.split(' guest')[0][:first.index(':') + 1]}')")
    page.evaluate("updateActorList()")
    assert first not in next(iter(picker_groups(page).values()))


def test_only_staff_on_shift_are_listed(page):
    page.evaluate("desEngine.changeCapacity('waiters', 1); desEngine.changeCapacity('cooks', -1); desEngine.changeCapacity('cooks', -1)")
    open_picker(page)
    groups = picker_groups(page)
    assert groups["Waiters (3)"] == ["Waiter 1", "Waiter 2", "Waiter 3"] and groups["Cooks (0)"] == []
    assert page.locator("#picker [data-group=cooks] .none").inner_text() == "No cooks on shift."
    page.evaluate("desEngine.changeCapacity('cooks', 1); updateActorList()")
    assert picker_groups(page)["Cooks (1)"] == ["Cook 1"] and page.evaluate("document.querySelector('#picker [data-group=cooks] .none')") is None


def test_typing_filters_names_and_hides_groups_with_no_match(page):
    open_picker(page)
    page.fill("#picker-filter", "table 1")
    assert picker_groups(page) == {"Tables (12)": ["Table 1", "Table 10", "Table 11", "Table 12"]}
    page.fill("#picker-filter", "OVEN")
    assert picker_groups(page) == {"Kitchen equipment (4)": ["Pizza oven"], "Resource pools (6)": ["Pizza oven"]}


def test_clicking_a_name_selects_it_and_closes_the_picker(page):
    open_picker(page)
    page.click("#picker [data-group=tables] .actor >> nth=6")
    assert about(page)["name"] == "Table 7" and page.evaluate("$('picker').hidden")
    open_picker(page)
    assert page.evaluate("[...document.querySelectorAll('#picker .actor[aria-pressed=true]')].map(row => row.textContent)") == ["Table 7"]
