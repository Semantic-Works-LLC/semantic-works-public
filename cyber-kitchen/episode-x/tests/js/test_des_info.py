"""js/des-info.js: the page's one engine, and the card of everything in it."""
import pytest

from tests.support import about, click, metrics, run, run_until, spec

STEPS = ["seating", "browsing", "ordering", "planning", "stoves", "oven", "coffee", "plating", "running", "dining"]
POOLS = ["tables", "waiters", "cooks", "stoves", "oven", "coffee"]


# ---------- the engine and its events ----------

def test_the_page_runs_one_engine_and_keeps_its_latest_events(page):
    run(page, 600)
    assert page.evaluate("desEngine instanceof DESEngine && desRecent.length === DES_EVENTS_KEPT && DES_EVENTS_KEPT") == 300
    assert page.evaluate("desRecent[0].timestamp >= desRecent[299].timestamp"), "newest first"


def test_parties_that_walk_out_are_remembered(page):
    page.evaluate("desEngine.changeCapacity('waiters', -1); desEngine.changeCapacity('waiters', -1)")
    run_until(page, "desEngine.abandoned > 0")
    assert page.evaluate("desGaveUp.size === desEngine.abandoned && [...desGaveUp].every(id => !desEngine.parties.has(id))")


def test_a_party_that_leaves_while_selected_stays_selected_and_its_card_says_the_visit_is_over(page):
    run(page, 30)
    page.evaluate("window.first = [...desEngine.parties.keys()][0]; select(desPartyInfo(first))")
    name = about(page)["name"]
    run_until(page, "!desEngine.parties.has(first)")
    assert about(page)["name"] == name and page.evaluate("desPartyInfos.has(first) && selected === desPartyInfo(first)")
    card = spec(page, "desPartyInfo(first)")
    numbers = dict(card["numbers"])
    assert card["notes"][0].startswith("Visit over: dined and left at ") and card["unit"] == "in the building; the visit is over"
    assert card["verdict"][0] in ("Happy visit", "Not a happy visit") and numbers["Table"] == "Given back." and "Left at" in numbers
    value = card["value"]
    run(page, 60)
    assert spec(page, "desPartyInfo(first)")["value"] == value, "the time inside no longer grows"


def test_the_card_of_a_party_that_gave_up_says_why(page):
    page.evaluate("desEngine.changeCapacity('waiters', -1); desEngine.changeCapacity('waiters', -1)")
    run_until(page, "desEngine.parties.size > 0")
    page.evaluate("window.first = [...desEngine.parties.keys()][0]; desPartyInfo(first)")
    run_until(page, "!desEngine.parties.has(first)")
    card = spec(page, "desPartyInfo(first)")
    assert card["notes"][0].startswith("Visit over: left without eating: nobody came to take the order at ") and card["verdict"] == ["Not a happy visit", "bad"]
    page.evaluate("desEngine.changeCapacity('waiters', 1); desEngine.changeCapacity('waiters', 1); desEngine.changeCapacity('cooks', -1); desEngine.changeCapacity('cooks', -1)")
    run_until(page, "desEngine.abandonedFor.food > 0")
    gone = page.evaluate("[...desGaveUp].at(-1)")
    assert page.evaluate(f"desPartyInfos.has('{gone}')") is False or "the food took too long" in spec(page, f"desPartyInfo('{gone}')")["notes"][0]


def test_everyone_in_the_building_has_a_card_as_a_group(page):
    assert spec(page, "desPartiesInfo")["unit"] == "parties in the building now"
    run_until(page, "desEngine.parties.size === 1")
    assert spec(page, "desPartiesInfo")["unit"] == "party in the building now"
    run(page, 300)
    card = spec(page, "desPartiesInfo")
    numbers = dict(card["numbers"])
    assert card["value"] == page.evaluate("desEngine.parties.size") and numbers["Seated"] + numbers["Waiting at the door"] == card["value"]
    assert numbers["Guests in the building"] >= card["value"] and ":" in numbers["Average time inside, last three minutes"]
    assert page.evaluate("[desPartiesInfo.kind, desPartiesInfo.name]") == ["Parties", "Parties"]


def test_attach_makes_a_node_selectable(page):
    assert page.evaluate("""(() => { const node = el('rect', {}, $('des-static')), info = { nodes: [], name: 'Probe', metrics: () => metricsFor(DES_RES.cooks.info) };
        const back = desAttach(node, info); node.dispatchEvent(new MouseEvent('click', { bubbles: true }));
        return back === info && info.nodes[0] === node && node.hasAttribute('data-selectable') && selected === info && node.hasAttribute('data-selected'); })()""")


def test_mean_of_no_times_is_zero(page):
    assert page.evaluate("[desMean({ done: 0, total: 0 }), desMean({ done: 4, total: 10 })]") == [0, 2.5]


