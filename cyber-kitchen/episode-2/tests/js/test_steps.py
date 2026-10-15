"""js/steps.js: the service seen as twelve steps that a party and its order pass through."""
import re

from tests.support import run_until

KEYS = ["door", "walkIn", "menu", "wantOrder", "ordering", "toRail", "rail", "cooking", "pass", "deliver", "eating", "leaving"]


def test_twelve_steps_in_order_four_of_them_waiting(page):
    assert page.evaluate("STEPS.map(s => s.key)") == KEYS
    assert page.evaluate("STEPS.filter(s => s.kind === 'wait').map(s => s.key)") == ["door", "wantOrder", "rail", "pass"]
    assert page.evaluate("Object.keys(FLOW)") == KEYS
    assert page.evaluate("STEPS.every(s => s.done === 0 && s.total === 0 && s.history.length === 0 && s.stays.length === 0)")


def test_every_step_has_a_card_with_static_text(page):
    infos = page.evaluate("STEPS.map(s => s.info)")
    for info in infos:
        assert info["kind"] == "Flow step" and info["name"] and info["what"] and info["purpose"] and info["why"]
        assert [row[0] for row in info["extra"]] == ["What flows through", "Resources", "Time spent here"]
    assert page.evaluate("FLOW.rail.info.what") == page.evaluate("KIND_WHAT.wait")
    assert page.evaluate("FLOW.rail.info.extra[0][1]") == "The party's order, as a paper ticket."


def test_a_step_can_say_how_long_parties_take(page):
    time_spent = "FLOW.menu.info.extra[2][1]()"
    assert page.evaluate(time_spent) == "No party has finished this step yet."
    run_until(page, "FLOW.menu.done > 0")
    assert re.fullmatch(r"0:0\d on average, over \d+ so far\.", page.evaluate(time_spent))


def test_wait_for_food_has_a_card_of_its_own(page):
    info = page.evaluate("WAIT_FOR_FOOD")
    assert info["kind"] == "Flow step" and info["name"] == "Wait for food" and info["subject"] == {"key": "waitForFood"}
    assert [row[0] for row in info["extra"]] == ["What flows through", "Resources"]
    assert page.evaluate("KITCHEN_STEPS") == ["toRail", "rail", "cooking", "pass", "deliver"]


def test_a_partys_step_is_read_from_the_simulation(page):
    seen = page.evaluate("""() => {
        const seen = new Set(), order = [];
        spawnParty(); const first = parties[0];
        for (let i = 0; i < 12000; i++) {
            tick(0.05);
            parties.forEach(p => seen.add(p.step));
            if (parties.includes(first) && order.at(-1) !== first.step) order.push(first.step);
        }
        return [[...seen].sort(), order];
    }""")
    assert seen[0] == sorted(KEYS)
    assert seen[1] == [key for key in KEYS if key != "door"]   # the first party is seated at once and then visits every step in order


def test_step_of_follows_party_table_and_ticket(page):
    step = "stepOf({ state: '%s', table: { status: '%s' }, ticket: %s })"
    assert page.evaluate(step % ("queue", "free", "null")) == "door"
    assert page.evaluate(step % ("arriving", "reserved", "null")) == "walkIn"
    assert page.evaluate(step % ("leaving", "free", "null")) == "leaving"
    assert page.evaluate(step % ("seated", "reading", "null")) == "menu"
    assert page.evaluate(step % ("seated", "ready", "null")) == "wantOrder"
    assert page.evaluate(step % ("seated", "ordering", "{ stage: 'carried' }")) == "toRail"
    assert page.evaluate(step % ("seated", "waiting", "{ stage: 'pass' }")) == "pass"
    assert page.evaluate(step % ("seated", "eating", "{ stage: 'done' }")) == "eating"
