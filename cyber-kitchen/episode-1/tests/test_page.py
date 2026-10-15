"""Browser tests for site/index.html, run in headless Chromium.

The `page` fixture loads the app with a seeded random generator and a frozen animation
loop, so each test advances the simulation itself by calling the page's own tick().
"""
import re

import pytest

from tests.conftest import PROJECT, SCREENSHOTS, open_page

HTML = (PROJECT / "site" / "index.html").read_text(encoding="utf-8")


# ---------- helpers ----------

def run(page, seconds, dt=0.05):
    """Advance the simulation by this many simulated seconds, then redraw."""
    page.evaluate("([n, dt]) => { for (let i = 0; i < n; i++) tick(dt); draw(); }", [round(seconds / dt), dt])


def run_until(page, condition, limit=900):
    """Advance until the JavaScript condition holds; fail if it never does."""
    reached = page.evaluate(
        f"() => {{ let n = 0; while (!({condition}) && n++ < {limit * 20}) tick(0.05); draw(); return !!({condition}); }}")
    assert reached, f"never reached: {condition}"


def click(page, expression):
    """Click an SVG or HTML element given as a JavaScript expression."""
    page.evaluate(f"({expression}).dispatchEvent(new MouseEvent('click', {{ bubbles: true }}))")


def card(page):
    """The about card as a dict, or None when nothing is selected."""
    return page.evaluate("""() => {
        const about = document.querySelector('.about');
        if (!about) return null;
        const rows = [...about.querySelectorAll('dt')].map(dt => [dt.textContent, dt.nextElementSibling.textContent]);
        return { kind: about.querySelector('.kind').textContent, name: about.querySelector('h3').textContent,
                 ...Object.fromEntries(rows) };
    }""")


def picker_groups(page):
    """Visible picker groups as {heading: [visible button names]}."""
    return page.evaluate("""() => Object.fromEntries([...document.querySelectorAll('#picker details')]
        .filter(group => !group.hidden)
        .map(group => [group.firstChild.textContent,
                       [...group.querySelectorAll('.actor')].filter(b => !b.hidden).map(b => b.textContent)]))""")


def seat_everyone(page, count=12):
    """Fill the room: spawn parties until `count` tables are taken, then let them sit down."""
    page.evaluate(f"() => {{ let n = 0; while (tables.filter(t => t.status !== 'free').length < {count} && n++ < 500) spawnParty(); }}")


# ---------- page structure ----------

def test_title_and_heading(page):
    assert page.title() == "Semantic Works: Cyber Kitchen"
    assert page.locator("h1").inner_text() == "Semantic Works: Cyber Kitchen"


def test_page_loads_nothing_from_the_internet(page):
    resources = page.evaluate("performance.getEntriesByType('resource').map(r => r.name)")
    origin = page.evaluate("location.origin")
    assert all(name.startswith(origin) for name in resources)
    assert not re.search(r"<(script|link|img)[^>]+(src|href)=\"(?!data:)", HTML)
    assert "@import" not in HTML


def test_twelve_tables_four_round_two_small_six_large(page):
    assert page.evaluate("tables.map(t => t.type + t.capacity).sort()") == ["round4"] * 4 + ["six6"] * 6 + ["two2"] * 2
    assert page.locator("#furniture .table").count() == 12
    assert page.locator("#furniture .seat").count() == 4 * 4 + 6 * 6 + 2 * 2


def test_two_waiters_two_cooks_and_kitchen_equipment(page):
    assert page.evaluate("waiters.map(w => w.name)") == ["Waiter 1", "Waiter 2"]
    assert page.evaluate("cooks.map(c => c.name)") == ["Cook 1", "Cook 2"]
    assert page.evaluate("cooks.map(c => c.stove.name)") == ["stove 1", "stove 2"]
    labels = page.locator("#furniture .small-label").all_text_contents()
    for label in ["ORDER RAIL", "PASS", "PREP COUNTER", "SINK", "FRIDGE", "STOVES", "PIZZA OVEN", "COFFEE"]:
        assert label in labels


def test_starts_empty_with_all_counters_at_zero(page):
    page.evaluate("draw()")
    assert page.locator(".stat .value").all_inner_texts() == ["0:00", "0", "0", "0", "0", "0", "0", "0"]
    assert page.evaluate("tables.every(t => t.status === 'free')")
    assert page.evaluate("tables[0].title.textContent") == "Table 1 (seats 6): free"


