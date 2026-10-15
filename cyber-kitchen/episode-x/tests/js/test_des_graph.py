"""js/des-graph.js: the Process Map, the steps a party goes through, with resources above and outcomes below."""
import pytest

from tests.conftest import open_page
from tests.support import about, click, resources, run, run_until, settle, show, strays

STEPS = ["seating", "browsing", "ordering", "planning", "stoves", "oven", "coffee", "plating", "running", "dining"]
OUTCOMES = ["away", "noorder", "hungry", "out"]


@pytest.fixture
def graph(page):
    show(page, "graph")
    return page


def box(page, key):
    return page.evaluate(f"(() => {{ const b = GRAPH['{key}']; return {{ x: b.x + b.dx, y: b.y + b.dy, right: b.right + b.dx, bottom: b.bottom + b.dy, cx: b.cx + b.dx, cy: b.cy + b.dy }}; }})()")


def lines(page):
    return page.evaluate("graphEdges.filter(edge => edge.line.style.display !== 'none').map(edge => edge.from + '>' + edge.to)")


# ---------- the three sections ----------

def test_three_sections_divided_by_two_lines_across_the_map(graph):
    headings = graph.evaluate("[...graphSectionLayer.querySelectorAll('text')].map(heading => [Number(heading.getAttribute('y')), heading.textContent])")
    assert [name for _, name in sorted(headings)] == ["ACTORS & RESOURCES", "TASKS", "OUTCOMES"]
    rules = sorted(graph.evaluate("[...graphSectionLayer.querySelectorAll('path')].map(line => line.getAttribute('d'))"), key=lambda d: float(d.split()[1].split("H")[0]))
    span = graph.evaluate("[GRAPH_SPAN.left, GRAPH_SPAN.right + graphWide]")
    assert rules == [f"M{span[0]} {graph.evaluate('GRAPH_SECTION.process')}H{span[1]}", f"M{span[0]} {graph.evaluate('GRAPH_SECTION.outcomes')}H{span[1]}"]
    assert span == [16, max(box(graph, key)["right"] for key in STEPS)], "the lines run from the first box's left edge to the last one's right"


def test_resources_and_outcomes_take_a_fifth_of_the_height_each(graph):
    s = graph.evaluate("GRAPH_SECTION")
    total = s["end"] - s["resources"]
    assert (s["process"] - s["resources"]) / total == pytest.approx(0.2) and (s["outcomes"] - s["process"]) / total == pytest.approx(0.6)


def test_outcomes_is_named_at_the_very_bottom_and_the_others_at_their_top(graph):
    ys = graph.evaluate("Object.fromEntries([...graphSectionLayer.querySelectorAll('text')].map(heading => [heading.textContent, Number(heading.getAttribute('y'))]))")
    s = graph.evaluate("GRAPH_SECTION")
    assert ys["ACTORS & RESOURCES"] == s["resources"] + 18 and ys["TASKS"] == s["process"] + 18 and ys["OUTCOMES"] == s["end"] - 3


def test_nothing_folds(graph):
    assert graph.evaluate("document.querySelectorAll('#desgraph [aria-label^=Collapse], #desgraph [aria-label^=Expand]').length") == 0


# ---------- resources ----------

def test_parties_and_six_resources_in_seven_boxes_centred_in_their_section(graph):
    boxes = graph.evaluate("GRAPH_TOP.map(pool => { const r = pool.g.querySelector('rect'); return [pool.id, Number(r.getAttribute('x')), Number(r.getAttribute('y')), Number(r.getAttribute('width')), Number(r.getAttribute('height'))]; })")
    assert [b[0] for b in boxes] == ["parties", "tables", "waiters", "cooks", "stoves", "oven", "coffee"]
    span, s = graph.evaluate("[GRAPH_SPAN.left, GRAPH_SPAN.right]"), graph.evaluate("GRAPH_SECTION")
    assert boxes[0][1] - span[0] == pytest.approx(span[1] - (boxes[-1][1] + boxes[-1][3])), "as much room on the left as on the right"
    assert boxes[0][2] - s["resources"] == pytest.approx(s["process"] - (boxes[0][2] + boxes[0][4])), "and as much above as below"
    assert {round(b[1] - a[1] - a[3]) for a, b in zip(boxes, boxes[1:])} == {9} and boxes[0][1] == span[0], "together they run the full width"


