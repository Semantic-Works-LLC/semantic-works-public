"""js/waiter-work.js: what a waiter does, step by step."""
import pytest

from tests.support import fixed_random, run, run_until, seat_everyone


def test_service_cycle_visits_every_stage(page):
    seen = page.evaluate("""() => {
        const seen = { table: new Set(), waiter: new Set(), cook: new Set(), party: new Set(), ticket: new Set(), carry: new Set() };
        for (let i = 0; i < 16000; i++) {
            tick(0.05);
            tables.forEach(t => seen.table.add(t.status));
            waiters.forEach(w => { seen.waiter.add(w.state); seen.carry.add('waiter:' + w.carry); });
            cooks.forEach(c => { seen.cook.add(c.state); seen.carry.add('cook:' + c.carry); });
            parties.forEach(p => seen.party.add(p.state));
            tickets.forEach(t => seen.ticket.add(t.stage));
            if (i % 10 === 0) draw();
        }
        return Object.fromEntries(Object.entries(seen).map(([key, set]) => [key, [...set].sort()]));
    }""")
    assert seen["table"] == sorted(["free", "reserved", "reading", "ready", "ordering", "waiting", "eating"])
    assert seen["waiter"] == sorted(["idle", "toTable", "taking", "toRail", "hanging", "toPass", "picking", "toServe", "serving"])
    assert set(seen["cook"]) >= {"idle", "toRail", "grabbing", "toStation", "working", "toPass", "plating"}
    assert seen["party"] == ["arriving", "leaving", "queue", "seated"]
    assert seen["ticket"] == ["carried", "cooking", "delivering", "pass", "rail"]
    assert set(seen["carry"]) == {"waiter:null", "waiter:ticket", "waiter:plates", "cook:null", "cook:ticket", "cook:plates"}
    assert page.evaluate("served") > 20
    assert page.locator("#s-served").inner_text() == str(page.evaluate("served"))
    assert page.evaluate("clock") == pytest.approx(800)
    assert page.locator("#s-clock").inner_text() == page.evaluate("clockText(clock)")
    assert page.evaluate("delivered.length") == 10   # only the latest ten delivered orders are kept


def test_a_ticket_travels_from_table_to_rail_to_cook_to_pass_and_back(page):
    run_until(page, "tickets.length > 0")
    page.evaluate("window.first = tickets[0]; window.stages = [first.stage]")
    page.evaluate("""() => { let n = 0; while (first.stage !== 'done' && n++ < 8000) {
        tick(0.05); if (stages.at(-1) !== first.stage) stages.push(first.stage); } draw(); }""")
    assert page.evaluate("stages") == ["carried", "rail", "cooking", "pass", "delivering", "done"]
    assert page.evaluate("first.delivered > first.created && delivered[0] === first && !tickets.includes(first)")
    assert page.evaluate("first.table.status") == "eating"
    assert page.evaluate("first.stove + first.oven === first.table.party.size")


def test_food_on_the_pass_comes_before_a_table_that_wants_to_order(page):
    seat_everyone(page, 2)
    page.evaluate("nextArrival = 1e9; waiters.splice(0)")
    run_until(page, "tables.filter(t => t.status === 'ready').length === 2")
    page.evaluate("window.order = { claimed: false, table: tables[0] }; pass.push(order)")
    assert page.evaluate("(job => [job.type, job.order === order, order.claimed])(nextWaiterJob())") == ["deliver", True, True]
    assert page.evaluate("nextWaiterJob().type") == "order"   # the food is spoken for, so the next job is a table


def test_the_table_that_has_waited_longest_is_served_first(page):
    seat_everyone(page, 3)
    page.evaluate("nextArrival = 1e9; window.gone = waiters.splice(0)")
    run_until(page, "tables.filter(t => t.status === 'ready').length === 3")
    oldest = page.evaluate("tables.filter(t => t.status === 'ready').sort((a, b) => a.since - b.since)[0].id")
    assert page.evaluate("nextWaiterJob().table.id") == oldest
    assert page.evaluate("nextWaiterJob().table.id") != oldest   # that table is now claimed
    page.evaluate("nextWaiterJob()")
    assert page.evaluate("nextWaiterJob()") is None


def test_a_waiter_with_nothing_to_do_walks_back_to_the_waiting_spot(page):
    fixed_random(page, 0, "spawnParty()")
    page.evaluate("nextArrival = 1e9")
    run_until(page, "delivered.length === 1")
    run(page, 20)
    assert page.evaluate("waiters.every(w => w.state === 'idle' && w.x === w.home.x && w.y === w.home.y)")