def test_page_uses_the_full_window_width(page):
    box = page.locator("main").bounding_box()
    assert box["x"] == 0 and box["width"] == 1400
    view = page.locator(".view-card").bounding_box()
    assert view["width"] == 1400 - 32


def test_opening_the_panel_narrows_the_view_but_keeps_its_height(page):
    before = page.locator(".view-card").bounding_box()
    page.click("#panel-toggle")
    page.wait_for_timeout(400)
    after = page.locator(".view-card").bounding_box()
    panel = page.locator(".panel-inner").bounding_box()
    assert after["height"] == before["height"] == panel["height"]
    assert after["width"] == before["width"] - 340 - 12
    assert round(panel["x"] + panel["width"]) == 1400 - 16
    stats = page.locator(".stats").bounding_box()
    assert stats["y"] > before["y"] + before["height"]


def test_narrow_screens_stack_the_panel_under_the_view(browser, site_server):
    page, finish = open_page(browser, site_server[0], width=600, height=900)
    page.click("#panel-toggle")
    view, panel = page.locator(".view-card").bounding_box(), page.locator(".panel-inner").bounding_box()
    assert panel["y"] >= view["y"] + view["height"]
    assert panel["width"] == view["width"]
    finish()


# ---------- small helpers inside the page ----------

def test_move_toward_steps_and_arrives(page):
    assert page.evaluate("(() => { const o = {x: 0, y: 0}; return [moveToward(o, 10, 0, 4), o]; })()") == [False, {"x": 4, "y": 0}]
    assert page.evaluate("(() => { const o = {x: 0, y: 0}; return [moveToward(o, 3, 4, 5), o]; })()") == [True, {"x": 3, "y": 4}]
    assert page.evaluate("(() => { const o = {x: 7, y: 7}; return [moveToward(o, 7, 7, 0), o]; })()") == [True, {"x": 7, "y": 7}]


def test_path_length_and_point_along_a_path(page):
    path = "[{x: 0, y: 0}, {x: 10, y: 0}, {x: 10, y: 0}, {x: 10, y: 5}]"
    assert page.evaluate(f"pathLength({path})") == 15
    assert page.evaluate(f"pointAt({path}, 4)") == {"x": 4, "y": 0}
    assert page.evaluate(f"pointAt({path}, 12)") == {"x": 10, "y": 2}
    assert page.evaluate(f"pointAt({path}, 99)") == {"x": 10, "y": 5}


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


def test_party_sizes_follow_the_weights(page):
    sizes = page.evaluate("""() => {
        const real = Math.random, out = [];
        for (const r of [0, 0.1, 0.4, 0.6, 0.8, 0.99, 2]) { Math.random = () => r; out.push(pickSize()); }
        Math.random = real;
        return out;
    }""")
    assert sizes == [1, 2, 3, 4, 5, 6, 2]


def test_clock_text(page):
    assert page.evaluate("[clockText(0), clockText(9.9), clockText(75), clockText(600)]") == ["0:00", "0:09", "1:15", "10:00"]


# ---------- seating ----------

def test_a_party_gets_the_smallest_table_that_fits(page):
    assert page.evaluate("[1, 2, 3, 4, 5, 6].map(size => findTable(size).capacity)") == [2, 2, 4, 4, 6, 6]
    page.evaluate("tables.filter(t => t.capacity === 2).forEach(t => setStatus(t, 'eating'))")
    assert page.evaluate("findTable(2).capacity") == 4
    page.evaluate("tables.forEach(t => setStatus(t, 'eating'))")
    assert page.evaluate("findTable(1)") is None


def test_guests_walk_in_sit_down_and_read_the_menu(page):
    page.evaluate("spawnParty()")
    assert page.evaluate("[parties.length, parties[0].state, parties[0].table.status]") == [1, "arriving", "reserved"]
    assert page.locator("#guests .guest").count() == page.evaluate("parties[0].size")
    run_until(page, "parties[0].state === 'seated'")
    assert page.evaluate("parties[0].table.status") == "reading"
    run(page, 3)
    assert page.evaluate("parties[0].members.every((m, i) => m.x === parties[0].table.seats[i].x && m.y === parties[0].table.seats[i].y)")
    run_until(page, "parties[0].table.status === 'ready'")
    assert page.locator(".table.ready .bubble").count() == 1