def test_actors_have_a_grey_edge_resources_a_violet_one_and_blue_is_left_for_buttons(graph):
    stripes = graph.evaluate("GRAPH_TOP.map(pool => pool.g.querySelectorAll('rect')[1].getAttribute('fill'))")
    assert dict(zip(graph.evaluate("GRAPH_TOP.map(pool => pool.id)"), stripes)) == {"parties": "#b9bcc0", "waiters": "#b9bcc0", "cooks": "#b9bcc0",
                                                                                   "tables": "#a78bfa", "stoves": "#a78bfa", "oven": "#a78bfa", "coffee": "#a78bfa"}
    assert graph.evaluate("['parties', 'waiters', 'cooks', 'tables', 'stoves', 'oven', 'coffee'].map(graphIsActor)") == [True, True, True, False, False, False, False]
    assert graph.evaluate("document.querySelector('#graph-arrow-actor path').getAttribute('fill')") == "#b9bcc0"
    assert graph.evaluate("document.querySelector('#graph-arrow-resource path').getAttribute('fill')") == "#a78bfa"
    drawn = graph.evaluate("$('desgraph').innerHTML")
    assert "#2563eb" not in drawn and "#3b82f6" not in drawn and "#4f9cf0" not in drawn


def test_a_unit_is_a_hollow_square_crossed_when_in_use(graph):
    run_until(graph, "desEngine.resources.tables.allocated >= 3 && desEngine.resources.cooks.allocated === 1")
    state = resources(graph)
    for pool in graph.evaluate("GRAPH_TOP.slice(1).map(pool => pool.id)"):
        marks = graph.evaluate(f"GRAPH_TOP.find(pool => pool.id === '{pool}').squares.map(square => square.style.display === 'none' ? 'off' : square.classList.contains('out') ? 'out' : square.classList.contains('used') ? 'busy' : 'free')")
        assert marks == state[pool]["units"], pool
    fills = graph.evaluate("(() => { const squares = GRAPH_TOP[1].squares; return [getComputedStyle(squares.find(s => s.classList.contains('used'))).fill, getComputedStyle(squares.find(s => !s.classList.contains('used'))).fill]; })()")
    assert fills == ['url("#unit-cross")', "rgba(0, 0, 0, 0)"]
    assert graph.evaluate("document.querySelector('#unit-cross path').getAttribute('stroke')") == "#6a737b", "the cross is the colour of the outline"


def test_a_unit_out_of_service_has_one_red_line(graph):
    graph.evaluate("desEngine.setOut('oven', 0, true)")
    settle(graph, 2)
    square = "GRAPH_TOP.find(pool => pool.id === 'oven').squares[0]"
    assert graph.evaluate(f"[{square}.classList.contains('out'), getComputedStyle({square}).fill]") == [True, 'url("#unit-out")']
    assert graph.evaluate("[document.querySelector('#unit-out path').getAttribute('stroke'), document.querySelector('#unit-out path').getAttribute('d').split('M').length - 1]") == ["#ef4444", 1]


def test_each_square_selects_its_unit_and_the_rest_of_the_box_the_resource(graph):
    click(graph, "GRAPH_TOP[1].squares[6]")
    assert about(graph)["name"] == "Table 7" and graph.evaluate("GRAPH_TOP[1].squares.filter(square => square.hasAttribute('data-selected')).length") == 1
    assert graph.evaluate("GRAPH_TOP[1].squares[6].querySelector('title').textContent") == "Table 7"
    click(graph, "GRAPH_TOP[1].g.querySelector('rect')")
    assert about(graph)["name"] == "Tables" and graph.evaluate("GRAPH_TOP[1].g.hasAttribute('data-selected')")
    show(graph, "des")
    graph.evaluate("select(DES_RES.tables.units[6].info)")
    assert graph.evaluate("desFloorTables[6].g.hasAttribute('data-selected')"), "table 7 here is the same table 7 as on the floor plan"


def test_plus_and_minus_above_waiters_and_cooks_change_who_is_on_shift(graph):
    buttons = graph.evaluate("[...graphMetersLayer.querySelectorAll('.loop-button')].map(button => button.getAttribute('aria-label'))")
    assert buttons == ["One waiter fewer", "One more waiter", "One cook fewer", "One more cook"]
    graph.evaluate("graphMetersLayer.querySelectorAll('.loop-button')[1].dispatchEvent(new MouseEvent('click', { bubbles: true }))")
    settle(graph, 2)
    assert resources(graph)["waiters"]["capacity"] == 3 and graph.evaluate("GRAPH_TOP[2].squares.filter(square => square.style.display !== 'none').length") == 3
    graph.evaluate("graphMetersLayer.querySelectorAll('.loop-button')[2].dispatchEvent(new MouseEvent('click', { bubbles: true }))")
    assert resources(graph)["cooks"]["capacity"] == 1 and graph.evaluate("selected") is None, "a button does not change the selection"
    above = graph.evaluate("(() => { const button = graphMetersLayer.querySelector('.loop-button').getBBox(), box = GRAPH_TOP[2].g.querySelector('rect'); return Number(graphMetersLayer.querySelector('.loop-button').getAttribute('transform').match(/ (\\S+)\\)/)[1]) + 18 <= Number(box.getAttribute('y')); })()")
    assert above


