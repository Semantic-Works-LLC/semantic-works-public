"""js/des-view.js: the Floor Plan, the restaurant as a place."""
import pytest

from tests.support import about, click, run, run_until, settle


def labels(page):
    return page.evaluate("[...document.querySelectorAll('#desview text')].map(node => node.textContent).filter(label => /[A-Z]{3}/.test(label))")


def test_only_the_room_is_drawn(page):
    assert labels(page) == ["DINING ROOM", "KITCHEN", "WAITING", "AREA", "TICKET", "RAIL", "PASS", "TABLE", "STOVES", "PIZZA OVEN", "COFFEE"]
    assert page.evaluate("$('des-static').children.length") == 0, "no meters, outcomes, figures or notes beside the room"
    assert not any(word in " ".join(labels(page)) for word in ["DOOR", "PREP", "SINK", "FRIDGE", "PHYSICAL", "UTILIZATION", "OUTCOMES"])


def test_twelve_numbered_tables_with_their_seats(page):
    assert page.evaluate("desFloorTables.map(table => table.g.querySelector('.table-num').textContent)") == [str(n) for n in range(1, 13)]
    assert page.evaluate("desFloorTables.map(table => table.g.querySelectorAll('.seat').length)") == page.evaluate("DES_CONFIG.tables")
    shapes = page.evaluate("desFloorTables.slice(0, 4).map(table => table.g.querySelector('.table-top').tagName)")
    assert shapes == ["rect", "rect", "circle", "rect"]


def test_a_table_is_coloured_by_what_its_party_is_doing(page):
    assert page.evaluate("desFloorTables.every(table => table.g.getAttribute('class') === 'table free')")
    for state, name in [("READING_MENU", "reading"), ("WAITING_FOR_WAITER_ORDER", "ready"), ("ORDERING", "ordering"), ("COOKING", "waiting"), ("EATING_AND_BILLING", "eating")]:
        run_until(page, f"[...desEngine.parties.values()].some(party => party.state === '{state}')")
        table = page.evaluate(f"[...desEngine.parties.values()].find(party => party.state === '{state}').table")
        assert page.evaluate(f"desFloorTables[{table}].g.getAttribute('class')") == f"table {name}"
    assert page.evaluate("Object.keys(DES_TABLE_CLASS).length") >= 10


def test_guests_sit_at_their_table_and_are_all_the_same_grey(page):
    run(page, 60)
    assert page.evaluate("""[...desEngine.parties.values()].filter(party => party.table !== null).every(party => Array.from({ length: party.size }, (_, k) => desTokens.get(`${party.id}:${k}`))
        .every((token, k) => Math.hypot(token.x - tables[party.table].seats[k].x, token.y - tables[party.table].seats[k].y) < 1))""")
    assert set(page.evaluate("[...document.querySelectorAll('#des-floor-tokens .guest')].map(guest => guest.getAttribute('fill'))")) == {"#b9bcc0"}


def test_a_new_party_walks_in_from_outside_and_a_leaving_one_walks_out(page):
    page.evaluate("for (let i = 0; i < 20; i++) tick(0.05); drawDes()")
    run_until(page, "desEngine.arrived === 2")
    page.evaluate("__advance(16); drawDes()")
    newcomer = page.evaluate("(() => { const id = [...desEngine.parties.keys()].at(-1), token = desTokens.get(id + ':0'); return [token.x, token.tx]; })()")
    assert newcomer[0] < newcomer[1], "still on its way in from the door"
    run_until(page, "desEngine.departed === 1")
    assert page.evaluate("[...desTokens.values()].every(token => token.live || token.home)")


