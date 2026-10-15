"""js/service-motion.js: where everything is drawn in the service view, frame by frame."""
import re

from tests.support import fixed_random, run, run_until, seat_everyone, settle, show_service

AT = "(key => { const t = loopTokens.get(key); return [t.tx, t.ty]; })"


def test_free_staff_stand_in_the_free_areas(page):
    show_service(page)
    assert page.evaluate("[...loopTokens.keys()]") == ["Waiter 1", "Waiter 2", "Cook 1", "Cook 2"]
    assert page.evaluate(f"{AT}('Waiter 1')") == page.evaluate("[FREE_AREAS.waiter.x + 28, FREE_AREAS.waiter.y + 31]")
    assert page.evaluate(f"{AT}('Waiter 2')") == page.evaluate("[FREE_AREAS.waiter.x + 52, FREE_AREAS.waiter.y + 31]")
    assert page.evaluate(f"{AT}('Cook 2')") == page.evaluate("[FREE_AREAS.cook.x + 52, FREE_AREAS.cook.y + 31]")
    assert page.evaluate("loopTokens.get('Waiter 1').g.textContent") == "W1" and page.evaluate("loopTokens.get('Cook 2').g.textContent") == "C2"


def test_on_the_first_draw_everything_appears_in_place(page):
    seat_everyone(page, 4)
    run(page, 20)
    show_service(page)
    assert page.evaluate("[...loopTokens.values()].every(t => t.x === t.tx && t.y === t.ty)")
    assert page.evaluate("loopFresh") is False


def test_later_arrivals_glide_in_parties_from_the_left_edge_and_orders_from_their_party(page):
    show_service(page)
    fixed_random(page, 0, "spawnParty()")
    page.evaluate("nextArrival = 1e9; draw()")
    party = page.evaluate("(({ x, tx, y, ty }) => ({ x, tx, y, ty }))(loopTokens.get('p1'))")
    assert party["x"] < 0 < party["tx"] and party["y"] == party["ty"]   # starts off the left edge, level with its place
    run_until(page, "tickets.length === 1")
    assert page.evaluate("loopTokens.get('k1').home === loopTokens.get('p1')")
    order = page.evaluate("(({ x, y, tx }) => ({ x, y, tx }))(loopTokens.get('k1'))")
    assert order["x"] != order["tx"]   # it started at its party's place, not at its own


def test_parties_sit_in_the_box_for_their_step_longest_there_first(page):
    seat_everyone(page, 7)
    page.evaluate("nextArrival = 1e9")
    show_service(page)
    walk_in = page.evaluate("PARTY_BOXES[1]")
    spots = page.evaluate("parties.map(p => [loopTokens.get('p' + p.id).tx, loopTokens.get('p' + p.id).ty])")
    assert spots[:5] == [[walk_in["x"] + 17 + i * 24, 84 + 58] for i in range(5)]
    assert spots[5:] == [[walk_in["x"] + 17 + i * 24, 84 + 58 + 25] for i in range(2)]   # a second row after five
    run_until(page, "parties.some(p => KITCHEN_STEPS.includes(p.step))")
    waiting = page.evaluate("parties.find(p => KITCHEN_STEPS.includes(p.step)).id")
    assert page.evaluate(f"loopTokens.get('p{waiting}').tx") >= page.evaluate("PARTY_BOXES[5].x")
    assert page.evaluate(f"loopTokens.get('p{waiting}').also.length") == 2


def test_a_waiter_stands_where_the_work_is(page):
    show_service(page)
    fixed_random(page, 0, "spawnParty()")
    page.evaluate("nextArrival = 1e9; window.w = () => waiters.find(w => w.state !== 'idle')")
    for state, spot in [("toTable", "dockUnder(PARTY_BOXES[3])"), ("taking", "dockUnder(PARTY_BOXES[4])"), ("toRail", "WAITER_SPOT.toRail"),
                        ("hanging", "WAITER_SPOT.hanging"), ("toPass", "WAITER_SPOT.toPass"), ("picking", "WAITER_SPOT.picking"),
                        ("toServe", "WAITER_SPOT.toServe"), ("serving", "WAITER_SPOT.serving")]:
        run_until(page, f"w() && w().state === '{state}'")
        assert page.evaluate(f"{AT}(w().name)") == page.evaluate(f"[{spot}.x, {spot}.y]"), state


def test_two_waiters_doing_the_same_thing_stand_side_by_side(page):
    seat_everyone(page, 6)
    page.evaluate("nextArrival = 1e9")
    show_service(page)
    run_until(page, "waiters.every(w => w.state === 'toTable')")
    assert page.evaluate(f"[{AT}('Waiter 1')[0], {AT}('Waiter 2')[0]]") == page.evaluate("[WAITER_SPOT.toTable.x, WAITER_SPOT.toTable.x + 24]")