def test_parties_queue_at_the_door_and_are_turned_away_when_it_is_full(page):
    seat_everyone(page)
    assert page.evaluate("tables.every(t => t.status === 'reserved')")
    page.evaluate("nextArrival = 1e9")
    queued_before = page.evaluate("parties.filter(p => p.state === 'queue').length")
    page.evaluate("() => { const real = Math.random; Math.random = () => 0.99; for (let i = 0; i < 5; i++) spawnParty(); Math.random = real; }")
    assert page.evaluate("parties.filter(p => p.state === 'queue').length") == 3
    assert page.evaluate("turnedAway") == 5 - (3 - queued_before)
    run(page, 4)
    assert page.evaluate("parties.filter(p => p.state === 'queue').every(p => p.members[0].x === 18)")
    assert page.locator("#s-queue").inner_text() == "3"
    assert int(page.locator("#s-lost").inner_text()) >= 2
    # a six-top frees up: the first party in the queue takes it
    page.evaluate("() => { const t = tables.find(t => t.capacity === 6); parties.splice(parties.indexOf(t.party), 1)[0].members.forEach(m => m.el.remove()); t.party = null; setStatus(t, 'free'); }")
    run(page, 0.1)
    assert page.evaluate("parties.filter(p => p.state === 'queue').length") == 2


# ---------- the full service cycle ----------

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
    assert page.evaluate("delivered.length") == 10


def test_counters_match_the_simulation(page):
    run(page, 120)
    expected = page.evaluate("""[
        parties.filter(p => p.state !== 'queue').reduce((sum, p) => sum + p.size, 0),
        parties.filter(p => p.state === 'queue').length, rail.length,
        cooks.filter(c => ['toStation', 'working', 'waitStation'].includes(c.state)).length, pass.length, served, turnedAway]""")
    assert page.locator(".stat .value").all_inner_texts()[1:] == [str(n) for n in expected]


def test_table_colour_classes_and_plates_follow_the_status(page):
    run_until(page, "tables.some(t => t.status === 'eating')")
    table = "tables.find(t => t.status === 'eating')"
    assert page.evaluate(f"{table}.g.getAttribute('class')") == "table eating"
    assert page.evaluate(f"{table}.plates.filter(p => p.classList.contains('on')).length === {table}.party.size")
    assert page.evaluate(f"/^Table \\d+ \\(seats \\d\\): eating$/.test({table}.title.textContent)")
    page.evaluate("window.eaten = tables.find(t => t.status === 'eating')")
    run_until(page, "eaten.status === 'free'")
    assert page.evaluate("eaten.plates.every(p => !p.classList.contains('on')) && eaten.party === null")


def test_a_ticket_travels_from_table_to_rail_to_cook_to_pass_and_back(page):
    run_until(page, "tickets.length > 0")
    page.evaluate("window.first = tickets[0]; window.stages = [first.stage]")
    page.evaluate("""() => { let n = 0; while (first.stage !== 'done' && n++ < 8000) {
        tick(0.05); if (stages.at(-1) !== first.stage) stages.push(first.stage); } draw(); }""")
    assert page.evaluate("stages") == ["carried", "rail", "cooking", "pass", "delivering", "done"]
    assert page.evaluate("first.delivered > first.created && delivered[0] === first && !tickets.includes(first)")
    assert page.evaluate("first.table.status") == "eating"
    assert page.evaluate("first.stove + first.oven === first.table.party.size")


def test_cooks_use_stove_oven_and_coffee_machine_as_the_ticket_says(page):
    steps = page.evaluate("""[
        stepsFor(cooks[0], { stove: 2, oven: 0, coffee: 0 }), stepsFor(cooks[1], { stove: 0, oven: 3, coffee: 0 }),
        stepsFor(cooks[1], { stove: 1, oven: 1, coffee: 2 })].map(steps => steps.map(s => [s.station.name, s.time]))""")
    assert steps == [[["stove 1", 6.6]], [["the pizza oven", 7]],
                     [["stove 2", 5.3], ["the pizza oven", 5], ["the coffee machine", 2]]]


def test_a_cook_waits_when_the_shared_oven_is_busy(page):
    run_until(page, "cooks[0].state === 'grabbing'")
    page.evaluate("cooks[0].job.stove = 0; cooks[0].job.oven = 2; cooks[0].job.coffee = 0; pizzaOven.busy = true")
    run_until(page, "cooks[0].state === 'waitStation'")
    assert page.evaluate("staffNow(cooks[0])").startswith("Waiting for the pizza oven to be free (order for table ")
    run(page, 2)
    assert page.evaluate("cooks[0].state") == "waitStation"
    page.evaluate("pizzaOven.busy = false")
    run_until(page, "cooks[0].state === 'working'")
    assert page.evaluate("[cooks[0].station === pizzaOven, pizzaOven.on, pizzaOven.busy, cooks[0].carry]") == [True, True, True, "ticket"]
    assert page.evaluate("staffNow(cooks[0])").startswith("Baking pizza for table ")
    run(page, 1)
    assert page.evaluate("pizzaOven.progress > 0 && Number(pizzaOven.bar.getAttribute('width')) > 0 && Number(pizzaOven.flame.style.opacity) > 0")
    run_until(page, "cooks[0].state === 'toPass'")
    assert page.evaluate("[pizzaOven.on, pizzaOven.busy, pizzaOven.progress, cooks[0].carry]") == [False, False, 0, "plates"]


