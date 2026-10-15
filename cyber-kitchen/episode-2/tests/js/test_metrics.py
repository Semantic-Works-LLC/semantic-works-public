"""js/metrics.js: for each kind of object, its objective, measure, number, verdict and history."""
import re

import pytest

from tests.support import fixed_random, run, run_until, seat_everyone, spec


def test_targets(page):
    assert page.evaluate("TARGET") == {"order": 60, "door": 30, "wantOrder": 15, "ordering": 5, "rail": 15, "cooking": 25, "pass": 10,
                                       "equipment": 0.8, "staff": 0.85, "table": 0.7}


def test_small_calculations(page):
    assert page.evaluate("[percent(0.256), percent(1), mean([]), mean([2, 4, 9])]") == ["26%", "100%", 0, 5]
    assert page.evaluate("[stepAverage('menu'), (FLOW.menu.done = 4, FLOW.menu.total = 30, stepAverage('menu'))]") == [0, 7.5]


def test_time_a_party_has_spent_in_a_step(page):
    page.evaluate("clock = 50")
    party = "{ spent: { door: 12 }, step: 'menu', stepSince: 44 }"
    assert page.evaluate(f"[spentIn({party}, 'door'), spentIn({party}, 'menu'), spentIn({party}, 'eating')]") == [12, 6, 0]


def test_verdicts_against_a_target(page):
    assert page.evaluate("[atMost(10, 10), atMost(12, 10), atMost(13, 10)]") == [["On target", "good"], ["A little over target", "warn"], ["Over target", "bad"]]
    assert page.evaluate("[atLeast(0.7, 0.7), atLeast(0.6, 0.7), atLeast(0.5, 0.7)]") == [["On target", "good"], ["A little under target", "warn"], ["Under target", "bad"]]


def test_latest_slice_compared_with_the_average(page):
    assert page.evaluate("trend(undefined, 0.5, percent)") == "No full 15-second slice yet."
    assert page.evaluate("trend(0.9, 0.5, percent)") == "Latest 15 seconds: 90%, above its average so far."
    assert page.evaluate("trend(0.2, 0.5, percent)") == "Latest 15 seconds: 20%, below its average so far."
    assert page.evaluate("trend(0.5, 0.5, percent)") == "Latest 15 seconds: 50%, the same as its average so far."
    assert page.evaluate("trend(0, 0, percent)") == "Latest 15 seconds: 0%, the same as its average so far."


def test_equipment_is_measured_by_share_of_time_in_use_against_eighty_percent(page):
    fresh = spec(page, "stoves[0].info")
    assert fresh["value"] == "0%" and fresh["unit"] == "of the time so far" and fresh["verdict"] == ["Within the limit", "good"]
    assert fresh["notes"] == ["Target: at most 80%.", "No full 15-second slice yet."]
    assert "80%" in fresh["objective"] and fresh["chart"] == "svg" and fresh["timeline"] == "svg" and fresh.get("numbers") is None
    page.evaluate("clock = 100; stoves[0].gauge.sum = 90; stoves[0].gauge.history = [1, 0.8]")
    worked = spec(page, "stoves[0].info")
    assert worked["value"] == "90%" and worked["verdict"] == ["Over the limit", "bad"]
    assert worked["notes"][1] == "Latest 15 seconds: 80%, below its average so far."
    for other in ("pizzaOven", "coffeeMachine"):
        assert spec(page, f"{other}.info")["notes"][0] == "Target: at most 80%."


def test_waiters_and_cooks_are_measured_by_share_of_time_busy(page):
    run(page, 120)
    waiter, cook = spec(page, "waiters[0].info"), spec(page, "cooks[0].info")
    assert re.fullmatch(r"\d+%", waiter["value"]) and waiter["notes"][0] == "Target: at most 85%."
    assert [row[0] for row in waiter["numbers"]] == ["Orders taken", "Orders served"]
    assert waiter["numbers"][0][1] == page.evaluate("waiters[0].counts.taking") > 0
    assert [row[0] for row in cook["numbers"]] == ["Orders cooked"] and cook["numbers"][0][1] > 0
    assert spec(page, "(changeStaff('waiter', 1), waiters[2].info)")["numbers"] == [["Orders taken", 0], ["Orders served", 0]]
    assert spec(page, "(changeStaff('cook', 1), cooks[2].info)")["numbers"] == [["Orders cooked", 0]]