# ---------- the process ----------

def test_the_first_three_steps_go_down_one_column_and_the_rest_run_to_the_right(graph):
    b = {key: box(graph, key) for key in ["source"] + STEPS}
    assert b["seating"]["y"] < b["source"]["cy"] < b["seating"]["cy"] and b["source"]["right"] < b["seating"]["x"], "the start is beside the first step, level with its upper half"
    assert b["seating"]["cx"] == b["browsing"]["cx"] == b["ordering"]["cx"] and b["seating"]["bottom"] < b["browsing"]["y"] < b["browsing"]["bottom"] < b["ordering"]["y"]
    main = ["planning", "oven", "plating", "running", "dining"]
    assert len({b[key]["cy"] for key in main}) == 1 and b["browsing"]["cy"] == b["planning"]["cy"]
    assert all(b[a]["right"] < b[c]["x"] for a, c in zip(main, main[1:])) and b["ordering"]["right"] < b["planning"]["x"]
    assert b["stoves"]["cx"] == b["oven"]["cx"] == b["coffee"]["cx"] and b["stoves"]["cy"] < b["oven"]["cy"] < b["coffee"]["cy"]


def test_boxes_are_at_least_32_units_apart_wherever_an_arrow_runs(graph):
    b = {key: box(graph, key) for key in ["source"] + STEPS}
    across = [("ordering", "planning"), ("planning", "oven"), ("oven", "plating"), ("plating", "running"), ("running", "dining")]
    wide = graph.evaluate("graphWide")
    assert {round(b[c]["x"] - b[a]["right"], 3) for a, c in across} == {round(32 + wide / 6, 3)}, "32 as laid out, and an equal share of any spare width on top"
    assert {round(b[c]["y"] - b[a]["bottom"]) for a, c in [("seating", "browsing"), ("browsing", "ordering"), ("stoves", "oven"), ("oven", "coffee")]} == {32}
    assert graph.evaluate("GB.gap") == 32


def test_box_widths(graph):
    widths = {key: round(box(graph, key)["right"] - box(graph, key)["x"]) for key in STEPS}
    assert widths["dining"] == 54 and widths["browsing"] == 74
    assert widths["stoves"] == widths["oven"] == widths["coffee"] == 8 + 2 * 48 + 8, "a kitchen part is its waiting area and as much again beside it"


def test_titles_are_short_and_wrap_onto_two_lines(graph):
    titles = {key: graph.evaluate(f"[...GRAPH['{key}'].g.querySelectorAll('.task-name')].map(line => line.textContent)") for key in STEPS}
    assert titles == {"seating": ["Get a", "table"], "browsing": ["View", "menu"], "ordering": ["Order"], "planning": ["Plan"], "stoves": ["Use", "stove"],
                      "oven": ["Bake", "pizza"], "coffee": ["Make", "coffee"], "plating": ["Plate", "food"], "running": ["Food", "to table"], "dining": ["Dining"]}
    assert graph.evaluate("GRAPH.stoves.label") == "Use stove", "the label in one line, for menus"
    clear = graph.evaluate("""Object.values(GRAPH).filter(b => b.task && b.g.querySelector('.task-zone')).every(b => {
        const zone = b.g.querySelector('.task-zone').getBBox(); return [...b.g.querySelectorAll('.task-name')].every(line => line.getBBox().x > zone.x + zone.width); })""")
    assert clear, "no title runs into the waiting area"


def test_a_step_that_can_wait_has_a_dashed_grey_waiting_area_the_full_height(graph):
    has = {key: graph.evaluate(f"Boolean(GRAPH['{key}'].g.querySelector('.task-zone.queue'))") for key in STEPS}
    assert has == {key: key not in ("browsing", "dining") for key in STEPS}
    zone = graph.evaluate("(() => { const z = GRAPH.oven.g.querySelector('.task-zone.queue'), s = getComputedStyle(z); return [z.getAttribute('width'), Number(z.getAttribute('height')), s.stroke, s.strokeDasharray]; })()")
    muted = graph.evaluate("(() => { const probe = document.createElement('i'); probe.style.color = 'var(--text-muted)'; document.body.append(probe); return getComputedStyle(probe).color; })()")
    assert zone == ["48", 96 - 12, muted, "5px, 4px"], "the same grey as the section headings, not orange"