# ---------- time cards ----------

def test_a_time_card_before_any_history(page):
    card = spec(page, "DES_TASKS.ordering.info")
    assert card["value"] == "–" and card["verdict"] == ["No history yet", "none"] and card["notes"][-1] == ""


def test_a_time_card_against_a_target(page):
    run(page, 300)
    card = spec(page, "DES_TASKS.ordering.info")
    assert card["unit"].startswith("on average, over ") and card["verdict"][1] in ("good", "warn", "bad")
    assert "Target: at most 0:15." in card["notes"] and card["notes"][-1].startswith("Latest: ")
    assert "Dashed line: the target." in card["caption"] and "Green: within the target." in card["timelineCaption"]


def test_a_time_card_without_a_target(page):
    run(page, 300)
    card = spec(page, "DES_TASKS.dining.info")
    assert card["verdict"] == ["No target", "none"] and "No target: this time is not ours to shorten." in card["notes"]
    assert "Dashed line" not in card["caption"] and card["chartTitle"] == "Time by party" and card["timelineTitle"] == "Time on the clock"


# ---------- resources and their units ----------

@pytest.mark.parametrize("pool", POOLS)
def test_every_resource_has_a_card_with_its_own_objective(page, pool):
    run(page, 60)
    card = spec(page, f"DES_RES.{pool}.info")
    info = page.evaluate(f"({{ kind: DES_RES.{pool}.info.kind, name: DES_RES.{pool}.info.name, what: DES_RES.{pool}.info.what }})")
    assert info["kind"] == "Resource pool" and card["objective"] and card["measure"] and card["numbers"][0][0] == "In use now"
    assert info["what"] == ("A resource pool with one unit." if pool in ("oven", "coffee") else f"A resource pool of {12 if pool == 'tables' else 2} units.")


def test_units_are_named_and_a_single_one_takes_the_resources_name(page):
    names = page.evaluate("Object.fromEntries(Object.entries(DES_RES).map(([id, res]) => [id, res.units.map(unit => unit.name)]))")
    assert names["oven"] == ["Pizza oven"] and names["stoves"] == ["Stove 1", "Stove 2"]
    assert names["tables"][6] == "Table 7" and len(names["waiters"]) == 6, "staff have a place for each of the six there can be"


def test_a_table_says_how_many_it_seats(page):
    assert page.evaluate("DES_RES.tables.units[3].info.what") == "Unit 4 of the tables pool. It seats 2."
    assert page.evaluate("DES_RES.oven.units[0].info.what") == "The only unit of the pizza oven pool."


def test_a_unit_says_what_it_is_doing_now(page):
    assert spec(page, "DES_RES.cooks.units[0].info")["numbers"] == [["Now", "Free."]]
    run_until(page, "Boolean(desEngine.resources.cooks.units[0])")
    now = spec(page, "DES_RES.cooks.units[0].info")["numbers"][0][1]
    assert now.endswith(".") and "party" in now and now[0].isupper()
    page.evaluate("desEngine.setOut('cooks', 0, true)")
    assert spec(page, "DES_RES.cooks.units[0].info")["numbers"][0][1].endswith("Off sick once this is done.")
    run_until(page, "desEngine.resources.cooks.units[0] === DES_OUT")
    assert spec(page, "DES_RES.cooks.units[0].info")["numbers"] == [["Now", "Off sick."]]


def test_the_words_for_out_of_service(page):
    words = page.evaluate("['cooks', 'waiters', 'oven', 'tables'].map(id => [desOutWords(id).state, desOutWords(id).out, desOutWords(id).back])")
    assert words == [["Off sick", "Call in sick", "Back to work"]] * 2 + [["Broken down", "Break down", "Fix"], ["Out of use", "Close table", "Open table"]]


def test_which_unit_a_card_is_about(page):
    assert page.evaluate("[desUnitOf(DES_RES.tables.units[6].info), desUnitOf(DES_RES.oven.units[0].info), desUnitOf(DES_RES.tables.info), desUnitOf(DES_TASKS.oven.info)]") == [
        {"id": "tables", "index": 6}, {"id": "oven", "index": 0}, None, None]


# ---------- queues and the stages of a visit ----------

def test_every_queue_has_a_card(page):
    run(page, 300)
    for queue in ["host", "order", "plan", "stoves", "oven", "coffee", "plate", "run"]:
        card = spec(page, f"DES_QUEUE.{queue}.info")
        assert card["objective"].startswith("Nobody waits long for ") and card["numbers"][0][0] == "Waiting now"
    assert spec(page, "DES_QUEUE.host.info")["numbers"][-1][0] == "Turned away"


