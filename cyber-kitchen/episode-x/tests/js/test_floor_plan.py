"""js/floor-plan.js: where the door, the tables, their seats and the service spots are."""


def test_there_are_twelve_tables_in_three_rows_of_four(page):
    layout = page.evaluate("tables.map(t => [t.type, t.x, t.y, t.capacity])")
    assert len(layout) == 12
    assert [t[0] for t in layout[:4]] == ["six", "six", "round", "two"]
    assert sorted({t[2] for t in layout}) == [170, 370, 565] and sorted({t[1] for t in layout}) == [190, 330, 470, 610]


def test_seats_match_the_engine_and_surround_the_table(page):
    assert page.evaluate("tables.map(t => t.capacity)") == page.evaluate("DES_CONFIG.tables")
    assert page.evaluate("tables.every(t => t.seats.length === t.capacity && t.seats.every(s => Math.hypot(s.x - t.x, s.y - t.y) > 30 && Math.hypot(s.x - t.x, s.y - t.y) < 60))")


def test_every_table_has_a_spot_where_a_waiter_serves_it(page):
    assert page.evaluate("tables.every(t => t.sp.x === t.x && Math.abs(t.sp.y - t.y) === 72)")
    assert page.evaluate("tables.slice(0, 4).every(t => t.sp.y > t.y) && tables.slice(4).every(t => t.sp.y < t.y)")


def test_the_door_and_the_kitchen_spots(page):
    spots = page.evaluate("({ DOOR, OUTSIDE, RAIL_COOK, PASS_WAITER, PASS_COOK })")
    assert spots["OUTSIDE"]["x"] < 0 < spots["DOOR"]["x"] and spots["DOOR"]["y"] == spots["OUTSIDE"]["y"]
    assert spots["PASS_WAITER"]["x"] < 790 < spots["PASS_COOK"]["x"], "the waiter stands on the dining side of the pass, the cook on the kitchen side"
    assert spots["RAIL_COOK"]["x"] == spots["PASS_COOK"]["x"]
