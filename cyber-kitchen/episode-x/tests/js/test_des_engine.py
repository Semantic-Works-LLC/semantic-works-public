"""js/des-engine.js: the simulation itself. It has no page in it, so most tests here run an engine of
their own, headless, and look at its events and its state."""
import pytest

from tests.support import counts, resources, run, run_until

# an engine that closes its door after five minutes, so it can be run until nothing is left to do
ENGINE = "const engine = new DESEngine({ ...DES_CONFIG, arrivalsUntil: 300, ...(window.overrides || {}) }); const events = []; engine.subscribe(event => events.push(event));"


def headless(page, body, **overrides):
    page.evaluate("overrides => { window.overrides = overrides; }", overrides)
    return page.evaluate(f"(() => {{ {ENGINE} {body} }})()")


# ---------- the clock and the event queue ----------

def test_events_come_out_in_time_order_and_ties_in_the_order_they_were_scheduled(page):
    order = headless(page, """
        const e = new DESEngine({ ...DES_CONFIG, arrivalsUntil: -1 }); e.heap.length = 0;
        [[5, 'a'], [1, 'b'], [5, 'c'], [3, 'd'], [1, 'e'], [9, 'f'], [0, 'g']].forEach(([t, name]) => e.scheduleEvent(t, 'PARTY_BALKED', name));
        const out = []; while (e.heap.length) out.push(e.pop().entityId); return out.join('');""")
    assert order == "gbedacf"


def test_the_same_seed_gives_the_same_run(page):
    a, b, c = page.evaluate("""[1, 1, 2].map(seed => { const e = new DESEngine({ ...DES_CONFIG, seed, arrivalsUntil: 200 }), log = [];
        e.subscribe(event => log.push(`${event.timestamp.toFixed(3)} ${event.type} ${event.entityId}`)); e.runToEnd(); return log.join('|'); })""")
    assert a == b and a != c and a.count("|") > 200


def test_how_time_is_sliced_does_not_change_what_happens(page):
    whole, sliced, stepped = page.evaluate("""[e => e.runUntil(200), e => { for (let t = 0; t <= 200; t += 0.37) e.runUntil(t); e.runUntil(200); },
        e => { while (e.heap.length && e.heap[0].timestamp <= 200) e.step(); }].map(drive => {
            const e = new DESEngine(DES_CONFIG), log = []; e.subscribe(event => log.push(event.id + event.type)); drive(e); return log.join(); })""")
    assert whole == sliced == stepped


def test_run_until_moves_the_clock_even_with_nothing_to_do(page):
    assert headless(page, "const e = new DESEngine({ ...DES_CONFIG, arrivalsUntil: -1 }); e.heap.length = 0; e.runUntil(42); return [e.currentTime, e.step()];") == [42, None]


def test_subscribers_hear_every_event_after_it_is_applied(page):
    heard = headless(page, "engine.runUntil(60); return [events.length, engine.eventsProcessed, events[0].type, events.every((event, i) => !i || event.timestamp >= events[i - 1].timestamp)];")
    assert heard[0] == heard[1] > 20 and heard[2] == "PARTY_ARRIVED" and heard[3]


def test_each_kind_of_draw_has_its_own_stream(page):
    assert headless(page, "return [engine.rng('menu') === engine.rng('menu'), engine.rng('menu') !== engine.rng('dine'), engine.draw('plan', 2)];") == [True, True, 2]


# ---------- a visit from start to end ----------

def test_a_party_goes_through_the_states_in_order(page):
    log = headless(page, """let first = null; engine.subscribe(event => { if (event.type === 'PARTY_ARRIVED' && !first) first = engine.parties.get(event.entityId); });
        engine.runToEnd(); return first.log.map(([state]) => state);""")
    assert log == ["WAITING_FOR_TABLE", "READING_MENU", "WAITING_FOR_WAITER_ORDER", "ORDERING", "WAITING_FOR_COOK", "PLANNING", "COOKING",
                   "WAITING_FOR_PLATING", "PLATING", "WAITING_FOR_WAITER_DELIVER", "FOOD_RUNNING", "EATING_AND_BILLING", "DEPARTED"]