def test_rail_and_pass_show_tickets_and_overflow(page):
    seat_everyone(page, 8)
    page.evaluate("nextArrival = 1e9; cooks.splice(0)")   # no cooks: tickets pile up on the rail
    run_until(page, "rail.length === 8")
    assert page.locator("#rail [data-selectable]").count() == 5
    assert page.locator("#rail .small-label").text_content() == "+3"
    assert page.locator("#s-rail").inner_text() == "8"
    page.evaluate("waiters.splice(0); rail.splice(0).forEach(t => { pass.push(t); moveTicket(t, 'pass'); }); draw()")
    assert page.locator("#rail [data-selectable]").count() == 0
    assert page.locator("#pass [data-selectable]").count() == 6
    assert page.locator("#s-pass").inner_text() == "8"


# ---------- controls ----------

def test_frame_advances_time_and_caps_long_gaps(page):
    page.evaluate("__frame(last + 50)")
    assert page.evaluate("clock") == pytest.approx(0.05)
    page.evaluate("__frame(last + 5000)")
    assert page.evaluate("clock") == pytest.approx(0.15)


def test_pause_button_stops_and_resumes_time(page):
    page.click("#pause")
    assert page.locator("#pause").inner_text() == "Resume"
    assert page.locator("#pause").get_attribute("aria-pressed") == "true"
    page.evaluate("__frame(last + 50)")
    assert page.evaluate("clock") == 0
    page.click("#pause")
    assert page.locator("#pause").inner_text() == "Pause"
    page.evaluate("__frame(last + 50)")
    assert page.evaluate("clock") == pytest.approx(0.05)


def test_speed_buttons_run_time_faster(page):
    page.click(".speed[data-speed='4']")
    assert page.locator(".speed[aria-pressed='true']").inner_text() == "4×"
    page.evaluate("__frame(last + 50)")
    assert page.evaluate("clock") == pytest.approx(0.2)
    page.click(".speed[data-speed='2']")
    page.evaluate("__frame(last + 50)")
    assert page.evaluate("clock") == pytest.approx(0.3)
    assert page.locator(".speed[aria-pressed='true']").count() == 1


def test_details_button_and_close_button_toggle_the_panel(page):
    toggle = page.locator("#panel-toggle")
    assert toggle.inner_text() == "Show details" and not page.evaluate("$('panel').classList.contains('open')")
    toggle.click()
    assert toggle.inner_text() == "Hide details" and toggle.get_attribute("aria-pressed") == "true"
    assert "Nothing selected" in page.locator("#about .empty").inner_text()
    toggle.click()
    assert toggle.inner_text() == "Show details"
    toggle.click()
    page.click("#panel-close")
    assert not page.evaluate("$('panel').classList.contains('open')")


# ---------- selection and about cards ----------

def test_every_fixed_object_can_be_selected_and_shows_one_card(page):
    names = page.evaluate("fixedObjects.map(o => o.name)")
    assert names[:3] == ["Front door", "Order rail", "Pass table"]
    assert set(names[3:10]) == {"Prep counter", "Sink", "Fridge", "Stove 1", "Stove 2", "Pizza oven", "Coffee machine"}
    assert names[10:] == [f"Table {n}" for n in range(1, 13)]
    for index, name in enumerate(names):
        click(page, f"fixedObjects[{index}].nodes[0]")
        shown = card(page)
        assert shown["name"] == name
        assert all(shown[field] for field in ("kind", "What it is", "Purpose", "Why it is here", "Right now"))
        assert page.locator(".about").count() == 1
        assert page.evaluate(f"document.querySelectorAll('[data-selected]').length === 1 && fixedObjects[{index}].nodes[0].hasAttribute('data-selected')")
    assert page.evaluate("$('panel').classList.contains('open')")