def test_parties_wait_in_the_waiting_area_outside_and_it_selects_the_host_queue(page):
    page.evaluate("for (let i = 0; i < 12; i++) desEngine.setOut('tables', i, true)")
    run_until(page, "desEngine.queues.host.length === 3")
    area = page.evaluate("(() => { const b = DES_QUEUE.host.info.nodes[0].querySelector('.des-rail').getBBox(); return [b.x, b.y, b.x + b.width, b.y + b.height]; })()")
    spots = page.evaluate("desEngine.queues.host.flatMap(id => Array.from({ length: desEngine.parties.get(id).size }, (_, k) => { const t = desTokens.get(`${id}:${k}`); return [t.x, t.y]; }))")
    assert all(area[0] < x - 10 and x + 10 < area[2] and area[1] < y - 10 and y + 10 < area[3] for x, y in spots), "every waiting guest stands inside the outline"
    assert area[2] <= 60, "the area is outside the dining room wall, right against it"
    look = page.evaluate("(() => { const r = DES_QUEUE.host.info.nodes[0].querySelector('.des-rail'), s = getComputedStyle(r); return [s.strokeDasharray, r.getAttribute('rx')]; })()")
    assert look == ["none", None], "a plain rectangle: no dashes, square corners"
    inside = page.evaluate("[...DES_QUEUE.host.info.nodes[0].querySelectorAll('text')].every(label => { const b = label.getBBox(); return b.x > -6 && b.x + b.width < 60 && b.y > 308 && b.y + b.height < 582; })")
    assert inside, "its name is written inside it"
    click(page, "DES_QUEUE.host.info.nodes[0].querySelector('.des-rail')")
    assert about(page)["name"] == "Host queue"


def test_the_door_is_drawn_open_to_the_outside(page):
    paths = page.evaluate("[...DES_QUEUE.host.info.nodes[0].querySelectorAll('path')].map(path => path.getAttribute('d'))")
    assert paths[1].startswith("M60 245 L") and float(paths[1].split("L")[1].split()[0]) < 60, "the leaf swings to the left of the wall, outside"
    assert "A50 50" in paths[0]


def test_staff_stand_at_home_when_free_and_where_their_task_is_when_busy(page):
    settle(page)
    assert page.evaluate("['waiter0', 'waiter1', 'cook0', 'cook1'].map(key => { const t = desTokens.get(key); return [t.x, t.y]; })") == [[760, 350], [760, 392], [960, 300], [960, 420]]
    run_until(page, "desEngine.resources.waiters.units.some(unit => unit && unit.task === 'order')")
    at = page.evaluate("(() => { const i = desEngine.resources.waiters.units.findIndex(unit => unit && unit.task === 'order'), unit = desEngine.resources.waiters.units[i], t = desTokens.get('waiter' + i); return [[t.x, t.y], tables[desEngine.parties.get(unit.party).table].sp]; })()")
    assert at[0] == pytest.approx([at[1]["x"], at[1]["y"]], abs=1)
    run_until(page, "desEngine.resources.cooks.units.some(unit => unit && unit.task === 'plan')")
    assert page.evaluate("(() => { const t = desTokens.get('cook' + desEngine.resources.cooks.units.findIndex(unit => unit && unit.task === 'plan')); return Math.hypot(t.x - RAIL_COOK.x, t.y - RAIL_COOK.y) < 1; })()")
    run_until(page, "desEngine.resources.cooks.units.some(unit => unit && unit.task === 'plate')")
    assert page.evaluate("(() => { const t = desTokens.get('cook' + desEngine.resources.cooks.units.findIndex(unit => unit && unit.task === 'plate')); return Math.hypot(t.x - PASS_COOK.x, t.y - PASS_COOK.y) < 1; })()")
    run_until(page, "desEngine.resources.cooks.units.some(unit => unit && unit.task === 'oven')")
    assert page.evaluate("(() => { const t = desTokens.get('cook' + desEngine.resources.cooks.units.findIndex(unit => unit && unit.task === 'oven')); return Math.hypot(t.x - DES_EQUIPMENT.oven[0].stand.x, t.y - DES_EQUIPMENT.oven[0].stand.y) < 1; })()")