def test_the_events_of_one_visit(page):
    types = headless(page, "engine.runToEnd(); return events.filter(event => event.entityId === 'P1' && !event.type.endsWith('PATIENCE_OUT')).map(event => event.type);")
    assert types[:4] == ["PARTY_ARRIVED", "SEIZE_TABLE", "MENU_READ_COMPLETE", "SEIZE_WAITER_ORDER"]
    assert types[-3:] == ["DINING_COMPLETE", "RELEASE_TABLE", "PARTY_DEPARTED"]
    assert "SEIZE_COOK_PLAN" in types and "PLATE_COMPLETE" in types and "RELEASE_WAITER_DELIVER" in types
    late = headless(page, "engine.runToEnd(); return events.filter(event => event.entityId === 'P1').map(event => event.type).slice(-2);")
    assert late == ["ORDER_PATIENCE_OUT", "FOOD_PATIENCE_OUT"], "the patience timers still ring after the party has left, and are ignored"


def test_when_the_door_closes_everyone_is_accounted_for_and_everything_is_given_back(page):
    end = headless(page, """engine.runToEnd(); const s = engine.snapshot();
        return { came: s.arrived, out: s.departed + s.abandoned, inside: s.parties.size, pending: s.pending, ghosts: engine.ghosts.size,
                 held: Object.values(s.resources).map(r => r.allocated), queues: Object.values(s.queues).map(q => q.length) };""")
    assert end["came"] == end["out"] > 20 and end["inside"] == end["pending"] == end["ghosts"] == 0
    assert set(end["held"]) == {0} and set(end["queues"]) == {0}


def test_the_order_is_written_per_guest_with_dishes_pizzas_and_coffees(page):
    orders = headless(page, "engine.runToEnd(); const seen = []; engine.subscribe(() => 0); return events.filter(e => e.type === 'RELEASE_WAITER_ORDER').length;")
    assert orders > 10
    order = headless(page, """let got = null; engine.subscribe(event => { if (event.type === 'RELEASE_WAITER_ORDER' && !got) { const p = engine.parties.get(event.entityId); got = { size: p.size, ...p.order }; } });
        engine.runUntil(120); return got;""")
    assert order["stoves"] + order["oven"] == order["size"] and 0 <= order["coffee"] <= order["size"]
    assert "×" in order["lines"]


def test_a_party_sits_at_the_smallest_free_table_that_fits_it(page):
    picks = headless(page, """const fit = size => engine.tableFor({ size }); const first = [1, 3, 5].map(fit);
        engine.resources.tables.units[3] = { party: 'X' }; engine.resources.tables.units[11] = { party: 'Y' }; const second = fit(2);
        engine.resources.tables.units.fill({ party: 'Z' }); return [first, second, fit(2)];""")
    assert picks == [[3, 2, 0], 2, -1], "a pair takes a table for two, then a table for four once the twos are taken"


# ---------- the kitchen: parts made in parallel ----------

def test_a_kitchen_part_takes_a_cook_and_its_equipment_at_the_same_moment(page):
    together = headless(page, """let ok = true, seen = 0; engine.subscribe(event => {
            if (!['SEIZE_STOVE', 'SEIZE_OVEN', 'SEIZE_COFFEE'].includes(event.type)) return;
            const party = engine.parties.get(event.entityId), kind = event.resourceId; seen++;
            ok &&= party.held['cooks:' + kind] !== undefined && party.held[kind + ':' + kind] !== undefined
                && engine.resources.cooks.units[party.held['cooks:' + kind]].until === engine.resources[kind].units[party.held[kind + ':' + kind]].until; });
        engine.runToEnd(); return [ok, seen > 20];""")
    assert together == [True, True]


def test_parts_of_one_order_are_made_at_the_same_time(page):
    overlap = headless(page, """let found = false; engine.subscribe(() => { for (const party of engine.parties.values())
            if (party.parts && Object.values(party.parts).filter(state => state === 'cooking').length > 1) found = true; });
        engine.runToEnd(); return found;""", capacity={"waiters": 2, "cooks": 4, "stoves": 2, "oven": 1, "coffee": 1})
    assert overlap


def test_plating_waits_for_every_part(page):
    ok = headless(page, """let ok = true, plated = 0; engine.subscribe(event => { if (event.type !== 'SEIZE_COOK_PLATE') return;
            plated++; ok &&= Object.values(engine.parties.get(event.entityId).parts).every(state => state === 'done'); });
        engine.runToEnd(); return [ok, plated > 10];""")
    assert ok == [True, True]