def test_a_table_is_measured_by_share_of_time_taken_and_should_be_at_least_seventy_percent(page):
    fresh = spec(page, "tables[0].info")
    assert fresh["verdict"] == ["Under target", "bad"] and fresh["notes"][0] == "Target: at least 70%."
    assert fresh["numbers"] == [["Parties seated", 0], ["Guests seated", 0], ["Seats filled, on average", "\u2013"]]
    page.evaluate("clock = 100; Object.assign(tables[0], { seated: 2, guests: 9 }); tables[0].gauge.sum = 75")
    used = spec(page, "tables[0].info")
    assert used["value"] == "75%" and used["verdict"] == ["On target", "good"]
    assert used["numbers"] == [["Parties seated", 2], ["Guests seated", 9], ["Seats filled, on average", "75%"]]


def test_a_queue_is_measured_by_how_long_things_wait_in_it(page):
    fresh = spec(page, "floorObject('Order rail')")
    assert fresh["value"] == "\u2013" and fresh["unit"] == "on average, over 0 so far" and fresh["verdict"] == ["No history yet", "none"]
    assert fresh["notes"] == ["Target: at most 0:15.", ""]
    assert fresh["measure"] == "How long a ticket hangs on the rail before a cook takes it."
    assert fresh["numbers"] == [["Average number waiting", "0.0"]]
    run(page, 200)
    rail, on_pass = spec(page, "floorObject('Order rail')"), spec(page, "floorObject('Pass table')")
    assert re.fullmatch(r"\d:\d\d", rail["value"]) and rail["verdict"][1] in ("good", "warn", "bad")
    assert re.fullmatch(r"Latest: \d:\d\d, (above|at or below) the average so far\.", rail["notes"][1])
    assert on_pass["notes"][0] == "Target: at most 0:10." and "Dashed line: the target." in on_pass["caption"]


def test_the_front_door_also_counts_parties_turned_away(page):
    assert spec(page, "floorObject('Front door')")["numbers"] == [["Average number waiting", "0.0"], ["Parties turned away", "0 (0% of arrivals)"]]
    page.evaluate("partyCount = 6; turnedAway = 2; clock = 10; QUEUE_LENGTH.door.sum = 15")
    assert spec(page, "floorObject('Front door')")["numbers"] == [["Average number waiting", "1.5"], ["Parties turned away", "2 (25% of arrivals)"]]


def test_a_step_with_a_target_and_a_step_without(page):
    run(page, 150)
    ordering, menu = spec(page, "FLOW.ordering.info"), spec(page, "FLOW.menu.info")
    assert ordering["verdict"] == ["On target", "good"] and ordering["notes"][0] == "Target: at most 0:05."
    assert menu["verdict"] == ["No target", "none"] and menu["notes"][0] == "No target: this time is not ours to shorten."
    assert "Dashed line" not in menu["caption"] and "Green: within the target" not in menu["timelineCaption"]
    assert menu["objective"] == page.evaluate("STEP_OBJECTIVE.menu")
    for key in ("walkIn", "wantOrder", "cooking", "eating", "leaving"):
        assert spec(page, f"FLOW.{key}.info")["objective"] == page.evaluate(f"STEP_OBJECTIVE.{key}")


def test_wait_for_food_is_measured_from_order_taken_to_food_served(page):
    fresh = spec(page, "WAIT_FOR_FOOD")
    assert fresh["value"] == "\u2013" and fresh["verdict"] == ["No history yet", "none"] and fresh["notes"] == ["Target: at most 1:00.", ""]
    page.evaluate("servedOrders.push(40, 50, 90)")
    served = spec(page, "WAIT_FOR_FOOD")
    assert served["value"] == "1:00" and served["unit"] == "on average, over 3 so far" and served["verdict"] == ["On target", "good"]
    assert served["notes"][1] == "Latest: 1:30, above the average so far."
    page.evaluate("servedOrders.push(20)")
    assert spec(page, "WAIT_FOR_FOOD")["notes"][1] == "Latest: 0:20, at or below the average so far."