def test_a_waiter_running_food_is_as_far_along_as_the_task(page):
    run_until(page, "desEngine.resources.waiters.units.some(unit => unit && unit.task === 'deliver')")
    places = page.evaluate("""() => { const i = desEngine.resources.waiters.units.findIndex(unit => unit && unit.task === 'deliver'), unit = desEngine.resources.waiters.units[i], to = tables[desEngine.parties.get(unit.party).table].sp, out = [];
        for (const k of [0.25, 0.75]) { desEngine.currentTime = unit.since + (unit.until - unit.since) * k; for (let n = 0; n < 200; n++) { __advance(16.7); drawDes(); } const t = desTokens.get('waiter' + i);
            out.push(Math.hypot(t.x - PASS_WAITER.x, t.y - PASS_WAITER.y) / Math.hypot(to.x - PASS_WAITER.x, to.y - PASS_WAITER.y)); }
        return out; }""")
    assert places == pytest.approx([0.25, 0.75], abs=0.02)


def test_equipment_glows_and_shows_progress_while_it_is_in_use(page):
    assert page.evaluate("Object.values(DES_EQUIPMENT).flat().every(one => one.flame.style.opacity === '0' || one.flame.style.opacity === '')")
    run_until(page, "Boolean(desEngine.resources.oven.units[0])")
    run(page, 1)
    assert page.evaluate("[Number(DES_EQUIPMENT.oven[0].flame.style.opacity) > 0.2, Number(DES_EQUIPMENT.oven[0].bar.getAttribute('width')) > 0]") == [True, True]
    assert page.evaluate("desProgress(0, null, 5)") == 0 and page.evaluate("[desProgress(0, 10, 5), desProgress(0, 10, 50), desProgress(3, 3, 3)]") == [0.5, 1, 0]


def test_the_ticket_rail_and_the_pass_table_are_the_same_size_and_steel(page):
    boxes = page.evaluate("[DES_QUEUE.plan.info.nodes[0], DES_QUEUE.run.info.nodes[0]].map(g => { const r = g.querySelector('rect'); return [r.getAttribute('class'), r.getAttribute('width'), r.getAttribute('height'), r.getAttribute('x')]; })")
    assert boxes == [["steel", "66", "80", "772"]] * 2
    captions = page.evaluate("[DES_QUEUE.plan.info.nodes[0], DES_QUEUE.run.info.nodes[0]].map(g => [...g.querySelectorAll('text')].map(t => [t.textContent, Number(t.getAttribute('x'))]))")
    assert captions == [[["TICKET", 846], ["RAIL", 846]], [["PASS", 846], ["TABLE", 846]]], "each caption is on two lines, just to the right"
    assert page.evaluate("RAIL_COOK.x > 846 + 60 && PASS_COOK.x === RAIL_COOK.x"), "the cook stands past the words"


def test_tickets_wait_on_the_rail_and_plates_on_the_pass_with_their_table_number(page):
    page.evaluate("desEngine.changeCapacity('cooks', -1); desEngine.changeCapacity('cooks', -1)")
    run_until(page, "desEngine.queues.plan.length >= 2")
    shown = page.evaluate("desRailTickets.filter(slot => slot.g.getAttribute('visibility') !== 'hidden').map(slot => slot.label.textContent)")
    assert shown == page.evaluate("desEngine.queues.plan.slice(0, 5).map(id => String(desEngine.parties.get(id).table + 1))")
    click(page, "desRailTickets[0].g")
    settle(page, 2)
    assert about(page)["name"].startswith("Party ") and page.evaluate("[desRailTickets[0].g.hasAttribute('data-selected'), desRailTickets[1].g.hasAttribute('data-selected')]") == [True, False]
    page.evaluate("select(null); desEngine.changeCapacity('cooks', 1); desEngine.changeCapacity('cooks', 1); desEngine.changeCapacity('waiters', -1); desEngine.changeCapacity('waiters', -1)")
    run_until(page, "desEngine.queues.run.length >= 1")
    assert page.evaluate("desPassDishes.filter(slot => slot.g.getAttribute('visibility') !== 'hidden').length") == page.evaluate("Math.min(6, desEngine.queues.run.length)")