def test_clicking_the_floor_clears_the_selection_but_leaves_the_panel_open(page):
    click(page, "tables[0].g")
    assert card(page)["name"] == "Table 1"
    click(page, "$('view')")
    assert card(page) is None
    assert page.locator("[data-selected]").count() == 0
    assert "Nothing selected" in page.locator("#about .empty").inner_text()
    assert page.evaluate("$('panel').classList.contains('open')")


def test_equipment_cards(page):
    click(page, "fixedObjects.find(o => o.name === 'Fridge').nodes[0]")
    assert card(page)["Right now"] == "Drawn for context. It is not part of the simulation yet."
    click(page, "fixedObjects.find(o => o.name === 'Stove 1').nodes[0]")
    assert card(page)["kind"] == "Kitchen equipment" and card(page)["Right now"] == "Idle."
    page.evaluate("stoves[0].busy = true; stoves[0].table = tables[4]; updateNow()")
    assert card(page)["Right now"] == "A cook is on the way to use it."
    page.evaluate("stoves[0].on = true; updateNow()")
    assert card(page)["Right now"] == "In use for table 5's order."


def test_door_rail_and_pass_cards_count_what_is_waiting(page):
    click(page, "fixedObjects[0].nodes[0]")
    assert card(page)["Right now"] == "0 parties waiting outside. 0 turned away so far."
    page.evaluate("tables.forEach(t => setStatus(t, 'eating')); spawnParty(); updateNow()")
    assert card(page)["Right now"] == "1 party waiting outside. 0 turned away so far."
    page.evaluate("parties.splice(0).forEach(p => p.members.forEach(m => m.el.remove())); tables.forEach(t => setStatus(t, 'free'))")

    seat_everyone(page, 3)
    page.evaluate("nextArrival = 1e9; cooks.splice(0)")
    click(page, "fixedObjects[1].nodes[0]")
    assert card(page)["Right now"] == "No tickets waiting."
    run_until(page, "rail.length === 1")
    assert re.fullmatch(r"1 ticket waiting, for table \d+\.", card(page)["Right now"])
    run_until(page, "rail.length === 3")
    assert re.fullmatch(r"3 tickets waiting, for table \d+, table \d+, table \d+\.", card(page)["Right now"])

    click(page, "fixedObjects[2].nodes[0]")
    assert card(page)["Right now"] == "Empty."
    page.evaluate("waiters.splice(0); pass.push(rail.shift()); updateNow()")
    assert re.fullmatch(r"1 order ready, for table \d+\.", card(page)["Right now"])
    page.evaluate("pass.push(rail.shift()); updateNow()")
    assert re.fullmatch(r"2 orders ready, for table \d+, table \d+\.", card(page)["Right now"])


def test_table_card_follows_the_party_and_its_order(page):
    page.evaluate("spawnParty(); window.t = parties[0].table")
    click(page, "t.g")
    shown = card(page)
    assert shown["kind"] == "Table" and shown["Order at this table"] == "Not ordered yet."
    assert re.fullmatch(r"Party of \d: guests arriving\.", shown["Right now"])
    assert re.fullmatch(r"A (rectangular|round|small square) table that seats \d\.", shown["What it is"])
    run_until(page, "t.status === 'waiting'")
    assert re.fullmatch(r"(\d × [A-Za-z ]+\n?)+", card(page)["Order at this table"])
    assert card(page)["Order at this table"] == page.evaluate("t.party.ticket.lines")
    run_until(page, "t.status === 'free'")
    assert card(page)["Order at this table"] == "Nobody is sitting here."
    assert card(page)["Right now"] == "Free."
    assert page.evaluate("t.g.hasAttribute('data-selected') && t.g.getAttribute('class') === 'table free'")


def test_party_card_follows_the_party_until_it_leaves(page):
    page.evaluate("tables.forEach(t => setStatus(t, 'eating')); spawnParty(); window.p = parties[0]")
    click(page, "p.members[0].el")
    shown = card(page)
    assert shown["kind"] == "Guests" and shown["Right now"] == "Waiting outside for a table that fits."
    assert shown["What they ordered"] == "Nothing yet."
    assert page.locator("#guests [data-selected]").count() == page.evaluate("p.size")
    page.evaluate("tables.forEach(t => setStatus(t, 'free'))")
    run(page, 0.1)
    assert re.fullmatch(r"Walking to table \d+\.", card(page)["Right now"])
    run_until(page, "p.state === 'seated'")
    assert re.fullmatch(r"At table \d+: reading the menu\.", card(page)["Right now"])
    run_until(page, "p.table.status === 'eating'")
    assert card(page)["What they ordered"] == page.evaluate("p.ticket.lines")
    run_until(page, "p.state === 'leaving'")
    assert card(page)["Right now"] == "Leaving after the meal."
    run_until(page, "!parties.includes(p)")
    assert card(page) is None
    assert page.locator("#guests .guest").count() == page.evaluate("parties.reduce((sum, p) => sum + p.size, 0)")