def test_a_cook_stands_at_the_rail_the_station_and_the_pass(page):
    show_service(page)
    fixed_random(page, 0.5, "spawnParty()")
    page.evaluate("nextArrival = 1e9; window.c = () => cooks.find(c => c.state !== 'idle')")
    run_until(page, "c() && c().state === 'toRail'")
    assert page.evaluate(f"{AT}(c().name)") == [688, 442]
    run_until(page, "c().state === 'working'")
    assert page.evaluate(f"{AT}(c().name)") == page.evaluate("[c().station.spot.x, c().station.spot.y]")
    assert float(page.evaluate("c().station.loopBar.getAttribute('width')")) >= 0
    run(page, 2)
    assert float(page.evaluate("stoves.find(s => s.on).loopBar.getAttribute('width')")) > 0
    run_until(page, "c() && c().state === 'toPass'")
    assert page.evaluate(f"{AT}(c().name)") == [808, 442]


def test_a_cook_waiting_for_equipment_stands_at_the_top_of_the_cook_box(page):
    show_service(page)
    run_until(page, "cooks[0].state === 'grabbing'")
    page.evaluate("cooks[0].job.stove = 0; cooks[0].job.oven = 1; cooks[0].job.coffee = 0; pizzaOven.busy = true")
    run_until(page, "cooks[0].state === 'waitStation'")
    assert page.evaluate(f"{AT}('Cook 1')") == page.evaluate("[COOK_SPOT.waitStation.x, COOK_SPOT.waitStation.y]")


def test_an_order_rides_with_its_waiter_or_cook_and_waits_in_the_queues(page):
    show_service(page)
    fixed_random(page, 0.5, "spawnParty()")
    page.evaluate("nextArrival = 1e9; window.k = () => loopTokens.get('k1'); window.who = name => loopTokens.get(name)")
    food = "[k().paper.getAttribute('visibility'), k().dish.getAttribute('visibility')]"
    run_until(page, "tickets.length === 1")
    assert page.evaluate("[k().tx - who(tickets[0].waiter.name).tx, k().ty - who(tickets[0].waiter.name).ty]") == [17, -11]
    assert page.evaluate(food) == ["visible", "hidden"]
    run_until(page, "tickets[0].stage === 'rail'")
    assert page.evaluate("[k().tx, k().ty]") == page.evaluate("[LOOP_QUEUES.rail.x + 19, LOOP_QUEUES.rail.y + 62]")
    run_until(page, "tickets[0].stage === 'cooking' && tickets[0].cook.state === 'working'")
    assert page.evaluate("[k().tx - who(tickets[0].cook.name).tx, k().ty - who(tickets[0].cook.name).ty]") == [17, -11]
    run_until(page, "onItsWayToPass(tickets[0])")
    assert page.evaluate(food) == ["hidden", "visible"]   # it is food from the moment the cook carries it
    run_until(page, "tickets[0].stage === 'pass'")
    assert page.evaluate("[k().tx, k().ty]") == page.evaluate("[LOOP_QUEUES.pass.x + 19, LOOP_QUEUES.pass.y + 62]")
    run_until(page, "tickets[0].stage === 'delivering'")
    assert page.evaluate("k().tx - who(tickets[0].waiter.name).tx") == 17
    run_until(page, "tickets.length === 0")
    settle(page)
    assert page.evaluate("loopTokens.has('k1')") is False   # served: it went back to its party and was removed


def test_averages_staff_totals_and_table_colours_are_kept_up_to_date(page):
    show_service(page)
    assert page.evaluate("[PARTY_BOXES[2].avg.textContent, LOOP_QUEUES.rail.avg.textContent, kitchenAvg.textContent]") == ["", "", ""]
    assert page.evaluate("FREE_AREAS.waiter.total.textContent") == "\u00b7 2 in total"
    run(page, 150)
    texts = page.evaluate("[...PARTY_BOXES.map(box => box.avg.textContent), LOOP_QUEUES.rail.avg.textContent, LOOP_QUEUES.pass.avg.textContent, kitchenAvg.textContent]")
    assert all(re.fullmatch(r"avg \d:\d\d", text) for text in texts[1:]), texts
    assert page.evaluate("tables.every(t => t.mini.getAttribute('class') === 'table ' + t.status)")
    assert page.evaluate("boxAverage(PARTY_BOXES[5])") > page.evaluate("boxAverage({ steps: ['cooking'] })")


def test_the_next_free_spot_in_a_grid(page):
    assert page.evaluate("(() => { loopSlots = {}; return [1, 2, 3, 4].map(() => gridSpot('test', 100, 50, 3)); })()") == [[100, 50], [124, 50], [148, 50], [100, 75]]