def test_a_queue_with_someone_in_it_says_what_is_missing(page):
    page.evaluate("desEngine.setOut('oven', 0, true)")
    run_until(page, "desEngine.queues.oven.length > 1")
    run(page, 60)
    numbers = dict(spec(page, "DES_QUEUE.oven.info")["numbers"])
    assert numbers["Missing right now"] in ("the oven", "a cook and the oven, both taken")
    assert any(label.startswith("Of the waiting so far, missing ") and value.endswith("%") for label, value in numbers.items())


def test_what_is_missing_in_words(page):
    assert page.evaluate("[desMissingText(['cooks'], true), desMissingText(['cooks', 'oven'], true), desMissingText(['tables'], false), desMissingText(['cooks', 'coffee'], false)]") == [
        "a cook", "a cook and the oven, both taken", "waiting for table", "for cook + machine"]


def test_a_queue_needing_one_thing_has_no_split_by_cause(page):
    run(page, 300)
    assert page.evaluate("[desBlockedRows('host'), desBlockedRows('order')]") == [[], []]


def test_the_stages_of_a_visit_have_cards_and_a_queue_stage_shares_its_queues(page):
    run(page, 300)
    assert page.evaluate("DES_STAGES.length === 12 && DES_STAGE.WAITING_FOR_COOK.info === DES_QUEUE.plan.info && DES_STAGE.WAITING_FOR_TABLE.info === DES_QUEUE.host.info")
    for state in ["READING_MENU", "ORDERING", "PLANNING", "COOKING", "PLATING", "FOOD_RUNNING", "EATING_AND_BILLING"]:
        card = spec(page, f"DES_STAGE.{state}.info")
        assert card["objective"] and card["measure"] == "Time a party spends in this stage, from entering it to leaving it."
    assert spec(page, "DES_STAGE.READING_MENU.info")["objective"] == "Let the guests take the time they want."


# ---------- steps ----------

@pytest.mark.parametrize("step", STEPS)
def test_every_step_has_a_card_about_its_own_objective(page, step):
    run(page, 300)
    card, info = spec(page, f"DES_TASKS.{step}.info"), page.evaluate(f"({{ name: DES_TASKS.{step}.info.name, purpose: DES_TASKS.{step}.info.purpose, extra: DES_TASKS.{step}.info.extra, kind: DES_TASKS.{step}.info.kind ?? null }})")
    assert info["kind"] is None and info["purpose"] and info["extra"][0][0] == "Needs"
    assert card["objective"] and card["measure"] and len(card["measure"].split(". ")) <= 2, "what is measured, in two sentences at most"
    waits = step not in ("browsing", "dining")
    assert card["chartTitle"] == ("Wait time by party" if waits else "Time by party")
    assert card["timelineTitle"] == ("Wait time on the clock" if waits else "Time on the clock")
    assert "The same" not in card["chartTitle"] + card["timelineTitle"]


def test_a_step_says_who_is_waiting_and_for_what(page):
    assert spec(page, "DES_TASKS.oven.info")["notes"][0] == "Waiting now: nobody."
    page.evaluate("desEngine.setOut('oven', 0, true)")
    run_until(page, "desEngine.queues.oven.length > 0")
    card = spec(page, "DES_TASKS.oven.info")
    assert card["notes"][0].startswith("Waiting now: ") and "the oven" in card["notes"][0]
    assert dict(card["numbers"])["Held up by"] != "Nothing: nobody is waiting."


def test_get_a_table_takes_no_time_of_its_own(page):
    run(page, 60)
    assert dict(spec(page, "DES_TASKS.seating.info")["numbers"])["Time the step itself takes"].startswith("None:")
    assert "Being done now" in dict(spec(page, "DES_TASKS.ordering.info")["numbers"])


def test_plating_counts_the_orders_held_for_other_parts(page):
    run_until(page, "desHeldForParts().length > 0")
    card = spec(page, "DES_TASKS.plating.info")
    assert dict(card["numbers"])["Orders waiting for other parts"] >= 1
    assert any(note.startswith("Also held back: ") for note in card["notes"])


def test_the_other_parts_of_an_order_have_their_own_card(page):
    assert spec(page, "desPartsInfo")["unit"] == "orders short of a part now"
    run_until(page, "desHeldForParts().length === 1")
    card = spec(page, "desPartsInfo")
    assert card["value"] == 1 and card["unit"] == "order short of a part now" and "still to come: " in card["notes"][1]
    assert page.evaluate("desPartsInfo.name") == "Other parts of the order"


# ---------- outcomes and the door ----------