def test_the_oven_and_the_coffee_machine_are_steel_with_nothing_white(page):
    fills = page.evaluate("['oven', 'coffee'].map(kind => [...DES_RES[kind].units[0].info.nodes[0].querySelectorAll('rect.steel, circle:not(.flame), path:not(.flame):not(.out-mark)')].map(node => node.getAttribute('fill') || 'steel'))")
    assert "#f2f2f2" not in sum(fills, []) and "#fff" not in sum(fills, [])
    assert page.evaluate("getComputedStyle(DES_RES.oven.units[0].info.nodes[0].querySelector('rect.steel')).fill") == page.evaluate("getComputedStyle(DES_RES.coffee.units[0].info.nodes[0].querySelector('rect.steel')).fill")


def test_everything_in_the_room_can_be_selected(page):
    run(page, 60)
    for expression, name in [("desFloorTables[6].g", "Table 7"), ("DES_RES.stoves.units[1].info.nodes[0]", "Stove 2"), ("DES_RES.oven.units[0].info.nodes[0]", "Pizza oven"),
                             ("DES_RES.coffee.units[0].info.nodes[0]", "Coffee machine"), ("DES_QUEUE.plan.info.nodes[0]", "Ticket rail"), ("DES_QUEUE.run.info.nodes[0]", "Pass"),
                             ("desTokens.get('waiter1').g", "Waiter 2"), ("desTokens.get('cook0').g", "Cook 1")]:
        click(page, expression)
        assert about(page)["name"] == name


def test_a_selected_table_has_a_white_ring_and_keeps_its_colour(page):
    run_until(page, "[...desEngine.parties.values()].some(party => party.table === 0 && party.state === 'EATING_AND_BILLING')")
    click(page, "desFloorTables[0].g")
    page.wait_for_timeout(350)   # the outline changes colour over a fifth of a second
    look = page.evaluate("(() => { const top = getComputedStyle(desFloorTables[0].g.querySelector('.table-top')), other = getComputedStyle(desFloorTables[1].g.querySelector('.table-top')); return [top.stroke, top.strokeWidth, top.fill !== 'rgb(255, 255, 255)', other.stroke, other.strokeWidth]; })()")
    assert look[:3] == ["rgb(255, 255, 255)", "5px", True] and look[3] != "rgb(255, 255, 255)" and look[4] == "3px"


def test_out_of_service_shows_as_a_red_line_and_a_sick_person_is_not_on_the_floor(page):
    settle(page)
    page.evaluate("desEngine.setOut('tables', 5, true); desEngine.setOut('oven', 0, true); desEngine.setOut('cooks', 1, true); desEngine.setOut('waiters', 0, true)")
    settle(page)
    assert page.evaluate("[desFloorTables[5].out, desFloorTables[4].out, DES_EQUIPMENT.oven[0].out, DES_EQUIPMENT.coffee[0].out].map(mark => mark.getAttribute('visibility'))") == ["visible", "hidden", "visible", "hidden"]
    assert sorted(key for key in page.evaluate("[...desTokens.keys()]") if not key.startswith("P")) == ["cook0", "waiter1"]
    assert page.evaluate("getComputedStyle(desFloorTables[5].out).stroke") == page.evaluate("(() => { const probe = document.createElement('i'); probe.style.color = 'var(--waiting)'; document.body.append(probe); return getComputedStyle(probe).color; })()")
    page.evaluate("desEngine.setOut('cooks', 1, false); desEngine.setOut('tables', 5, false)")
    settle(page)
    assert "cook1" in page.evaluate("[...desTokens.keys()]") and page.evaluate("desFloorTables[5].out.getAttribute('visibility')") == "hidden"


def test_staff_not_on_shift_are_not_drawn(page):
    page.evaluate("desEngine.changeCapacity('waiters', 1)")
    settle(page)
    assert sorted(key for key in page.evaluate("[...desTokens.keys()]") if key.startswith("waiter")) == ["waiter0", "waiter1", "waiter2"]
