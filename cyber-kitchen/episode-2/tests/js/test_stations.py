"""js/stations.js: the two stoves, the pizza oven and the coffee machine."""
from tests.support import card, click


def test_four_stations_each_with_a_card(page):
    assert page.evaluate("stations.map(s => [s.name, s.verb, s.info.name, s.info.kind])") == [
        ["stove 1", "Cooking", "Stove 1", "Kitchen equipment"], ["stove 2", "Cooking", "Stove 2", "Kitchen equipment"],
        ["the pizza oven", "Baking pizza", "Pizza oven", "Kitchen equipment"],
        ["the coffee machine", "Making coffee", "Coffee machine", "Kitchen equipment"]]
    assert page.evaluate("stations.every(s => !s.on && !s.busy && s.progress === 0)")


def test_each_cook_has_a_stove(page):
    assert page.evaluate("cooks.map(c => c.stove.name)") == ["stove 1", "stove 2"]


def test_clicking_a_station_on_the_floor_selects_it(page):
    click(page, "stoves[0].info.nodes[0]")
    assert card(page)["name"] == "Stove 1"
    click(page, "pizzaOven.info.nodes[0]")
    assert card(page)["name"] == "Pizza oven"
    click(page, "coffeeMachine.info.nodes[0]")
    assert card(page)["name"] == "Coffee machine"