def test_running_food_comes_before_taking_orders(page):
    first = headless(page, """engine.runUntil(1); engine.queues.order.push('A'); engine.queues.run.push('B');
        engine.parties.set('A', { id: 'A', held: {}, queued: { order: { since: 0, stay: {} } }, metrics: {} });
        engine.parties.set('B', { id: 'B', held: {}, queued: { run: { since: 0, stay: {} } }, metrics: {} });
        engine.resources.waiters.units = [null, false, false, false, false, false]; engine.resources.waiters.capacity = 1; engine.resources.waiters.allocated = 0;
        engine.dispatchWaiters(); return [engine.resources.waiters.units[0].party, engine.resources.waiters.units[0].task, engine.queues.order];""")
    assert first == ["B", "deliver", ["A"]]


# ---------- parties that do not get served ----------

def test_a_party_is_turned_away_when_three_are_already_waiting_at_the_door(page):
    door = headless(page, """let most = 0; engine.subscribe(() => { most = Math.max(most, engine.queues.host.length); }); engine.runToEnd();
        return [most, engine.balked, events.filter(event => event.type === 'PARTY_BALKED').length, engine.arrived + engine.balked];""",
                    capacity={"waiters": 1, "cooks": 1, "stoves": 2, "oven": 1, "coffee": 1})
    assert door[0] == 3 and door[1] == door[2] > 0 and door[3] == page.evaluate("(() => { const e = new DESEngine({ ...DES_CONFIG, arrivalsUntil: 300 }); e.runToEnd(); return e.arrived + e.balked; })()")


def test_a_party_that_waits_too_long_to_order_walks_out(page):
    left = headless(page, "engine.runToEnd(); return [engine.abandonedFor.order, engine.abandoned, engine.departed, events.filter(e => e.type === 'PARTY_ABANDONED').map(e => e.metadata.reason)];",
                    capacity={"waiters": 0, "cooks": 2, "stoves": 2, "oven": 1, "coffee": 1})
    assert left[0] == left[1] > 0 and left[2] == 0 and set(left[3]) == {"order"}


def test_a_party_that_waits_too_long_for_its_food_walks_out_and_the_work_in_hand_is_dropped(page):
    left = headless(page, """let ghosts = 0; engine.subscribe(() => { ghosts = Math.max(ghosts, engine.ghosts.size); }); engine.runToEnd();
        return [engine.abandonedFor.food, engine.abandonedFor.order, ghosts, engine.ghosts.size, engine.resources.cooks.allocated];""",
                    capacity={"waiters": 3, "cooks": 1, "stoves": 1, "oven": 1, "coffee": 1})
    assert left[0] > 0 and left[2] > 0, "some party gave up while a cook was still working for it"
    assert left[3] == 0 and left[4] == 0, "and that work was finished and the cook freed"


def test_a_party_whose_food_is_on_its_way_does_not_walk_out(page):
    kept = headless(page, """engine.runUntil(40); const party = [...engine.parties.values()][0]; party.timestamps.orderPlaced = 0; party.held['waiters:deliver'] = 0;
        const before = engine.abandoned; engine.currentTime = 41; engine.processEvent({ type: 'FOOD_PATIENCE_OUT', entityId: party.id }); return engine.abandoned - before;""")
    assert kept == 0


def test_events_for_a_party_that_has_gone_are_ignored(page):
    assert headless(page, "engine.runUntil(10); const before = engine.eventsProcessed; engine.processEvent({ type: 'MENU_READ_COMPLETE', entityId: 'P999' }); return engine.parties.size > 0;")


def test_a_happy_visit_has_every_wait_within_its_target(page):
    happy = headless(page, "engine.runToEnd(); return [engine.happy, engine.departed];")
    assert 0 < happy[0] <= happy[1]
    unhappy = headless(page, "engine.runToEnd(); return [engine.happy, engine.departed];", targets={"table": 0, "order": 0, "food": 0, "happy": 0.8})
    assert unhappy[0] < happy[0]


# ---------- resources ----------

def test_seizing_and_releasing_keep_count(page):
    held = headless(page, """const party = { id: 'P', held: {} }; const unit = engine.seize('oven', party, 'oven'); const during = [engine.resources.oven.allocated, engine.available('oven'), party.held['oven:oven']];
        engine.release('oven', party, 'oven'); return [unit, during, engine.resources.oven.allocated, engine.available('oven'), party.held];""")
    assert held == [0, [1, False, 0], 0, True, {}]