def test_party_names_for_one_guest_and_for_groups(page):
    names = page.evaluate("""() => {
        const real = Math.random, out = [];
        for (const r of [0, 0.8]) { Math.random = () => r; spawnParty(); const info = parties.at(-1).info; out.push(info.name, info.listName, info.what); }
        Math.random = real;
        return out;
    }""")
    assert names == ["Party 1: 1 guest", "Party 1", "One customer.",
                     "Party 2: 5 guests", "Party 2", "5 customers who came together and share a table."]


def test_staff_card_describes_every_activity(page):
    click(page, "waiters[0].g")
    shown = card(page)
    assert shown["kind"] == "Waiter" and shown["name"] == "Waiter 1" and shown["Right now"] == "Waiting for something to do."
    click(page, "cooks[1].g")
    assert card(page)["kind"] == "Cook" and card(page)["name"] == "Cook 2"
    assert page.evaluate("waiters[0].g.hasAttribute('data-selected')") is False
    texts = page.evaluate("""() => {
        const job = { table: tables[6] }, station = pizzaOven, out = {};
        const say = (kind, state, extra) => out[kind + ':' + state] = staffNow({ kind, state, job, path: [], station, steps: [{ station: coffeeMachine }], ...extra });
        for (const state of ['toTable', 'taking', 'toRail', 'hanging', 'toPass', 'picking', 'toServe', 'serving', 'mystery']) say('waiter', state);
        for (const state of ['toRail', 'grabbing', 'waitStation', 'toStation', 'working', 'toPass', 'plating']) say('cook', state);
        say('waiter', 'idle', { job: null, path: [{ x: 1, y: 1 }] });
        return out;
    }""")
    assert texts == {
        "waiter:toTable": "Walking to table 7 to take the order.",
        "waiter:taking": "Taking the order at table 7.",
        "waiter:toRail": "Carrying the ticket for table 7 to the order rail.",
        "waiter:hanging": "Hanging the ticket for table 7 on the order rail.",
        "waiter:toPass": "Going to the pass for the food for table 7.",
        "waiter:picking": "Collecting the food for table 7 from the pass.",
        "waiter:toServe": "Carrying food to table 7.",
        "waiter:serving": "Serving table 7.",
        "waiter:mystery": "",
        "waiter:idle": "Walking back to the waiting spot.",
        "cook:toRail": "Going to the rail for the ticket for table 7.",
        "cook:grabbing": "Taking the ticket for table 7 off the rail.",
        "cook:waitStation": "Waiting for the coffee machine to be free (order for table 7).",
        "cook:toStation": "Taking the order for table 7 to the pizza oven.",
        "cook:working": "Baking pizza for table 7 at the pizza oven.",
        "cook:toPass": "Carrying the plates for table 7 to the pass.",
        "cook:plating": "Putting the plates for table 7 on the pass.",
    }


def test_about_card_updates_live_while_the_object_works(page):
    click(page, "waiters[0].g")
    run_until(page, "waiters[0].state === 'taking'")
    assert re.fullmatch(r"Taking the order at table \d+\.", card(page)["Right now"])


def test_ticket_card_shows_the_order_and_follows_the_ticket(page):
    page.evaluate("() => { const real = Math.random; Math.random = () => 0; spawnParty(); Math.random = real; }")
    run_until(page, "rail.length === 1")
    page.evaluate("window.ticket = rail[0]; draw()")
    click(page, "document.querySelector('#rail [data-selectable]')")
    shown = card(page)
    assert shown["kind"] == "Order ticket" and re.fullmatch(r"Ticket 1 for table \d+", shown["name"])
    assert re.fullmatch(r"A paper slip with the order from table \d+ \(1 guest\), written by Waiter \d at \d:\d\d\.", shown["What it is"])
    assert shown["On the ticket"] == page.evaluate("ticket.lines")
    assert re.fullmatch(r"1 × [A-Za-z ]+(\n1 × Coffee)?", shown["On the ticket"])
    assert re.fullmatch(r"Hanging on the order rail for 0:0\d, waiting for a cook\.", shown["Right now"])
    assert page.locator("#rail [data-selected]").count() == 1

    run_until(page, "ticket.stage === 'cooking'")
    assert re.fullmatch(r"Cook \d has it and is preparing the order \(0:\d\d so far\)\.", card(page)["Right now"])
    assert page.locator("[data-selected]").count() == 0   # the paper is in the cook's hand now
    run_until(page, "ticket.stage === 'pass'")
    assert re.fullmatch(r"The food is on the pass, waiting 0:\d\d for a waiter\.", card(page)["Right now"])
    assert page.locator("#pass [data-selected]").count() == 1
    run_until(page, "ticket.stage === 'delivering'")
    assert re.fullmatch(r"Waiter \d is carrying the food to table \d+\.", card(page)["Right now"])
    run_until(page, "ticket.stage === 'done'")
    total = card(page)["Time since the order was taken"]
    assert re.fullmatch(rf"Delivered\. Table \d+ got its food {total} after ordering\.", card(page)["Right now"])
    run(page, 5)
    assert card(page)["Time since the order was taken"] == total   # the clock on a delivered ticket stops


