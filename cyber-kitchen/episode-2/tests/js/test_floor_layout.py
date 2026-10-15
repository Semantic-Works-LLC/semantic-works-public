"""js/floor-layout.js: where things are in the room, and how people walk between them."""


def test_layout_is_three_rows_of_four_tables(page):
    assert page.evaluate("LAYOUT.map(row => row.length)") == [4, 4, 4]
    assert page.evaluate("[COLS.length, ROWS.length, SERVICE.length]") == [4, 3, 3]
    assert page.evaluate("Object.fromEntries(Object.entries(SEATS).map(([type, seats]) => [type, seats.length]))") == {"six": 6, "round": 4, "two": 2}


def test_routes_follow_aisles_and_corridors(page):
    same_aisle = page.evaluate("route({x: 100, y: 240, aisle: 270}, {x: 300, y: 300, aisle: 270})")
    assert same_aisle == [{"x": 100, "y": 270}, {"x": 300, "y": 270}, {"x": 300, "y": 300}]
    left = page.evaluate("route({x: 190, y: 240, aisle: 270}, {x: 190, y: 495, aisle: 465})")
    assert [p["x"] for p in left] == [190, 85, 85, 190, 190]
    right = page.evaluate("route({x: 610, y: 240, aisle: 270}, {x: 610, y: 495, aisle: 465})")
    assert [p["x"] for p in right] == [610, 735, 735, 610, 610]
    from_kitchen_side = page.evaluate("route({x: 760, y: 350}, {x: 330, y: 240, aisle: 270})")
    assert from_kitchen_side == [{"x": 735, "y": 350}, {"x": 735, "y": 270}, {"x": 330, "y": 270}, {"x": 330, "y": 240}]
    to_kitchen_side = page.evaluate("route({x: 330, y: 240, aisle: 270}, {x: 762, y: 465})")
    assert to_kitchen_side == [{"x": 330, "y": 270}, {"x": 735, "y": 270}, {"x": 735, "y": 465}, {"x": 762, "y": 465}]