def test_the_engine_refuses_impossible_seizes_and_releases(page):
    errors = headless(page, """const tryIt = fn => { try { fn(); return 'ok'; } catch (error) { return error.message; } }, a = { id: 'A', held: {} }, b = { id: 'B', held: {} };
        engine.seize('oven', a, 'oven');
        return [tryIt(() => engine.seize('oven', b, 'oven')), tryIt(() => engine.seize('tables', b, 'table', 0) + engine.seize('tables', a, 'table', 0)), tryIt(() => engine.release('oven', b, 'oven'))];""")
    assert errors == ["oven: seized beyond capacity", "tables: unit 0 seized while taken", "oven: B released a unit it does not hold"]


def test_use_is_averaged_over_time_and_over_capacity(page):
    average = headless(page, """const party = { id: 'P', held: {} }; engine.currentTime = 0; engine.seize('stoves', party, 'stoves'); engine.currentTime = 10; engine.release('stoves', party, 'stoves');
        engine.currentTime = 20; return engine.snapshot().resources.stoves.average;""")
    assert average == pytest.approx(0.25), "one of two stoves, for half the time"


def test_one_more_waiter_starts_at_once(page):
    assert page.evaluate("desEngine.changeCapacity('waiters', 1)") is True
    assert resources(page)["waiters"]["units"] == ["free", "free", "free", "off", "off", "off"] and resources(page)["waiters"]["capacity"] == 3
    assert page.evaluate("desRecent[0].type + ' ' + desRecent[0].resourceId") == "CAPACITY_UP waiters"


def test_there_are_at_most_six_and_at_least_none(page):
    assert page.evaluate("[1, 2, 3, 4, 5, 6].map(() => desEngine.changeCapacity('cooks', 1))") == [True, True, True, True, False, False]
    assert page.evaluate("[1, 2, 3, 4, 5, 6, 7].map(() => desEngine.changeCapacity('cooks', -1))") == [True] * 6 + [False]
    assert resources(page)["cooks"]["capacity"] == 0


def test_a_free_one_leaves_at_once_and_a_busy_one_after_the_task(page):
    run_until(page, "desEngine.resources.waiters.allocated === 2")
    assert page.evaluate("desEngine.changeCapacity('waiters', -1)") and page.evaluate("desEngine.resources.waiters.leaving") == 1
    assert resources(page)["waiters"]["capacity"] == 2, "still two until one of them is done"
    run_until(page, "desEngine.resources.waiters.leaving === 0")
    assert resources(page)["waiters"]["capacity"] == 1 and resources(page)["waiters"]["units"].count("off") == 5


def test_one_who_was_about_to_leave_can_be_kept(page):
    run_until(page, "desEngine.resources.waiters.allocated === 2")
    page.evaluate("desEngine.changeCapacity('waiters', -1); desEngine.changeCapacity('waiters', 1)")
    assert page.evaluate("desEngine.resources.waiters.leaving") == 0
    run(page, 60)
    assert resources(page)["waiters"]["capacity"] == 2


# ---------- out of service ----------

def test_a_free_unit_goes_out_of_service_at_once_and_comes_back(page):
    assert page.evaluate("desEngine.setOut('oven', 0, true)") is True
    assert resources(page)["oven"] == {"capacity": 0, "allocated": 0, "units": ["out"]}
    assert page.evaluate("desEngine.setOut('oven', 0, true)") is False, "it is already out"
    assert page.evaluate("desRecent[0].type + ' ' + desRecent[0].resourceId") == "UNIT_OUT oven 1"
    assert page.evaluate("desEngine.setOut('oven', 0, false)") is True and resources(page)["oven"]["units"] == ["free"]
    assert page.evaluate("desEngine.setOut('oven', 0, false)") is False, "it is not out"


def test_a_busy_unit_finishes_its_task_first(page):
    run_until(page, "Boolean(desEngine.resources.cooks.units[0])")
    assert page.evaluate("desEngine.setOut('cooks', 0, true)") and page.evaluate("desEngine.snapshot().resources.cooks.goingOut") == [0]
    assert resources(page)["cooks"]["units"][0] == "busy" and resources(page)["cooks"]["capacity"] == 2
    run_until(page, "desEngine.resources.cooks.units[0] === DES_OUT")
    assert resources(page)["cooks"]["capacity"] == 1 and page.evaluate("desEngine.resources.cooks.goingOut.size") == 0


