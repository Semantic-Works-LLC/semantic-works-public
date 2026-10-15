"""js/orders.js: the menu, order tickets, and the two places they wait (the rail and the pass)."""
import re

from tests.support import fixed_random, run, run_until, seat_everyone


def test_the_menu_has_stove_dishes_and_pizzas(page):
    assert page.evaluate("[MENU.stove.length, MENU.oven.length]") == [6, 3]
    assert page.evaluate("MENU.oven.every(dish => dish.endsWith('pizza'))")


def test_a_ticket_lists_one_dish_per_guest_and_any_coffees(page):
    fixed_random(page, 0, "spawnParty()")
    run_until(page, "tickets.length === 1")
    ticket = page.evaluate("(({ id, stage, stove, oven, coffee, lines, spent }) => ({ id, stage, stove, oven, coffee, lines, spent }))(tickets[0])")
    assert ticket["id"] == 1 and ticket["stage"] == "carried" and ticket["spent"] == {}
    assert ticket["stove"] + ticket["oven"] == 1
    assert re.fullmatch(r"1 × [A-Za-z ]+(\n1 × Coffee)?", ticket["lines"])
    assert ("Coffee" in ticket["lines"]) == (ticket["coffee"] == 1)
    assert page.evaluate("tickets[0].table.party.ticket === tickets[0] && tickets[0].info.subject === tickets[0]")


def test_pizza_and_coffee_follow_the_dice(page):
    page.evaluate("spawnParty(); window.t = parties[0].table; window.w = waiters[0]")
    all_pizza_and_coffee = fixed_random(page, 0.1, "const k = makeTicket(t, w); return [k.stove, k.oven, k.coffee, k.lines];")
    size = page.evaluate("t.party.size")
    assert all_pizza_and_coffee[:3] == [0, size, size] and all_pizza_and_coffee[3].endswith(f"{size} × Coffee")
    plain = fixed_random(page, 0.9, "const k = makeTicket(t, w); return [k.stove, k.oven, k.coffee, k.lines];")
    assert plain[:3] == [size, 0, 0] and "Coffee" not in plain[3]


def test_ticket_card_text(page):
    fixed_random(page, 0, "spawnParty()")
    run_until(page, "tickets.length === 1")
    info = page.evaluate("(({ kind, name, listName, what }) => ({ kind, name, listName, what }))(tickets[0].info)")
    assert info["kind"] == "Order ticket" and info["listName"] == "Ticket 1"
    assert re.fullmatch(r"Ticket 1 for table \d+", info["name"])
    assert re.fullmatch(r"A paper slip with the order from table \d+ \(1 guest\), written by Waiter \d at \d:\d\d\.", info["what"])
    seat_everyone(page, 4)
    run_until(page, "tickets.length > 1 && tickets.at(-1).table.party.size > 1")
    assert re.search(r"\(\d guests\)", page.evaluate("tickets.at(-1).info.what"))


def test_a_tickets_clock_runs_until_the_food_is_served(page):
    fixed_random(page, 0, "spawnParty()")
    run_until(page, "tickets.length === 1")
    page.evaluate("window.ticket = tickets[0]; nextArrival = 1e9")
    age = "ticket.info.extra[1][1]()"
    assert page.evaluate("'now' in ticket.info") is False
    run_until(page, "ticket.stage === 'rail'")
    assert re.fullmatch(r"0:0\d", page.evaluate(age))
    run_until(page, "ticket.stage === 'done'")
    total = page.evaluate(age)
    assert total == page.evaluate("clockText(ticket.delivered - ticket.created)")
    run(page, 5)
    assert page.evaluate(age) == total   # the clock on a delivered ticket stops


def test_moving_a_ticket_records_how_long_each_stage_took(page):
    fixed_random(page, 0, "spawnParty()")
    page.evaluate("nextArrival = 1e9")
    run_until(page, "delivered.length === 1")
    spent = page.evaluate("delivered[0].spent")
    assert list(spent) == ["carried", "rail", "cooking", "pass", "delivering"]
    assert all(seconds > 0 for seconds in spent.values())
    total = page.evaluate("delivered[0].delivered - delivered[0].created")
    assert abs(sum(spent.values()) - total) < 1e-6
    assert page.evaluate("servedOrders") == [total]
    assert page.evaluate("[orderStays.length, orderStays[0].start === delivered[0].created, orderStays[0].end === delivered[0].delivered]") == [1, True, True]


def test_moving_a_ticket_asks_for_the_rail_and_pass_to_be_redrawn(page):
    fixed_random(page, 0, "spawnParty()")
    run_until(page, "tickets.length === 1")
    page.evaluate("draw(); moveTicket(tickets[0], 'rail')")
    assert page.evaluate("[boardsDirty, tickets[0].stage, tickets[0].since === clock]") == [True, "rail", True]