def test_ticket_in_a_waiters_hand_and_plate_on_the_pass(page):
    seat_everyone(page, 3)
    run_until(page, "tickets.length === 1")
    assert re.fullmatch(r"Waiter \d is carrying it to the order rail\.", page.evaluate("tickets[0].info.now()"))
    assert re.search(r"\(\d guests\)", page.evaluate("tickets[0].info.what"))
    run_until(page, "pass.length === 1")
    page.evaluate("draw()")
    click(page, "document.querySelector('#pass [data-selectable]')")
    assert card(page)["kind"] == "Order ticket"
    click(page, "tables[0].g")
    assert page.locator("#pass [data-selected]").count() == 0


# ---------- the picker ----------

def test_picker_opens_from_the_magnifying_glass_and_lists_everything(page):
    assert page.locator("#picker").is_hidden()
    assert page.locator("#panel .actor").count() == 0
    page.click("#picker-toggle")
    assert page.locator("#picker").is_visible()
    assert page.locator("#picker-toggle").get_attribute("aria-expanded") == "true"
    assert page.evaluate("document.activeElement.id") == "picker-filter"
    groups = picker_groups(page)
    assert list(groups) == ["Order tickets, open (0)", "Order tickets, delivered (last 10) (0)", "Waiters (2)", "Cooks (2)",
                            "Guest parties (0)", "Tables (12)", "Hand-off points (3)", "Kitchen equipment (7)"]
    assert groups["Waiters (2)"] == ["Waiter 1", "Waiter 2"]
    assert groups["Tables (12)"] == [f"Table {n}" for n in range(1, 13)]
    assert groups["Hand-off points (3)"] == ["Front door", "Order rail", "Pass table"]
    assert page.locator("#picker .none").all_text_contents() == ["No open orders.", "Nothing delivered yet.", "No guests at the moment."]
    assert page.evaluate("[...document.querySelectorAll('#picker details')].map(d => d.open)") == [True, False] + [True] * 6


def test_picker_buttons_are_plain_names_only(page):
    run(page, 60)
    page.click("#picker-toggle")
    assert page.evaluate("[...document.querySelectorAll('#picker .actor')].every(b => b.children.length === 0 && /^[A-Z][A-Za-z]+( [a-z]+)?( \\d+)?$/.test(b.textContent))")


def test_picking_a_name_selects_it_closes_the_picker_and_shows_its_card(page):
    page.click("#picker-toggle")
    page.click("#picker .actor:text-is('Pizza oven')")
    assert page.locator("#picker").is_hidden()
    assert page.locator("#picker-toggle").get_attribute("aria-expanded") == "false"
    assert card(page)["name"] == "Pizza oven"
    assert page.evaluate("$('panel').classList.contains('open') && fixedObjects.find(o => o.name === 'Pizza oven').nodes[0].hasAttribute('data-selected')")
    page.click("#picker-toggle")
    assert page.locator("#picker .actor[aria-pressed='true']").all_inner_texts() == ["Pizza oven"]


