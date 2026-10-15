"""js/tables.js: the twelve tables and their status."""
from tests.support import card, click, run_until


def test_twelve_tables_four_round_two_small_six_large(page):
    assert page.evaluate("tables.map(t => t.type + t.capacity).sort()") == ["round4"] * 4 + ["six6"] * 6 + ["two2"] * 2
    assert page.locator("#furniture .table").count() == 12
    assert page.locator("#furniture .seat").count() == 4 * 4 + 6 * 6 + 2 * 2
    assert page.evaluate("tables.map(t => t.id)") == list(range(1, 13))


def test_tables_start_free(page):
    assert page.evaluate("tables.every(t => t.status === 'free')")
    assert page.evaluate("tables[0].title.textContent") == "Table 1 (seats 6): free"


def test_table_card_describes_its_shape_and_size(page):
    for index, shape, seats in [(0, "rectangular", 6), (2, "round", 4), (3, "small square", 2)]:
        click(page, f"tables[{index}].g")
        shown = card(page)
        assert shown["kind"] == "Table" and shown["What it is"] == f"A {shape} table that seats {seats}."


def test_table_colour_classes_and_plates_follow_the_status(page):
    run_until(page, "tables.some(t => t.status === 'eating')")
    table = "tables.find(t => t.status === 'eating')"
    assert page.evaluate(f"{table}.g.getAttribute('class')") == "table eating"
    assert page.evaluate(f"{table}.plates.filter(p => p.classList.contains('on')).length === {table}.party.size")
    assert page.evaluate(f"/^Table \\d+ \\(seats \\d\\): eating$/.test({table}.title.textContent)")
    page.evaluate("window.eaten = tables.find(t => t.status === 'eating')")
    run_until(page, "eaten.status === 'free'")
    assert page.evaluate("eaten.plates.every(p => !p.classList.contains('on')) && eaten.party === null")


def test_set_status_records_when_the_status_began(page):
    page.evaluate("clock = 42; setStatus(tables[5], 'ready')")
    assert page.evaluate("[tables[5].status, tables[5].since, tables[5].g.getAttribute('class')]") == ["ready", 42, "table ready"]
    assert page.locator(".table.ready .bubble").count() == 1


def test_a_table_can_say_what_was_ordered_at_it(page):
    page.evaluate("spawnParty(); window.t = parties[0].table")
    order = "t.info.extra[0][1]()"
    assert page.evaluate(order) == "Not ordered yet." and page.evaluate("'now' in t.info") is False
    run_until(page, "t.status === 'waiting'")
    assert page.evaluate(order) == page.evaluate("t.party.ticket.lines")
    run_until(page, "t.status === 'free'")
    assert page.evaluate(order) == "Nobody is sitting here."