def test_the_process_starts_at_a_small_filled_circle_with_an_arrow_into_get_a_table(graph):
    start = graph.evaluate("(() => { const dot = GRAPH.source.g.querySelector('.graph-start'); return [dot.tagName, Number(dot.getAttribute('r')), getComputedStyle(dot).fill, GRAPH.source.g.querySelectorAll('text').length, GRAPH.source.g.querySelector('title').textContent]; })()")
    muted = graph.evaluate("(() => { const probe = document.createElement('i'); probe.style.color = 'var(--text-muted)'; document.body.append(probe); return getComputedStyle(probe).color; })()")
    assert start == ["circle", 8, muted, 0, "Start: parties arrive here"], "no name and no count: just where it starts"
    arrow = graph.evaluate("graphEdges.find(edge => edge.from === 'source').points")
    assert graph.evaluate("graphEdges.filter(edge => edge.from === 'source').map(edge => edge.to)") == ["seating"]
    assert arrow[0]["y"] == arrow[1]["y"] == box(graph, "source")["cy"] and arrow[1]["x"] == box(graph, "seating")["x"] - 3


def test_parties_at_the_door_wait_inside_get_a_table_and_a_party_turned_away_leaves_from_it(graph):
    graph.evaluate("for (let i = 0; i < 12; i++) desEngine.setOut('tables', i, true)")
    run_until(graph, "desEngine.queues.host.length === 3")
    seating = box(graph, "seating")
    waiting = graph.evaluate("desEngine.queues.host.map(id => { const token = graphTokens.get(id); return [token.x, token.y]; })")
    assert all(seating["x"] + 8 < x < seating["x"] + 56 and seating["y"] < y < seating["bottom"] for x, y in waiting), "in the dashed waiting area of Get a table"
    out = graph.evaluate("graphEdges.find(edge => edge.from === 'seating' && edge.to === 'away').points")
    assert out[0]["x"] == seating["x"] - 1 and out[0]["y"] == out[1]["y"] > box(graph, "source")["cy"] and out[1]["x"] == out[2]["x"] and out[2]["y"] == box(graph, "away")["y"] - 3
    assert box(graph, "away")["x"] < out[2]["x"] < box(graph, "away")["right"]


def test_every_step_the_door_and_every_outcome_selects_its_own_card(graph):
    names = {}
    for key in ["source"] + STEPS + OUTCOMES:
        click(graph, f"GRAPH['{key}'].g.querySelector('.graph-node')")
        names[key] = about(graph)["name"]
        assert graph.evaluate("document.querySelectorAll('#desgraph [data-step][data-selected]').length") == 1, key
    assert names["source"] == "Parties arriving" and [names[key] for key in OUTCOMES] == ["Turned away", "Left: slow waiter", "Left: slow kitchen", "Dined"]
    assert len(set(names.values())) == 15 and "Flow through the restaurant" not in names.values()


# ---------- outcomes ----------

def test_outcomes_are_drawn_like_steps_with_a_green_or_red_edge(graph):
    look = {key: graph.evaluate(f"(() => {{ const g = GRAPH['{key}'].g, r = g.querySelectorAll('rect'); return [r[0].getAttribute('class'), r[0].getAttribute('rx'), r[0].getAttribute('width'), r[0].getAttribute('height'), r[1].getAttribute('fill'), g.querySelector('.task-name').textContent]; }})()") for key in OUTCOMES}
    assert look["out"] == ["des-stage graph-node", "6", "108", "74", "var(--eating)", "dined"]
    assert [look[key][4] for key in OUTCOMES[:3]] == ["var(--waiting)"] * 3 and [look[key][5] for key in OUTCOMES[:3]] == ["turned away", "left: slow waiter", "left: slow kitchen"]
    step = graph.evaluate("(() => { const r = GRAPH.ordering.g.querySelector('rect'); return [r.getAttribute('class'), r.getAttribute('rx')]; })()")
    assert step == look["out"][:2]


def test_outcomes_sit_in_the_middle_of_their_section_under_their_step_without_overlapping(graph):
    s, b = graph.evaluate("GRAPH_SECTION"), {key: box(graph, key) for key in OUTCOMES + ["source", "ordering", "running", "dining"]}
    assert all(b[key]["y"] - s["outcomes"] - graph.evaluate("graphSpare") == pytest.approx(s["end"] + graph.evaluate("graphSpare") - b[key]["bottom"], abs=1) for key in OUTCOMES)
    for outcome, step in [("away", "source"), ("noorder", "ordering"), ("hungry", "running"), ("out", "dining")]:
        assert b[outcome]["x"] <= b[step]["cx"] <= b[outcome]["right"], f"{outcome} is under {step}"
    ordered = sorted(OUTCOMES, key=lambda key: b[key]["x"])
    assert all(b[c]["x"] - b[a]["right"] >= 16 for a, c in zip(ordered, ordered[1:]))
    assert b["away"]["x"] >= 16 and b["out"]["right"] == graph.evaluate("GRAPH_SPAN.right + graphWide")