def test_a_ticket_is_measured_from_taken_to_served(page):
    fixed_random(page, 0.5, "spawnParty()")
    page.evaluate("nextArrival = 1e9")
    run_until(page, "tickets.length === 1 && tickets[0].stage === 'rail'")
    page.evaluate("window.ticket = tickets[0]")
    run(page, 2)
    open_ticket = spec(page, "ticket.info")
    assert open_ticket["unit"] == "and counting" and open_ticket["verdict"] == ["On target", "good"]
    assert open_ticket["notes"] == ["Target: at most 1:00.", "No order has been served yet."]
    assert "as soon as possible" in open_ticket["objective"]
    run_until(page, "ticket.stage === 'done'")
    closed = spec(page, "ticket.info")
    assert closed["unit"] == "closed" and closed["value"] == page.evaluate("clockText(ticket.delivered - ticket.created)")
    assert re.fullmatch(r"Average of the 1 orders served so far: \d:\d\d\. This one is at or below it\.", closed["notes"][1])
    run(page, 30)
    assert spec(page, "ticket.info")["value"] == closed["value"]
    page.evaluate("servedOrders[0] = 1")
    assert spec(page, "ticket.info")["notes"][1].endswith("This one is above it.")


def test_a_party_is_measured_by_its_waiting_only(page):
    page.evaluate("tables.forEach(t => { setStatus(t, 'eating'); t.timer = 1e9; })")   # every table taken
    fixed_random(page, 0.5, "spawnParty()")
    page.evaluate("window.p = parties[0]; nextArrival = 1e9")
    run(page, 10.5)
    queued = spec(page, "p.info")
    assert queued["value"] == "0:10" and queued["unit"] == "waiting so far" and queued["notes"][0] == "Target: at most 1:45 in all."
    assert "not counted" in queued["objective"]
    page.evaluate("tables.forEach(t => { setStatus(t, 'free'); t.timer = 0; })")
    run_until(page, "p.table && p.table.status === 'eating'")
    run(page, 3.5)
    fed = spec(page, "p.info")
    door, order, food = page.evaluate("[spentIn(p, 'door'), spentIn(p, 'wantOrder'), p.ticket.delivered - p.ticket.created]")
    assert fed["value"] == page.evaluate(f"clockText({door + order + food})")
    assert fed["numbers"][0][0] == "Time with the menu (not counted)" and fed["numbers"][1] == ["Time eating (not counted)", "0:03"]
    assert re.fullmatch(r"Average party so far: \d:\d\d\. This one is (above|at or below) it\.", fed["notes"][1])
    assert door == pytest.approx(10.5, abs=0.2)


def test_a_slow_party_is_over_target_and_above_average(page):
    page.evaluate("tables.forEach(t => { setStatus(t, 'eating'); t.timer = 1e9; }); spawnParty(); window.p = parties[0]; nextArrival = 1e9")
    run(page, 150)
    slow = spec(page, "p.info")
    assert slow["verdict"] == ["Over target", "bad"] and slow["notes"][1].endswith("This one is above it.")


def test_every_object_that_can_be_selected_has_metrics(page):
    seat_everyone(page, 5)
    run(page, 60)
    kinds = page.evaluate("""() => {
        const all = [...fixedObjects, ...waiters.map(w => w.info), ...cooks.map(c => c.info), ...parties.map(p => p.info),
                     ...tickets.map(t => t.info), ...STEPS.filter(s => s.info.nodes).map(s => s.info), WAIT_FOR_FOOD];
        return all.map(info => { const spec = metricsFor(info); return [info.kind, info.name, !!spec.objective && !!spec.measure && !!spec.value && spec.verdict.length === 2]; });
    }""")
    assert [name for _, name, ok in kinds if not ok] == []
    assert {kind for kind, _, _ in kinds} == {"Entrance", "Hand-off point", "Kitchen equipment", "Table", "Waiter", "Cook", "Guests", "Order ticket", "Flow step"}