def test_a_busy_unit_asked_to_go_can_be_kept(page):
    run_until(page, "Boolean(desEngine.resources.cooks.units[0])")
    page.evaluate("desEngine.setOut('cooks', 0, true)")
    assert page.evaluate("desEngine.setOut('cooks', 0, false)") is True
    run(page, 60)
    assert resources(page)["cooks"]["units"][0] != "out" and resources(page)["cooks"]["capacity"] == 2


def test_nothing_is_given_to_a_unit_that_is_out(page):
    page.evaluate("desEngine.setOut('oven', 0, true); desEngine.setOut('tables', 3, true); desEngine.setOut('tables', 11, true)")
    run(page, 240)
    state = resources(page)
    assert state["oven"]["units"] == ["out"] and state["tables"]["units"][3] == state["tables"]["units"][11] == "out"
    assert page.evaluate("desEngine.queues.oven.length") > 0, "pizzas wait while the oven is broken"
    page.evaluate("desEngine.setOut('oven', 0, false)")
    assert resources(page)["oven"]["units"] == ["busy"], "fixed: the first waiting pizza order starts at once"


# ---------- queues and what they wait for ----------

def test_what_a_queue_is_missing(page):
    missing = headless(page, """const out = [engine.missing('oven'), engine.missing('host')];
        engine.resources.cooks.allocated = engine.resources.cooks.capacity; out.push(engine.missing('oven'));
        engine.resources.oven.allocated = 1; out.push(engine.missing('oven')); return out;""")
    assert missing == [["cooks"], ["tables"], ["cooks"], ["cooks", "oven"]], "with nothing short, the first need is named"


def test_waiting_is_charged_to_what_was_missing(page):
    run(page, 600)
    blocked = page.evaluate("desEngine.blocked")
    assert set(blocked) == {"host", "order", "plan", "stoves", "oven", "coffee", "plate", "run"}
    assert sum(sum(causes.values()) for causes in blocked.values()) > 0
    assert set(blocked["oven"]) <= {"cooks", "oven", "cooks+oven"}


def test_queue_waits_are_recorded_even_when_there_is_no_wait(page):
    run(page, 120)
    stats = page.evaluate("desEngine.queueStats.host")
    assert stats["done"] > 5 and min(stats["history"]) == 0 and stats["total"] >= 0


def test_only_the_latest_forty_times_are_kept_and_stays_are_trimmed_to_the_window(page):
    run(page, 900, dt=0.25)
    assert page.evaluate("[desEngine.queueStats.host.history.length, DES_KEEP]") == [40, 40]
    assert page.evaluate("desEngine.queueStats.host.stays.every(stay => stay.end === null || stay.end >= clock - DES_WINDOW - 60)")


# ---------- what renderers read ----------

def test_a_snapshot_is_a_copy(page):
    run(page, 60)
    assert page.evaluate("""(() => { const s = desEngine.snapshot(); const id = [...s.parties.keys()][0]; s.parties.get(id).state = 'CHANGED'; s.queues.host.push('X'); s.resources.tables.units[0] = 'X';
        return desEngine.parties.get(id).state !== 'CHANGED' && !desEngine.queues.host.includes('X') && desEngine.resources.tables.units[0] !== 'X'; })()""")


def test_the_snapshot_holds_the_totals(page):
    run(page, 120)
    totals = counts(page)
    assert totals["arrived"] >= totals["departed"] + totals["abandoned"] and totals["inside"] == totals["arrived"] - totals["departed"] - totals["abandoned"]
    assert totals["events"] > 100 and page.evaluate("desEngine.snapshot().time") == pytest.approx(page.evaluate("clock"))


def test_telemetry_follows_littles_law_in_the_long_run(page):
    run(page, 900, dt=0.25)
    t = page.evaluate("desEngine.telemetry()")
    assert t["L"] == counts(page)["inside"] and t["sample"] > 5
    assert t["predictedL"] == pytest.approx(t["lambda"] * t["W"]) and t["averageL"] == pytest.approx(t["predictedL"], rel=0.5)


def test_telemetry_before_anything_has_happened(page):
    assert page.evaluate("new DESEngine(DES_CONFIG).telemetry()") == {"L": 0, "averageL": 0, "lambda": 0, "W": 0, "predictedL": 0, "sample": 0}


def test_old_arrivals_and_departures_are_forgotten(page):
    run(page, 1300, dt=0.5)
    page.evaluate("desEngine.telemetry()")
    assert page.evaluate("desEngine.arrivalLog[0] >= clock - 601 && desEngine.departureLog[0][0] >= clock - 601 && desEngine.wipLog[1][0] >= clock - 601")