def test_outcomes_count_how_visits_ended(graph):
    graph.evaluate("desEngine.changeCapacity('cooks', -1)")
    run(graph, 900, dt=0.25)
    assert [graph.evaluate(f"GRAPH['{key}'].count.textContent") for key in OUTCOMES] == [str(v) for v in graph.evaluate("[desEngine.balked, desEngine.abandonedFor.order, desEngine.abandonedFor.food, desEngine.departed]")]


# ---------- parties moving ----------

def test_parties_are_grey_boxes_with_black_numbers(graph):
    run(graph, 60)
    look = graph.evaluate("(() => { const token = [...graphTokens.values()][0]; const s = getComputedStyle(token.g.querySelector('.token-box')); return [s.fill, token.g.querySelector('text').style.fill, token.g.querySelector('text').textContent]; })()")
    assert look[0] == "rgb(185, 188, 192)" and look[1] in ("rgb(17, 17, 17)", "#111") and look[2].isdigit()


def test_every_party_is_in_its_box_waiting_on_the_left_and_being_served_on_the_right(graph):
    for _ in range(6):
        run(graph, 45)
        assert strays(graph) == []
    placed = graph.evaluate("""[...desEngine.parties.values()].filter(party => GRAPH_PLACE[party.state]).map(party => { const [key, area] = GRAPH_PLACE[party.state], token = graphTokens.get(party.id), b = GRAPH[key];
        return [area, token.x - b.x - b.dx, b.g.querySelector('.task-zone') ? 56 : 0]; })""")
    assert placed and all((x < edge) if area == "wait" else (x > edge) for area, x, edge in placed)


def test_tokens_stay_on_the_arrows_while_they_move(graph):
    off = graph.evaluate("""() => { let off = 0, samples = 0;
        const inBox = t => Object.values(GRAPH).some(b => t.x >= b.x + b.dx - 3 && t.x <= b.right + b.dx + 3 && t.y >= b.y + b.dy - 3 && t.y <= b.bottom + b.dy + 3);
        const onArrow = t => graphEdges.some(edge => edge.points.slice(1).some((p, i) => { const a = edge.points[i];
            return t.x >= Math.min(a.x, p.x) - 3 && t.x <= Math.max(a.x, p.x) + 3 && t.y >= Math.min(a.y, p.y) - 3 && t.y <= Math.max(a.y, p.y) + 3; }));
        for (let i = 0; i < 9000; i++) { tick(1 / 60); __advance(16.7); drawGraph(); for (const token of graphTokens.values()) { samples++; if (!inBox(token) && !onArrow(token)) off++; } }
        return [off, samples > 20000]; }""")
    assert off == [0, True], "never cutting a corner"


def test_an_order_being_cooked_shows_one_token_per_part_and_waits_at_plating_for_the_rest(graph):
    run_until(graph, "desHeldForParts().length > 0")
    party = graph.evaluate("desHeldForParts()[0].id")
    keys = graph.evaluate(f"[...graphTokens.keys()].filter(key => key.startsWith('{party}/'))")
    assert f"{party}/held" in keys and any(key.split("/")[1] in ("stoves", "oven", "coffee") for key in keys)
    held, zone = graph.evaluate(f"graphTokens.get('{party}/held').x"), box(graph, "plating")
    assert zone["x"] < held < zone["x"] + 56, "the held order waits in Plating's waiting area"
    assert graph.evaluate(f"getComputedStyle(graphTokens.get('{party}/held').g.querySelector('.token-box')).strokeDasharray") == "none", "drawn like any other waiting token"


def test_a_box_with_more_parties_than_places_says_how_many_more(graph):
    graph.evaluate("desEngine.changeCapacity('cooks', -1); desEngine.changeCapacity('cooks', -1); for (let i = 0; i < 4; i++) desEngine.changeCapacity('waiters', 1)")
    run_until(graph, "desEngine.queues.plan.length > 8")
    waiting = graph.evaluate("desEngine.queues.plan.length")
    assert graph.evaluate("GRAPH.planning.wait.more.textContent") == f"+{waiting - 8}" and graph.evaluate("GRAPH.oven.active.more.textContent") == ""
    assert graph.evaluate("[graphSpot(GRAPH.dining.active, 0), graphSpot(GRAPH.dining.active, 5), graphSpot(GRAPH.dining.active, 99)].map(spot => [spot.x, spot.y])")[1:] == [graph.evaluate("(() => { const s = graphSpot(GRAPH.dining.active, 5); return [s.x, s.y]; })()")] * 2