def test_each_outcome_has_its_own_card(page):
    page.evaluate("desEngine.changeCapacity('cooks', -1)")
    run(page, 900, dt=0.25)
    cards = {key: spec(page, f"DES_OUTCOME.{key}.info") for key in ["away", "noorder", "hungry", "out"]}
    names = page.evaluate("Object.values(DES_OUTCOME).map(outcome => [outcome.info.kind, outcome.info.name])")
    assert names == [["Outcome", "Turned away"], ["Outcome", "Left: slow waiter"], ["Outcome", "Left: slow kitchen"], ["Outcome", "Dined"]]
    totals = page.evaluate("[desEngine.balked, desEngine.abandonedFor.order, desEngine.abandonedFor.food, desEngine.departed]")
    assert [cards[key]["value"] for key in ["away", "noorder", "hungry", "out"]] == totals and totals[0] > 0 and totals[2] > 0 and totals[3] > 0
    assert cards["away"]["numbers"][0][0] == "Share of the parties that came to the door"
    assert cards["out"]["numbers"][1][0].startswith("Of them happy") and cards["out"]["chartMarks"] > 20


def test_an_outcome_with_one_party_and_with_none(page):
    assert spec(page, "DES_OUTCOME.out.info")["numbers"] == [["Share of the parties that walked in", "–"], ["Of them happy, every wait within its target", "–"]]
    run_until(page, "desEngine.departed === 1")
    assert spec(page, "DES_OUTCOME.out.info")["unit"] == "party so far"


def test_the_door_has_a_card_about_arrivals(page):
    assert dict(spec(page, "desArrivalsInfo")["numbers"])["Share turned away"] == "–"
    run(page, 120)
    card = spec(page, "desArrivalsInfo")
    assert page.evaluate("[desArrivalsInfo.kind, desArrivalsInfo.name]") == ["Start", "Parties arriving"]
    assert card["unit"] == "parties per minute walking in" and float(card["value"]) > 0 and dict(card["numbers"])["Came to the door"] > 10


# ---------- parties ----------

def test_a_party_has_one_card_for_as_long_as_it_is_inside(page):
    run(page, 30)
    assert page.evaluate("(() => { const id = [...desEngine.parties.keys()][0]; return desPartyInfo(id) === desPartyInfo(id) && desPartyInfo(id).kind; })()") == "Party"
    assert page.evaluate("desPartyInfo([...desEngine.parties.keys()][0]).name").startswith("Party ")


def test_a_party_of_one_is_one_guest(page):
    run_until(page, "[...desEngine.parties.values()].some(party => party.size === 1)")
    assert page.evaluate("desPartyInfo([...desEngine.parties.values()].find(party => party.size === 1).id).name").endswith(": 1 guest")


def test_a_partys_card_follows_its_visit(page):
    run_until(page, "[...desEngine.parties.values()].some(party => party.state === 'COOKING')")
    card = spec(page, "desPartyInfo([...desEngine.parties.values()].find(party => party.state === 'COOKING').id)")
    numbers = dict(card["numbers"])
    assert card["notes"][0].startswith("Now: Cooking (") and card["unit"] == "in the building so far" and card["verdict"][1] in ("good", "bad")
    assert numbers["Table"].startswith("Table ") and "×" in numbers["Ordered"] and any(label.startswith("Part of the order: ") for label in numbers)
    assert card["chartTitle"] == "Waits" and card["timelineTitle"] == "Visit on the clock"


def test_a_party_at_the_door_has_no_table_and_nothing_ordered(page):
    page.evaluate("for (let i = 0; i < 12; i++) desEngine.setOut('tables', i, true)")
    run_until(page, "desEngine.queues.host.length > 0")
    card = spec(page, "desPartyInfo(desEngine.queues.host[0])")
    numbers = dict(card["numbers"])
    assert numbers["Table"] == "None yet." and numbers["Ordered"] == "Nothing yet." and numbers["Holds now"] == "Nothing."
    assert card["notes"] == ["Now: Host queue."]
    run(page, 60)
    assert spec(page, "desPartyInfo(desEngine.queues.host[0])")["verdict"] == ["Not a happy visit", "bad"]


def test_a_party_waiting_to_order_counts_that_wait(page):
    page.evaluate("desEngine.changeCapacity('waiters', -1); desEngine.changeCapacity('waiters', -1)")
    run_until(page, "desEngine.queues.order.length > 0")
    run(page, 20)
    assert page.evaluate("(() => { const id = desEngine.queues.order[0], spec = metricsFor(desPartyInfo(id)); return spec.chart.querySelectorAll('text')[3].textContent; })()") != "0:00"


def test_plating_says_orders_when_more_than_one_is_held(page):
    page.evaluate("for (let i = 0; i < 4; i++) { desEngine.changeCapacity('waiters', 1); desEngine.changeCapacity('cooks', 1); }")
    run_until(page, "desHeldForParts().length >= 2")
    held = page.evaluate("desHeldForParts().length")
    assert f"Also held back: {held} orders waiting for other parts to be done." in spec(page, "DES_TASKS.plating.info")["notes"]
    run_until(page, "desHeldForParts().length === 1")
    assert "Also held back: 1 order waiting for other parts to be done." in spec(page, "DES_TASKS.plating.info")["notes"]
