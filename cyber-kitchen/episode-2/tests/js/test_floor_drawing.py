"""js/floor-drawing.js: walls, the front door, the order rail, the pass table and the kitchen scenery."""


def test_rooms_and_labels_are_drawn(page):
    assert page.locator("#floor .zone-label").all_text_contents() == ["DINING ROOM", "KITCHEN"]
    assert page.locator("#floor .wall").count() == 2
    labels = page.locator("#furniture .small-label").all_text_contents()
    for label in ["ORDER RAIL", "PASS", "PREP COUNTER", "SINK", "FRIDGE", "STOVES", "PIZZA OVEN", "COFFEE"]:
        assert label in labels


def test_prep_counter_sink_and_fridge_are_scenery_and_cannot_be_selected(page):
    assert page.evaluate("fixedObjects.filter(o => /Prep|Sink|Fridge/.test(o.name)).length") == 0
    sink = "[...document.querySelectorAll('#furniture .small-label')].find(t => t.textContent === 'SINK')"
    assert page.evaluate(f"{sink}.closest('[data-selectable]')") is None


def test_door_rail_and_pass_are_objects_with_static_descriptions(page):
    infos = page.evaluate("fixedObjects.slice(0, 3).map(o => [o.kind, o.name, !!o.what, !!o.purpose, !!o.why])")
    assert page.evaluate("fixedObjects.slice(0, 3).some(o => 'now' in o)") is False   # nothing live on the cards
    assert infos == [["Entrance", "Front door", True, True, True], ["Hand-off point", "Order rail", True, True, True],
                     ["Hand-off point", "Pass table", True, True, True]]