def test_a_selected_party_is_outlined_and_can_be_clicked(graph):
    run(graph, 60)
    key = graph.evaluate("[...graphTokens.keys()][0]")
    click(graph, f"graphTokens.get('{key}').g")
    settle(graph, 2)
    assert about(graph)["name"].startswith("Party ") and graph.evaluate(f"graphTokens.get('{key}').g.hasAttribute('data-selected')")


def test_a_party_that_dines_leaves_through_dined_and_one_that_gives_up_through_its_exit(graph):
    seen = graph.evaluate("""() => { desEngine.changeCapacity('cooks', -1); const ends = { out: 0, hungry: 0, noorder: 0 };
        for (let i = 0; i < 40000; i++) { tick(1 / 30); __advance(33); drawGraph(); if (i % 3) continue;
            for (const token of graphTokens.values()) if (token.going && ends[token.at] !== undefined && !token.counted) { token.counted = true; ends[token.at]++; } }
        return ends; }""")
    assert seen["out"] > 5 and seen["hungry"] > 0


def test_a_party_turned_away_is_seen_going_through_get_a_table_to_its_outcome(graph):
    graph.evaluate("for (let i = 0; i < 12; i++) desEngine.setOut('tables', i, true)")
    seen = graph.evaluate("""() => { const keys = new Set(); let path = null;
        for (let i = 0; i < 6000; i++) { tick(1 / 30); __advance(33); drawGraph(); for (const [key, token] of graphTokens) if (key.endsWith('/away')) { keys.add(key); (path ||= []).push([Math.round(token.x), Math.round(token.y)]); } }
        return { seen: keys.size, balked: desEngine.balked, left: [...graphTokens.keys()].filter(key => key.endsWith('/away')).length, x: [...new Set(path.map(p => p[0]))] }; }""")
    assert seen["seen"] == seen["balked"] > 0 and seen["left"] <= 1
    turn = graph.evaluate("graphEdges.find(edge => edge.to === 'away').points")
    assert seen["x"][-1] == round(turn[-1]["x"]) and max(seen["x"]) > round(turn[0]["x"]), "from the start into Get a table, back out of its left side and down to turned away"


def test_turned_away_parties_are_not_replayed_when_the_view_comes_back(page):
    page.evaluate("for (let i = 0; i < 12; i++) desEngine.setOut('tables', i, true)")
    run_until(page, "desEngine.balked > 2")
    show(page, "graph")
    assert page.evaluate("[graphBalks.length, [...graphTokens.keys()].filter(key => key.endsWith('/away')).length]") == [0, 0]


# ---------- filling the card ----------

def test_the_map_hangs_from_the_top_with_the_same_margin_as_the_sides(graph):
    card = graph.locator("#desgraph").bounding_box()
    first = graph.evaluate("(() => { const b = graphSectionLayer.querySelector('rect').getBoundingClientRect(); return [b.left, b.top, b.right]; })()")
    assert first[1] - card["y"] == pytest.approx(first[0] - card["x"], abs=1.5) or first[1] - card["y"] < 16
    assert graph.evaluate("$('desgraph').getAttribute('preserveAspectRatio')") == "xMidYMin"


def test_on_a_tall_card_outcomes_go_down_to_the_bottom_and_the_steps_stay_in_the_middle(browser, site_server):
    page, finish = open_page(browser, site_server[0] + "#graph", width=900, height=1100)
    run(page, 120)
    spare = page.evaluate("graphSpare")
    assert spare > 100
    card, frame = page.locator("#desgraph").bounding_box(), page.evaluate("(() => { const b = graphFullHeight.getBoundingClientRect(); return [b.top, b.bottom]; })()")
    assert card["y"] + card["height"] - frame[1] == pytest.approx(frame[0] - card["y"], abs=2), "as far from the bottom edge as from the top"
    assert page.evaluate("[GRAPH.out.dy, GRAPH.ordering.dy, GRAPH.source.dy, graphOutcomesMarks.getAttribute('transform')]") == [spare, spare / 2, spare / 2, f"translate(0 {spare})"]
    assert page.evaluate("graphEdges.find(edge => edge.to === 'out').points.map(point => point.y)") == [page.evaluate("GRAPH.dining.bottom + 1 + graphSpare / 2"), page.evaluate("GRAPH.out.y - 3 + graphSpare")]
    assert strays(page) == []
    finish()


