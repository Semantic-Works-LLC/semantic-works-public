"""js/service-layout.js: the fixed parts of the service view."""
from tests.support import card, click, show_service


def test_eight_party_boxes_left_to_right_with_arrows(page):
    assert page.evaluate("PARTY_BOXES.map(box => box.name)") == ["At the door", "Walk in", "Read menu", "Wait to order", "Order", "Wait for food", "Eat", "Leave"]
    xs = page.evaluate("PARTY_BOXES.map(box => box.x)")
    assert xs == sorted(xs) and len(set(b - a for a, b in zip(xs, xs[1:]))) == 1
    assert page.locator("#loop-static .line-arrow").count() == 7
    assert page.evaluate("BOX_OF.cooking === PARTY_BOXES[5] && BOX_OF.door === PARTY_BOXES[0] && Object.keys(BOX_OF).length === 12")


def test_every_party_box_can_be_selected(page):
    show_service(page)
    boxes = "[...document.querySelectorAll('#loop-static > .step.work')].slice(0, 8)"
    expected = ["Front door", "Walk to the table", "Read the menu", "Wait to order", "Order", "Wait for food", "Eat", "Leave"]
    for index, name in enumerate(expected):
        click(page, f"{boxes}[{index}]")
        assert card(page)["name"] == name
        assert page.evaluate(f"{boxes}[{index}].hasAttribute('data-selected')")
    assert page.evaluate("selected.kind") == "Flow step"


def test_two_queues_stand_for_the_order_rail_and_the_pass(page):
    show_service(page)
    assert page.locator("#loop-static .step.wait").count() == 2
    assert page.locator("#loop-static .line-tag").all_text_contents() == ["QUEUE", "QUEUE"]
    for index, name in enumerate(["Order rail", "Pass table"]):
        click(page, f"document.querySelectorAll('#loop-static .step.wait')[{index}]")
        assert card(page)["name"] == name
        assert page.evaluate("selected.nodes.length === 2 && selected.nodes.every(n => n.hasAttribute('data-selected'))")


def test_four_arrows_trace_the_order_from_the_table_to_the_kitchen_and_back(page):
    assert page.locator("#loop-static .loop-arrow").count() == 4
    labels = page.locator("#loop-static .small-label").all_text_contents()
    assert "ticket" in labels and "food" in labels


def test_the_cook_box_holds_a_slot_for_each_station(page):
    show_service(page)
    assert page.locator("#loop-static .loop-station").count() == 4
    names = page.evaluate("[...document.querySelectorAll('#loop-static .loop-station')].map(r => r.nextSibling.textContent)")
    assert names == ["Stove 1", "Stove 2", "Pizza oven", "Coffee"]
    for index, name in enumerate(["Stove 1", "Stove 2", "Pizza oven", "Coffee machine"]):
        click(page, f"document.querySelectorAll('#loop-static .loop-station')[{index}].parentNode")
        assert card(page)["name"] == name
    click(page, "kitchenG.querySelector('.flow-box')")
    assert card(page)["name"] == "Cook" and card(page)["kind"] == "Flow step"
    assert page.evaluate("stations.every(s => s.spot.x > KITCHEN.x && s.spot.x < KITCHEN.x + KITCHEN.w)")


def test_free_areas_have_a_title_and_minus_and_plus_buttons(page):
    assert page.locator("#loop-static .loop-area").count() == 3   # waiters, cooks and the tables panel
    titles = page.locator("#loop-static .zone-label").all_text_contents()
    assert "WAITERS, FREE" in titles and "COOKS, FREE" in titles and "TABLES" in titles
    buttons = page.locator("#loop-static .loop-button")
    assert buttons.count() == 4
    assert [buttons.nth(i).get_attribute("aria-label") for i in range(4)] == ["One waiter fewer", "One more waiter", "One cook fewer", "One more cook"]
    assert page.evaluate("[...document.querySelectorAll('.loop-button')].map(b => b.querySelector('text').textContent)") == ["\u2212", "+", "\u2212", "+"]
    assert page.evaluate("[...document.querySelectorAll('.loop-button title')].map(t => t.textContent)")[1] == "One more waiter"


def test_minus_and_plus_change_the_number_of_staff_without_touching_the_selection(page):
    show_service(page)
    click(page, "tables[0].mini")
    for index, counts in [(1, [3, 2]), (3, [3, 3]), (0, [2, 3]), (2, [2, 2])]:
        click(page, f"document.querySelectorAll('.loop-button')[{index}]")
        page.evaluate("tick(0.05); draw()")
        assert page.evaluate("[waiters.length, cooks.length]") == counts
    assert card(page)["name"] == "Table 1"   # a click on a button is not a click on the background
    assert page.evaluate("[FREE_AREAS.waiter.total.textContent, FREE_AREAS.cook.total.textContent]") == ["\u00b7 2 in total", "\u00b7 2 in total"]


def test_twelve_small_tables_can_be_selected_too(page):
    show_service(page)
    assert page.locator("#loop-static .table").count() == 12
    assert page.evaluate("tables.map(t => t.mini.textContent)") == [f"{n}{seats}" for n, seats in zip(range(1, 13), [6, 6, 4, 2, 4, 6, 6, 4, 6, 4, 6, 2])]
    click(page, "tables[6].mini")
    assert card(page)["name"] == "Table 7"
    assert page.evaluate("tables[6].g.hasAttribute('data-selected') && tables[6].mini.hasAttribute('data-selected')")


def test_prep_counter_sink_and_fridge_are_not_in_the_service_view(page):
    text = page.evaluate("$('loop-static').textContent")
    assert "ALSO IN THE KITCHEN" not in text and "Sink" not in text and "Fridge" not in text