def test_picker_lists_parties_and_tickets_as_they_come_and_go(page):
    page.click("#picker-toggle")
    page.evaluate("() => { const real = Math.random; Math.random = () => 0; spawnParty(); Math.random = real; nextArrival = 1e9; }")
    page.evaluate("__frame(last + 1000)")
    groups = picker_groups(page)
    assert groups["Guest parties (1)"] == ["Party 1"]
    assert "No guests at the moment." not in page.locator("#picker .none").all_text_contents()
    run_until(page, "tickets.length === 1")
    page.evaluate("updateActorList()")
    assert picker_groups(page)["Order tickets, open (1)"] == ["Ticket 1"]
    run_until(page, "delivered.length === 1")
    page.evaluate("updateActorList()")
    groups = picker_groups(page)
    assert groups["Order tickets, open (0)"] == [] and groups["Order tickets, delivered (last 10) (1)"] == ["Ticket 1"]
    assert "No open orders." in page.locator("#picker .none").all_text_contents()
    run_until(page, "parties.length === 0")
    page.evaluate("updateActorList()")
    assert picker_groups(page)["Guest parties (0)"] == []
    page.evaluate("document.querySelector('#picker details:nth-of-type(2)').open = true")
    page.click("#picker .actor:text-is('Ticket 1')")
    assert card(page)["kind"] == "Order ticket"


def test_picker_filter_narrows_the_list(page):
    page.click("#picker-toggle")
    page.fill("#picker-filter", "cook")
    assert picker_groups(page) == {"Cooks (2)": ["Cook 1", "Cook 2"]}
    page.fill("#picker-filter", "TABLE 1")
    assert picker_groups(page) == {"Tables (12)": ["Table 1", "Table 10", "Table 11", "Table 12"]}
    page.fill("#picker-filter", "zzz")
    assert picker_groups(page) == {}
    page.fill("#picker-filter", "")
    assert len(picker_groups(page)) == 8
    page.fill("#picker-filter", "sink")
    page.click("#picker-toggle")
    page.click("#picker-toggle")
    assert page.input_value("#picker-filter") == "" and len(picker_groups(page)) == 8   # reopening clears the filter


def test_picker_closes_on_escape_outside_click_or_its_own_button(page):
    toggle, picker = page.locator("#picker-toggle"), page.locator("#picker")
    toggle.click()
    page.keyboard.press("a")
    page.click("#picker h3")
    assert picker.is_visible()
    page.keyboard.press("Escape")
    assert picker.is_hidden()
    toggle.click()
    page.click("h1")
    assert picker.is_hidden()
    toggle.click()
    toggle.click()
    assert picker.is_hidden()
    toggle.click()
    click(page, "tables[2].g")
    assert picker.is_hidden() and card(page)["name"] == "Table 3"


def test_picker_is_not_refreshed_while_hidden(page):
    run(page, 30)
    page.evaluate("__frame(last + 1000)")
    assert page.locator("#picker .actor").count() == 0


# ---------- live reload ----------

def test_page_reloads_itself_when_a_site_file_changes(browser, site_server):
    url, root = site_server
    page, finish = open_page(browser, url, init_script=None)
    page.evaluate("window.loadedBefore = true")
    page.wait_for_timeout(300)
    index = root / "index.html"
    with page.expect_navigation(timeout=10_000):
        index.write_text(index.read_text(encoding="utf-8") + "\n<!-- touched by test -->", encoding="utf-8")
    assert page.evaluate("typeof window.loadedBefore") == "undefined"
    assert page.title() == "Semantic Works: Cyber Kitchen"
    page.wait_for_timeout(300)   # let the real animation loop run a few frames
    assert page.evaluate("clock") > 0
    finish()


# ---------- screenshots ----------
# Each run rewrites tests/screenshots/*.png. They are meant to be checked in, so a later
# change to the look of the page shows up as a changed image in version control.

def snap(page, name):
    path = SCREENSHOTS.directory / f"{name}.png"
    before = path.read_bytes() if path.exists() else None
    page.evaluate("draw()")
    page.screenshot(path=str(path), full_page=True, animations="disabled")
    SCREENSHOTS.results.append((path.name, "new" if before is None else "unchanged" if before == path.read_bytes() else "CHANGED"))
    assert path.stat().st_size > 10_000


def test_screenshots_of_the_empty_restaurant(page):
    snap(page, "01-empty-panel-closed")
    page.click("#panel-toggle")
    snap(page, "02-empty-panel-open")
    page.click("#picker-toggle")
    snap(page, "03-empty-picker-open")


def test_screenshots_of_a_known_busy_moment(page):
    run(page, 150.5)   # seeded random + fixed steps: always the same moment, 2:30 into service
    assert page.locator("#s-clock").inner_text() == "2:30"
    snap(page, "04-busy-panel-closed")
    click(page, "tables[2].g")
    snap(page, "05-busy-table-selected")
    click(page, "cooks[0].g")
    snap(page, "06-busy-cook-selected")
    page.click("#picker-toggle")
    snap(page, "07-busy-picker-open")