def test_the_map_is_laid_out_again_when_the_card_changes_shape(graph):
    before = graph.evaluate("graphSpare")
    graph.set_viewport_size({"width": 1000, "height": 1100})
    graph.wait_for_timeout(300)
    settle(graph, 2)
    assert graph.evaluate("graphSpare") > before and graph.evaluate("graphStale") is False
    same = graph.evaluate("(() => { const spare = graphSpare; graphMeasure(); return [graphSpare === spare, graphStale]; })()")
    assert same == [True, False], "measuring again with nothing changed does nothing"


def test_a_card_that_cannot_be_measured_keeps_the_layout_it_has(page):
    assert page.evaluate("(() => { const spare = graphSpare; const card = $('desgraph').parentNode; Object.defineProperty(card, 'clientWidth', { value: 0, configurable: true }); graphMeasure(); delete card.clientWidth; return graphSpare === spare; })()")


# ---------- the Parties box ----------

def parties_box(page):
    return page.evaluate("""() => { const pool = GRAPH_TOP[0], shown = pool.squares.filter(square => square.style.display !== 'none');
        return { title: pool.g.querySelector('.task-name').textContent, shown: shown.map(square => square.dataset.party), names: shown.map(square => square.firstChild.textContent), places: pool.squares.length }; }""")


def test_the_parties_box_has_one_crossed_square_for_each_party_in_the_building(graph):
    assert parties_box(graph)["shown"] == [] and parties_box(graph)["title"] == "Parties"
    run(graph, 90)
    box = parties_box(graph)
    assert box["shown"] == graph.evaluate("[...desEngine.parties.keys()]") and len(box["shown"]) > 3, "in the order they came in"
    assert box["names"][0].startswith("Party ") and box["places"] >= 15, "room for a full house and a full line at the door"
    assert graph.evaluate("getComputedStyle(GRAPH_TOP[0].squares[0]).fill") == 'url("#unit-cross")', "not filled: crossed, like a cook who is busy"


def test_parties_arrive_in_the_box_and_depart_from_it(graph):
    run_until(graph, "desEngine.departed >= 3")
    box = parties_box(graph)
    assert box["shown"] == graph.evaluate("[...desEngine.parties.keys()]") and "P1" not in box["shown"]
    graph.evaluate("desEngine.config.arrivalsUntil = 0")
    run_until(graph, "desEngine.parties.size === 0", limit=600)
    graph.evaluate("desEngine.config.arrivalsUntil = Infinity")
    assert parties_box(graph)["shown"] == []


def test_a_square_selects_its_party_and_the_rest_of_the_box_selects_all_the_parties(graph):
    run(graph, 90)
    click(graph, "GRAPH_TOP[0].squares[2]")
    settle(graph, 2)
    name = about(graph)["name"]
    assert name == parties_box(graph)["names"][2] and graph.evaluate("GRAPH_TOP[0].squares.filter(square => square.hasAttribute('data-selected')).length") == 1
    assert graph.evaluate(f"graphTokens.get('{parties_box(graph)['shown'][2]}')?.g.hasAttribute('data-selected') ?? true"), "the same party is outlined where it stands on the map"
    click(graph, "GRAPH_TOP[0].g.querySelector('rect')")
    card = about(graph)
    assert card["name"] == "Parties" and card["Kind"] == "Parties"


def test_a_square_whose_party_has_just_left_selects_nothing(graph):
    run(graph, 90)
    graph.evaluate("select(null); GRAPH_TOP[0].squares[0].dataset.party = 'P999'; GRAPH_TOP[0].squares[0].dispatchEvent(new MouseEvent('click', { bubbles: true }))")
    assert about(graph) is None


def test_a_passing_token_is_made_once_and_only_where_an_arrow_leads(graph):
    made = graph.evaluate("""() => { const build = graphPartyToken({ number: 7 });
        graphPasser('probe/away', 'source', 'away', DES_OUTCOME.away.info, build); const first = graphTokens.get('probe/away');
        graphPasser('probe/away', 'source', 'away', DES_OUTCOME.away.info, build);
        graphPasser('probe/back', 'out', 'source', DES_OUTCOME.away.info, build);
        return [graphTokens.get('probe/away') === first, first.going, first.at, graphTokens.has('probe/back'), first.tx, first.ty]; }""")
    assert made[:4] == [True, True, "away", False] and made[4:] == [graph.evaluate("GRAPH.source.cx"), graph.evaluate("GRAPH.away.y + GRAPH.away.dy - 3")]


def test_a_leaving_token_with_no_arrow_to_follow_just_goes(graph):
    run_until(graph, "[...desEngine.parties.values()].some(party => party.state === 'EATING_AND_BILLING')")
    graph.evaluate("window.mine = [...desEngine.parties.values()].find(party => party.state === 'EATING_AND_BILLING').id; graphRoute = makeRouter([], graphCentre)")
    run_until(graph, "!desEngine.parties.has(mine)")
    assert graph.evaluate("graphTokens.has(mine)") is False
    graph.evaluate("graphPin(null)")


# ---------- using the full width ----------

def test_a_card_wider_than_the_map_spreads_the_columns_out_to_fill_it(graph):
    wide = graph.evaluate("graphWide")
    assert wide > 100 and graph.evaluate("graphSpare") == 0, "at 1400 by 900 the card is wider than the map"
    card, frame = graph.locator("#desgraph").bounding_box(), graph.evaluate("(() => { const b = graphFullHeight.getBoundingClientRect(); return [b.left, b.right, b.top, b.bottom]; })()")
    margins = [frame[0] - card["x"], card["x"] + card["width"] - frame[1], frame[2] - card["y"], card["y"] + card["height"] - frame[3]]
    assert max(margins) - min(margins) < 2 and margins[0] < 20, "the same small margin on all four sides"
    assert graph.evaluate("Object.values(GRAPH).every(b => b.dx === graphWide * GRAPH_COLUMN[b.key] / 6)")
    assert graph.evaluate("[GRAPH.source.dx, GRAPH.dining.dx, GRAPH.out.dx, GRAPH.away.dx]") == [0, wide, wide, 0]


def test_the_boxes_along_the_top_and_the_section_lines_spread_out_with_it(graph):
    wide = graph.evaluate("graphWide")
    shifts = graph.evaluate("GRAPH_TOP.map(pool => Number(pool.g.getAttribute('transform').match(/\\(([\\d.]+)/)[1]))")
    assert shifts == pytest.approx([wide * i / 6 for i in range(7)])
    buttons = graph.evaluate("GRAPH_TOP[2].buttons.map(button => [button.x, Number(button.g.getAttribute('transform').match(/\\(([\\d.]+)/)[1])])")
    assert all(now == pytest.approx(base + wide * 2 / 6) for base, now in buttons), "minus and plus move with their box"
    right = graph.evaluate("GRAPH_SPAN.right + graphWide")
    assert all(rule.endswith(f"H{right}") for rule in graph.evaluate("[...graphSectionLayer.querySelectorAll('path')].map(line => line.getAttribute('d'))"))
    last = graph.evaluate("(() => { const b = GRAPH_TOP[6].g.getBoundingClientRect(), f = graphFullHeight.getBoundingClientRect(); return Math.abs(b.right - f.right); })()")
    assert last < 1.5


def test_upright_arrows_stay_upright_when_the_map_is_spread_out(graph):
    for edge in ["seating>browsing", "browsing>ordering", "ordering>noorder", "running>hungry", "dining>out"]:
        xs = graph.evaluate(f"graphEdges.find(edge => edge.from + '>' + edge.to === '{edge}').points.map(point => point.x)")
        assert len(set(xs)) == 1, edge
    bends = graph.evaluate("graphEdges.every(edge => edge.points.slice(1).every((point, i) => point.x === edge.points[i].x || point.y === edge.points[i].y))")
    assert bends, "every arrow is made of level and upright pieces only"


def test_a_token_of_a_party_that_gave_up_somewhere_with_no_exit_of_its_own_just_goes(graph):
    run(graph, 30)
    gone = graph.evaluate("""() => { desGaveUp.add('P999'); const token = viewToken(graphTokens, 'graph-parties', 'P999/stoves', DES_OUTCOME.hungry.info, graphPartyToken({ number: 999 }));
        token.x = token.tx = 500; token.y = token.ty = 300; token.at = 'stoves'; token.route = []; __advance(16); drawGraph(); __advance(16); drawGraph(); desGaveUp.delete('P999'); return graphTokens.has('P999/stoves'); }""")
    assert gone is False


def test_a_party_that_gives_up_waiting_to_order_leaves_through_left_slow_waiter(graph):
    graph.evaluate("desEngine.changeCapacity('waiters', -1); desEngine.changeCapacity('waiters', -1)")
    seen = graph.evaluate("""() => { let going = 0; for (let i = 0; i < 9000 && !going; i++) { tick(1 / 30); __advance(33); drawGraph();
            for (const token of graphTokens.values()) if (token.going && token.at === 'noorder') going++; }
        return [going, desEngine.abandonedFor.order]; }""")
    assert seen[0] > 0 and seen[1] > 0
