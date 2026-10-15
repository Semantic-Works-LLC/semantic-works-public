"""js/des-graph.js, continued: pinning a step, the door, an outcome, a resource or one unit of it."""
import pytest

from tests.support import about, click, resources, run, run_until, settle, show, strays
from tests.js.test_des_graph import box, lines, graph, STEPS  # noqa: F401  (graph is a fixture)


def pinned_badges(page):
    return page.evaluate("[...graphPinLayer.querySelectorAll('g')].filter(g => g.querySelector('title')?.textContent === 'Pinned').map(g => g.getAttribute('transform'))")


# ---------- a step ----------

def test_a_pinned_step_shows_only_what_leads_into_it_and_out_of_it(graph):
    graph.evaluate("graphPin('plating')")
    assert graph.evaluate("[...graphShown]") == ["plating", "stoves", "oven", "coffee", "running", "hungry"]
    assert sorted(lines(graph)) == sorted(["stoves>plating", "oven>plating", "coffee>plating", "plating>running", "plating>hungry"]), "only lines to it and from it"
    hidden = graph.evaluate("Object.values(GRAPH).filter(b => b.g.style.display === 'none').map(b => b.key)")
    assert set(hidden) == {"source", "seating", "browsing", "ordering", "planning", "dining", "away", "noorder", "out"}
    assert graph.evaluate("[graphMetersLayer.style.display, graphSectionLayer.style.display]") == ["none", "none"]


def test_a_pinned_step_reads_left_to_right_what_leads_in_then_the_step_then_what_it_leads_to(graph):
    for key, before, after in [("browsing", ["seating"], ["ordering"]), ("ordering", ["browsing"], ["planning"]), ("seating", ["source"], ["browsing"]),
                               ("plating", ["stoves", "oven", "coffee"], ["running"]), ("planning", ["ordering"], ["stoves", "oven", "coffee"])]:
        graph.evaluate(f"graphPin('{key}')")
        pinned = box(graph, key)
        assert round(pinned["cx"]) == graph.evaluate("GRAPH_RING.x") and round((pinned["y"] + pinned["bottom"]) / 2) == graph.evaluate("GRAPH_RING.y"), key
        assert {pinned["x"] - box(graph, k)["right"] for k in before} == {64} and {box(graph, k)["x"] - pinned["right"] for k in after} == {64}, key
        for side in (before, after):
            middles = [(box(graph, k)["y"] + box(graph, k)["bottom"]) / 2 for k in side]
            assert sum(middles) / len(middles) == graph.evaluate("GRAPH_RING.y"), "a column of several is centred on the same line"
            assert middles == sorted(middles) and all(b - a == 96 + 32 for a, b in zip(middles, middles[1:])), key


def test_the_outcomes_of_a_pinned_step_stand_underneath_it(graph):
    for key, ends in [("ordering", ["noorder"]), ("plating", ["hungry"]), ("dining", ["out"]), ("seating", ["away"]), ("planning", ["hungry"])]:
        graph.evaluate(f"graphPin('{key}')")
        lowest = max(box(graph, k)["bottom"] for k in graph.evaluate("[...graphShown]") if k not in ends)
        assert all(box(graph, end)["y"] == lowest + 64 and round(box(graph, end)["cx"]) == graph.evaluate("GRAPH_RING.x") for end in ends), key


def test_a_pinned_outcome_is_at_the_bottom_with_the_steps_that_lead_to_it_in_a_row_above(graph):
    graph.evaluate("graphPin('hungry')")
    steps, end = [box(graph, k) for k in ["planning", "plating", "running"]], box(graph, "hungry")
    assert len({b["y"] for b in steps}) == 1 and [b["x"] for b in steps] == sorted(b["x"] for b in steps) and all(c["x"] - a["right"] == 32 for a, c in zip(steps, steps[1:]))
    assert end["y"] == steps[0]["bottom"] + 64 and round(end["cx"]) == graph.evaluate("GRAPH_RING.x")


def test_arrows_in_a_pinned_view_are_level_and_upright_and_turn_half_way(graph):
    for key in ["browsing", "ordering", "plating", "planning", "hungry", "source", "dining", "out"]:
        graph.evaluate(f"graphPin('{key}')")
        assert graph.evaluate("graphEdges.filter(edge => edge.line.style.display !== 'none').every(edge => edge.points.slice(1).every((point, i) => point.x === edge.points[i].x || point.y === edge.points[i].y))"), key
    graph.evaluate("graphPin('planning')")
    out = graph.evaluate("graphEdges.find(edge => edge.from === 'planning' && edge.to === 'stoves').points")
    assert out[1]["x"] - out[0]["x"] == 31 and out[1]["y"] == out[0]["y"] and out[2]["x"] == out[1]["x"], "at least 24 straight out of the box before it turns"
    assert len(graph.evaluate("graphEdges.find(edge => edge.from === 'planning' && edge.to === 'oven').points")) == 2, "in line: no turn at all"


def test_an_outcome_straight_below_its_step_has_an_upright_arrow(graph):
    for pin, edge in [("running", "running>hungry"), ("dining", "dining>out"), ("ordering", "ordering>noorder")]:
        graph.evaluate(f"graphPin('{pin}')")
        xs = graph.evaluate(f"graphEdges.find(edge => edge.from + '>' + edge.to === '{edge}').points.map(point => point.x)")
        assert len(set(xs)) == 1, edge


def test_the_resources_a_pinned_step_needs_stand_above_it_with_arrows_into_it(graph):
    graph.evaluate("graphPin('oven')")
    pools = graph.evaluate("graphPools.map(pool => [pool.id, pool.g.querySelector('.task-name').textContent, pool.squares.length])")
    assert pools == [["cooks", "Cooks", 6], ["oven", "Pizza oven", 1]]
    top = min(box(graph, key)["y"] for key in graph.evaluate("[...graphShown]"))
    assert all(graph.evaluate(f"Number(graphPools[{i}].g.querySelector('rect').getAttribute('y')) + 74") < top for i in range(2))
    arrows = graph.evaluate("[...graphPinLayer.querySelectorAll('path.loop-arrow')].map(path => [path.getAttribute('marker-end'), path.style.stroke])")
    assert arrows == [["url(#graph-arrow-actor)", "rgb(185, 188, 192)"], ["url(#graph-arrow-resource)", "rgb(167, 139, 250)"]], "from the cooks in grey, from the oven in violet"
    run_until(graph, "desEngine.resources.oven.allocated === 1")
    assert graph.evaluate("graphPools.map(pool => pool.note.textContent)")[1] == "0 of 1 free"


def test_plating_also_waits_for_the_other_parts_of_the_order(graph):
    graph.evaluate("graphPin('plating')")
    pools = graph.evaluate("graphPools.map(pool => [pool.id, pool.g.querySelector('.task-name').textContent, pool.g.querySelectorAll('rect')[1].getAttribute('fill')])")
    assert pools == [["cooks", "Cooks", "#b9bcc0"], ["parts", "Other parts of order", "#898781"]]
    run_until(graph, "desHeldForParts().length > 0")
    short = graph.evaluate("desHeldForParts().length")
    assert graph.evaluate("graphPools[1].note.textContent").startswith(f"{short} of ") and graph.evaluate("graphPools[1].squares.filter(square => square.classList.contains('used') && square.style.display !== 'none').length") == short
    click(graph, "graphPools[1].g.querySelector('rect')")
    assert about(graph)["name"] == "Other parts of the order" and graph.evaluate("GRAPH.plating.g.hasAttribute('data-selected')") is False


def test_resources_are_always_on_top_of_a_pinned_step(graph):
    for key in ["ordering", "plating", "seating", "running"]:
        graph.evaluate(f"graphPin('{key}')")
        top = min(box(graph, k)["y"] for k in graph.evaluate("[...graphShown]"))
        bottoms = graph.evaluate("graphPools.map(pool => Number(pool.g.querySelector('rect').getAttribute('y')) + 74)")
        assert bottoms and all(bottom == top - 64 for bottom in bottoms), key
        ends = graph.evaluate("[...graphPinLayer.querySelectorAll('path.loop-arrow')].map(path => path.getAttribute('d').split('L').at(-1).split(' ').map(Number))")
        pinned = box(graph, key)
        assert all(pinned["x"] < x < pinned["right"] and y == pinned["y"] - 3 for x, y in ends), key
    graph.evaluate("graphPin('ordering')")
    assert box(graph, "browsing")["right"] < box(graph, "ordering")["x"] and box(graph, "browsing")["y"] == box(graph, "ordering")["y"], "View menu is beside Order now, not above it"


def test_the_door_and_an_outcome_can_be_pinned_and_need_no_resources(graph):
    graph.evaluate("graphPin('source')")
    assert graph.evaluate("[[...graphShown], graphPools.length]") == [["source", "seating"], 0]
    graph.evaluate("graphPin('away')")
    assert graph.evaluate("[[...graphShown], graphPools.length]") == [["away", "seating"], 0]
    graph.evaluate("graphPin('hungry')")
    assert graph.evaluate("[[...graphShown], graphPools.length]") == [["hungry", "planning", "plating", "running"], 0]


def test_with_the_door_pinned_a_party_seated_at_once_is_seen_going_in(graph):
    run(graph, 30)
    graph.evaluate("graphPin('source')")
    settle(graph, 2)
    seen = graph.evaluate("""() => { const keys = new Set(); let last = null;
        for (let i = 0; i < 3000; i++) { tick(1 / 30); __advance(33); drawGraph(); for (const [key, token] of graphTokens) if (key.endsWith('/in')) { keys.add(key); last = [Math.round(token.x), Math.round(token.y)]; } }
        return { seen: keys.size, arrived: desEngine.arrived, y: last[1], sourceY: GRAPH.source.cy, left: [...graphTokens.keys()].filter(key => key.endsWith('/in')).length }; }""")
    assert seen["seen"] > 5 and seen["y"] == graph.evaluate("GRAPH.source.cy + GRAPH.source.dy") and seen["left"] <= 1, "each goes along the arrow into Get a table and is gone"


def test_unpinning_brings_the_whole_map_back(graph):
    whole = graph.evaluate("$('desgraph').getAttribute('viewBox')")
    graph.evaluate("graphPin('plating')")
    assert graph.evaluate("$('desgraph').getAttribute('viewBox')") != whole and graph.evaluate("$('desgraph').getAttribute('preserveAspectRatio')") == "xMidYMid"
    graph.evaluate("graphPin(null)")
    assert graph.evaluate("[$('desgraph').getAttribute('viewBox'), graphPinned, graphShown, graphPools.length, graphPinLayer.children.length]") == [whole, None, None, 0, 0]
    assert len(lines(graph)) == graph.evaluate("graphEdges.length") and graph.evaluate("Object.values(GRAPH).every(b => b.dx === graphWide * GRAPH_COLUMN[b.key] / 6 && b.g.style.display === '')")
    assert graph.evaluate("DES_RES.cooks.info.nodes.every(node => node.isConnected)"), "the pinned boxes that are gone no longer count as the resource's nodes"


def test_tokens_start_afresh_in_place_when_the_picture_changes(graph):
    run(graph, 120)
    graph.evaluate("graphPin('ordering'); drawGraph()")
    assert strays(graph) == [] and graph.evaluate("[...graphTokens.values()].every(token => !(token.route || []).length)")
    assert all(key in ("ordering", "browsing", "planning", "noorder") for key in graph.evaluate("[...graphTokens.values()].map(token => token.at)"))


def test_a_token_leaving_a_pinned_picture_follows_only_the_pinned_things_own_arrows(graph):
    graph.evaluate("graphPin('dining')")
    left = graph.evaluate("""() => { let going = 0; for (let i = 0; i < 9000; i++) { tick(1 / 30); __advance(33); drawGraph(); for (const token of graphTokens.values()) if (token.going && token.at === 'out') going++; } return going; }""")
    assert left > 0 and strays(graph) == []


# ---------- the badge ----------

def test_whatever_is_pinned_carries_a_grey_pin_badge_on_its_bottom_right_corner(graph):
    assert pinned_badges(graph) == []
    for key in ["plating", "out", "source"]:
        graph.evaluate(f"graphPin('{key}')")
        corner = box(graph, key)
        assert pinned_badges(graph) == [f"translate({corner['right'] - 1} {corner['bottom'] - 1})"], key
    look = graph.evaluate("(() => { const badge = graphPinLayer.querySelector('circle'); return [badge.getAttribute('fill'), badge.parentNode.querySelector('path').getAttribute('fill'), badge.parentNode.style.pointerEvents]; })()")
    assert look == ["#6a737b", "#fff", "none"], "grey, not blue: it states a fact, it is not a button"
    graph.evaluate("graphPin(null)")
    assert pinned_badges(graph) == []


def test_being_pinned_is_not_being_selected(graph):
    graph.evaluate("graphPin('plating'); select(DES_TASKS.oven.info)")
    assert graph.evaluate("[GRAPH.plating.g.hasAttribute('data-selected'), GRAPH.oven.g.hasAttribute('data-selected')]") == [False, True] and len(pinned_badges(graph)) == 1


# ---------- a resource ----------

@pytest.mark.parametrize("pool, steps", [("tables", ["seating"]), ("waiters", ["ordering", "running"]), ("cooks", ["planning", "stoves", "oven", "coffee", "plating"]),
                                           ("stoves", ["stoves"]), ("oven", ["oven"]), ("coffee", ["coffee"])])
def test_a_pinned_resource_stands_in_the_middle_with_the_steps_that_use_it_around_it(graph, pool, steps):
    graph.evaluate(f"graphPin('res:{pool}')")
    assert graph.evaluate("[...graphShown]") == steps
    centre = graph.evaluate("(() => { const r = graphPools[0].g.querySelector('rect'); return [Number(r.getAttribute('x')) + 62, Number(r.getAttribute('y')) + 37]; })()")
    assert centre == [graph.evaluate("GRAPH_RING.x"), graph.evaluate("GRAPH_RING.y")]
    places = [box(graph, key) for key in steps]
    assert all(abs(b["cx"] - centre[0]) > 150 or abs(b["cy"] - centre[1]) > 150 for b in places)
    overlap = lambda a, b: a["x"] < b["right"] and b["x"] < a["right"] and a["y"] < b["bottom"] and b["y"] < a["bottom"]
    middle = {"x": centre[0] - 62, "right": centre[0] + 62, "y": centre[1] - 37, "bottom": centre[1] + 37}
    assert not any(overlap(a, b) for i, a in enumerate(places) for b in places[i + 1:] + [middle])


def test_only_lines_from_the_pinned_resource_are_drawn(graph):
    graph.evaluate("graphPin('res:cooks')")
    assert lines(graph) == [], "no arrow of the process, not even between two steps that are both shown"
    arrows = graph.evaluate("[...graphPinLayer.querySelectorAll('path.loop-arrow')].map(path => path.getAttribute('d'))")
    assert len(arrows) == 5 and all(arrow.count("L") == 1 for arrow in arrows), "one straight arrow into each step"
    assert len(pinned_badges(graph)) == 1


def test_steps_go_round_a_resource_clockwise_from_its_left(graph):
    graph.evaluate("graphPin('res:cooks')")
    centre, places = [graph.evaluate("GRAPH_RING.x"), graph.evaluate("GRAPH_RING.y")], {key: box(graph, key) for key in ["planning", "stoves", "oven", "coffee", "plating"]}
    assert places["planning"]["cx"] < centre[0] and places["planning"]["cy"] == centre[1]
    assert places["stoves"]["cy"] < centre[1] and places["oven"]["cx"] > centre[0] and places["coffee"]["cy"] > centre[1] and places["plating"]["cy"] > centre[1]
    assert graph.evaluate("[graphRingPlace(0, 1), graphRingPlace(0, 2), graphRingPlace(1, 2)].map(place => [Math.round(place.x - GRAPH_RING.x), Math.round(place.y - GRAPH_RING.y)])") == [[270, 0], [-270, 0], [270, 0]]


def test_parties_are_still_shown_in_the_steps_of_a_pinned_resource(graph):
    graph.evaluate("graphPin('res:cooks')")
    run(graph, 240)
    assert graph.evaluate("graphTokens.size") > 0 and strays(graph) == []
    assert graph.evaluate("graphPools[0].note.textContent") == f"{resources(graph)['cooks']['capacity'] - resources(graph)['cooks']['allocated']} of 2 free"


def test_where_a_line_leaves_a_box(graph):
    points = graph.evaluate("[graphEdgePoint({ x: 0, y: 0 }, { x: 100, y: 0 }, 20, 10, 2), graphEdgePoint({ x: 0, y: 0 }, { x: 0, y: -100 }, 20, 10, 2), graphEdgePoint({ x: 0, y: 0 }, { x: 100, y: 100 }, 20, 10, 0)]")
    assert points == [{"x": 22, "y": 0}, {"x": 0, "y": -12}, {"x": 10, "y": 10}]


# ---------- one unit ----------

def test_one_unit_can_be_pinned_by_itself(graph):
    graph.evaluate("graphPin('unit:cooks:0')")
    assert graph.evaluate("[graphPools[0].g.querySelector('.task-name').textContent, graphPools[0].squares.length, [...graphShown]]") == ["Cook 1", 1, ["planning", "stoves", "oven", "coffee", "plating"]]
    assert graph.evaluate("[graphPinnedUnit('unit:cooks:0'), graphPinnedUnit('res:cooks'), graphPinnedUnit('plating'), graphPinnedResource('unit:cooks:0'), graphPinnedResource('plating'), graphPinnedResource(null)]") == [
        {"pool": "cooks", "index": 0}, None, None, "cooks", None, None]
    assert len(pinned_badges(graph)) == 1 and lines(graph) == []


def test_a_pinned_unit_says_what_it_is_doing_and_the_arrow_to_that_step_is_solid(graph):
    graph.evaluate("graphPin('unit:cooks:0')")
    settle(graph, 2)
    assert graph.evaluate("[graphPools[0].note.textContent, graphPools[0].squares[0].classList.contains('used')]") == ["Free", False]
    seen = graph.evaluate("""() => { const notes = new Set(), steps = new Set(); let wrong = 0, others = 0;
        for (let i = 0; i < 12000; i++) { tick(1 / 20); if (i % 10) continue; __advance(16); drawGraph();
            const pool = graphPools[0], unit = desEngine.resources.cooks.units[0], at = unit ? GRAPH_TASK_STEP[unit.task] || unit.task : null;
            const solid = Object.entries(pool.links).filter(([, link]) => link.style.strokeDasharray === 'none').map(([key]) => key);
            notes.add(pool.note.textContent.replace(/party .*/, 'party')); solid.forEach(key => steps.add(key));
            if ((solid[0] || null) !== at || pool.squares[0].classList.contains('used') !== Boolean(unit)) wrong++;
            for (const [key, token] of graphTokens) if (token.live && unit && !key.startsWith(unit.party)) others++; }
        return { notes: [...notes].sort(), steps: [...steps].sort(), wrong, others }; }""")
    assert seen["steps"] == ["coffee", "oven", "planning", "plating", "stoves"] and seen["wrong"] == 0 and seen["others"] == 0
    assert set(seen["notes"]) >= {"Baking for party", "Cooking for party", "Making coffee for party", "Planning the order of party", "Plating for party"}


def test_a_pinned_unit_that_is_out_or_not_on_shift_says_so(graph):
    graph.evaluate("graphPin('unit:waiters:1'); desEngine.setOut('waiters', 1, true)")
    settle(graph, 2)
    assert graph.evaluate("[graphPools[0].note.textContent, graphPools[0].squares[0].classList.contains('out')]") == ["Off sick", True]
    graph.evaluate("graphPin('unit:waiters:4')")
    settle(graph, 2)
    assert graph.evaluate("graphPools[0].note.textContent") == "Not on shift"
    graph.evaluate("graphPin('unit:oven:0'); desEngine.setOut('oven', 0, true)")
    settle(graph, 2)
    assert graph.evaluate("graphPools[0].note.textContent") == "Broken down"


def test_a_pinned_table_shows_who_has_it(graph):
    run_until(graph, "Boolean(desEngine.resources.tables.units[3])")
    graph.evaluate("graphPin('unit:tables:3')")
    settle(graph, 2)
    assert graph.evaluate("graphPools[0].note.textContent") == f"Taken by party {graph.evaluate('desEngine.parties.get(desEngine.resources.tables.units[3].party).number')}"


def test_a_selected_unit_stays_selected_when_it_is_pinned(graph):
    graph.evaluate("select(DES_RES.cooks.units[0].info); graphPin('unit:cooks:0')")
    assert graph.evaluate("graphPools[0].g.hasAttribute('data-selected')")
    graph.evaluate("select(DES_RES.tables.units[6].info); graphPin('res:tables')")
    assert graph.evaluate("graphPools[0].squares.findIndex(square => square.hasAttribute('data-selected'))") == 6


# ---------- what can be pinned ----------

def test_what_each_card_is_pinned_as(graph):
    targets = graph.evaluate("[DES_TASKS.oven.info, DES_RES.cooks.info, DES_RES.cooks.units[1].info, DES_RES.tables.units[6].info, desPartsInfo].map(graphPinTarget)")
    assert targets == ["oven", "res:cooks", "unit:cooks:1", "unit:tables:6", None]
    click(graph, "GRAPH.out.g.querySelector('rect')")
    assert graph.evaluate("graphPinTarget(selected)") == "out"
    click(graph, "GRAPH.source.g.querySelector('circle')")
    assert graph.evaluate("graphPinTarget(selected)") == "source"
    run(graph, 30)
    assert graph.evaluate("graphPinTarget(desPartyInfo([...desEngine.parties.keys()][0]))") == "party:" + graph.evaluate("[...desEngine.parties.keys()][0]")
    assert graph.evaluate("graphPinTarget(DES_QUEUE.run.info)") is None


# ---------- a party ----------

PARTY_STEPS = ["seating", "browsing", "ordering", "running", "dining"]


def arrow(page):
    """The steps the pinned party's arrow points at, each with "solid" or "dashed"."""
    return page.evaluate("Object.entries(graphPools[0].links).filter(([, link]) => link.style.display !== 'none').map(([key, link]) => [key, link.style.strokeDasharray === 'none' ? 'solid' : 'dashed'])")


def test_a_pinned_party_stands_in_the_middle_with_the_steps_it_takes_part_in_around_it(graph):
    run_until(graph, "desEngine.parties.size > 0")
    graph.evaluate("graphPin('party:' + [...desEngine.parties.keys()][0])")
    assert graph.evaluate("[...graphShown]") == PARTY_STEPS + ["noorder", "hungry", "out"], "the kitchen is out of the party's sight; a party inside cannot be turned away"
    assert graph.evaluate("graphPools[0].g.querySelector('.task-name').textContent").startswith("Party 1:") and len(pinned_badges(graph)) == 1
    centre = graph.evaluate("(() => { const r = graphPools[0].g.querySelector('rect'); return [Number(r.getAttribute('x')) + 62, Number(r.getAttribute('y')) + 37]; })()")
    assert centre == [graph.evaluate("GRAPH_RING.x"), graph.evaluate("GRAPH_RING.y")] and lines(graph) == []
    assert graph.evaluate("[graphPinnedParty('party:P12'), graphPinnedParty('res:cooks'), graphPinnedParty(null)]") == ["P12", None, None]


def test_the_arrow_points_at_the_step_the_party_is_at_dashed_while_it_waits_and_solid_while_it_is_served(graph):
    graph.evaluate("desEngine.changeCapacity('waiters', -1)")
    run_until(graph, "[...desEngine.parties.values()].some(party => party.state === 'READING_MENU')")
    graph.evaluate("window.mine = [...desEngine.parties.values()].find(party => party.state === 'READING_MENU').id; graphPin('party:' + mine)")
    seen = graph.evaluate("""() => { const seen = {}; let relaid = 0; const layer = graphPinLayer.firstChild;
        for (let i = 0; i < 20000 && desEngine.parties.has(mine); i++) { tick(1 / 20); if (i % 4) continue; __advance(16); drawGraph();
            const party = desEngine.parties.get(mine); if (!party) break; if (graphPinLayer.firstChild !== layer) relaid++;
            const shown = Object.entries(graphPools[0].links).filter(([, link]) => link.style.display !== 'none').map(([key, link]) => key + (link.style.strokeDasharray === 'none' ? ' solid' : ' dashed'));
            (seen[party.state] ||= new Set()).add(shown.join() + ' | ' + graphPools[0].note.textContent + ' | ' + [...graphTokens.values()].map(token => token.at).join()); }
        return { seen: Object.fromEntries(Object.entries(seen).map(([state, set]) => [state, [...set]])), relaid }; }""")
    states = seen["seen"]
    assert seen["relaid"] == 0, "nothing is laid out again as the party moves on"
    assert states["READING_MENU"] == ["browsing solid | Browsing the menu | browsing"]
    assert states["ORDERING"] == ["ordering solid | Ordering | ordering"] and states["EATING_AND_BILLING"] == ["dining solid | Dining | dining"]
    assert states["FOOD_RUNNING"] == ["running solid | Running the food | running"]
    for kitchen in ["WAITING_FOR_COOK", "PLANNING", "COOKING", "PLATING", "WAITING_FOR_WAITER_DELIVER"]:
        assert states.get(kitchen, ["running dashed | Waiting for the food | running"]) == ["running dashed | Waiting for the food | running"], kitchen
    assert "COOKING" in states and all(entry.split(" | ")[0] == "ordering dashed" for entry in states.get("WAITING_FOR_WAITER_ORDER", []))


def test_a_party_waiting_at_the_door_is_waiting_for_a_table(graph):
    graph.evaluate("for (let i = 0; i < 12; i++) desEngine.setOut('tables', i, true)")
    run_until(graph, "desEngine.queues.host.length > 0")
    graph.evaluate("graphPin('party:' + desEngine.queues.host[0])")
    settle(graph, 2)
    assert arrow(graph) == [["seating", "dashed"]] and graph.evaluate("graphPools[0].note.textContent") == "Waiting for table"


def test_only_the_pinned_partys_token_is_shown(graph):
    run(graph, 120)
    graph.evaluate("window.mine = [...desEngine.parties.keys()][0]; graphPin('party:' + mine)")
    run(graph, 20)
    assert graph.evaluate("[...graphTokens.keys()]") in ([graph.evaluate("mine")], []) and strays(graph) == []


def test_a_party_that_leaves_stays_pinned_and_says_its_visit_is_over(graph):
    run_until(graph, "desEngine.parties.size > 0")
    graph.evaluate("window.mine = [...desEngine.parties.keys()][0]; select(desPartyInfo(mine)); graphPin('party:' + mine)")
    run_until(graph, "!desEngine.parties.has(mine)")
    assert graph.evaluate("[graphPinned, selected === desPartyInfo(mine), graphPools[0].note.textContent]") == [f"party:{graph.evaluate('mine')}", True, "Visit over"]
    assert arrow(graph) == [["out", "solid"]] and graph.evaluate("graphTokens.size") == 0 and len(pinned_badges(graph)) == 1
    assert graph.evaluate("graphPinTarget(selected)") == graph.evaluate("graphPinned"), "so it can still be unpinned by hand"
    graph.evaluate("graphPin(null)")
    assert graph.evaluate("graphPinned") is None


def test_a_party_that_has_left_can_be_pinned_again_from_its_card(graph):
    run(graph, 30)
    run_until(graph, "desEngine.departed > 0")
    gone = graph.evaluate("[...desPartyInfos.keys()].find(id => !desEngine.parties.has(id))")
    graph.evaluate(f"graphPin('party:{gone}')")
    settle(graph, 2)
    assert graph.evaluate("[[...graphShown].length, graphPools[0].note.textContent]") == [8, "Visit over"]


def test_where_a_party_sees_itself(graph):
    places = graph.evaluate("['WAITING_FOR_TABLE', 'READING_MENU', 'WAITING_FOR_WAITER_ORDER', 'ORDERING', 'WAITING_FOR_COOK', 'COOKING', 'WAITING_FOR_PLATING', 'FOOD_RUNNING', 'EATING_AND_BILLING', 'DEPARTED'].map(state => graphPartyPlace({ state }).join(' '))")
    assert places == ["seating wait", "browsing active", "ordering wait", "ordering active", "running wait", "running wait", "running wait", "running active", "dining active", "running wait"]


def test_all_the_parties_can_be_pinned_like_all_the_cooks(graph):
    run(graph, 120)
    click(graph, "GRAPH_TOP[0].g.querySelector('rect')")
    assert graph.evaluate("graphPinTarget(selected)") == "parties"
    graph.evaluate("graphPin('parties')")
    run(graph, 5)
    inside = graph.evaluate("desEngine.parties.size")
    assert graph.evaluate("[...graphShown]") == PARTY_STEPS + ["away", "noorder", "hungry", "out"] and lines(graph) == [] and len(pinned_badges(graph)) == 1
    assert graph.evaluate("[graphPools[0].g.querySelector('.task-name').textContent, graphPools[0].note.textContent, graphPools[0].squares.filter(square => square.style.display !== 'none').length]") == ["Parties", f"{inside} in the building", inside]
    assert graph.evaluate("graphPinLayer.querySelectorAll('path.loop-arrow').length") == 9
    assert sorted(graph.evaluate("[...graphTokens.keys()]")) == sorted(graph.evaluate("[...desEngine.parties.keys()]")), "every party, once"
    assert strays(graph) == []
    at = graph.evaluate("Object.fromEntries([...graphTokens].map(([id, token]) => [id, token.at]))")
    assert at == graph.evaluate("Object.fromEntries([...desEngine.parties.values()].map(party => [party.id, graphPartyPlace(party)[0]]))")
    click(graph, "graphPools[0].squares[0]")
    assert about(graph)["name"].startswith("Party ")


def test_the_steps_of_a_visit_go_over_the_top_and_the_outcomes_along_the_bottom(graph):
    for key, ends in [("parties", ["away", "noorder", "hungry", "out"]), ("party:P1", ["noorder", "hungry", "out"])]:
        run_until(graph, "desEngine.parties.has('P1') || desPartyInfos.has('P1')")
        settle(graph, 2)
        graph.evaluate(f"graphPin('{key}')")
        centre = [graph.evaluate("GRAPH_RING.x"), graph.evaluate("GRAPH_RING.y")]
        steps, outs = [box(graph, step) for step in PARTY_STEPS], [box(graph, end) for end in ends]
        assert [round(b["cx"]) for b in steps] == sorted(round(b["cx"]) for b in steps) and all(b["cy"] <= centre[1] for b in steps), key
        assert [round(b["cx"]) for b in outs] == sorted(round(b["cx"]) for b in outs) and all(b["y"] > centre[1] + 37 for b in outs), key
        everything = steps + outs + [{"x": centre[0] - 62, "right": centre[0] + 62, "y": centre[1] - 37, "bottom": centre[1] + 37}]
        assert not any(a["x"] < b["right"] and b["x"] < a["right"] and a["y"] < b["bottom"] and b["y"] < a["bottom"] for i, a in enumerate(everything) for b in everything[i + 1:]), key


def test_a_party_that_gave_up_points_at_the_way_it_left(graph):
    graph.evaluate("desEngine.changeCapacity('waiters', -1); desEngine.changeCapacity('waiters', -1)")
    run_until(graph, "desEngine.parties.size > 0")
    graph.evaluate("window.mine = [...desEngine.parties.keys()][0]; graphPin('party:' + mine)")
    run_until(graph, "!desEngine.parties.has(mine)")
    assert arrow(graph) == [["noorder", "solid"]]
    graph.evaluate("graphPin(null); desEngine.changeCapacity('waiters', 1); desEngine.changeCapacity('waiters', 1); desEngine.changeCapacity('cooks', -1); desEngine.changeCapacity('cooks', -1)")
    settle(graph, 2)
    run_until(graph, "[...desEngine.parties.values()].some(party => party.timestamps.orderPlaced !== undefined)")
    graph.evaluate("window.mine = [...desEngine.parties.values()].find(party => party.timestamps.orderPlaced !== undefined).id; graphPin('party:' + mine)")
    run_until(graph, "!desEngine.parties.has(mine)")
    assert arrow(graph) == [["hungry", "solid"]]


def test_a_pinned_cook_finishing_work_for_a_party_that_walked_out_says_so(graph):
    graph.evaluate("desEngine.changeCapacity('cooks', -1); graphPin('unit:cooks:0')")
    seen = graph.evaluate("""() => { for (let i = 0; i < 60000; i++) { tick(1 / 20); const unit = desEngine.resources.cooks.units[0];
            if (unit && !desEngine.parties.has(unit.party)) { __advance(16); drawGraph(); return graphPools[0].note.textContent; } }
        return null; }""")
    assert seen is not None and seen.endswith(" party that left")


def test_with_turned_away_pinned_parties_are_seen_coming_out_of_get_a_table(graph):
    graph.evaluate("for (let i = 0; i < 12; i++) desEngine.setOut('tables', i, true); graphPin('away')")
    settle(graph, 2)
    seen = graph.evaluate("""() => { const keys = new Set(); let first = null; for (let i = 0; i < 6000; i++) { tick(1 / 30); __advance(33); drawGraph();
            for (const [key, token] of graphTokens) if (key.endsWith('/away')) { keys.add(key); first ||= [Math.round(token.x), Math.round(token.y)]; } }
        return [keys.size, desEngine.balked, first]; }""")
    seating = box(graph, "seating")
    assert seen[0] == seen[1] > 0 and seating["x"] <= seen[2][0] <= seating["right"] and seating["y"] <= seen[2][1] <= seating["bottom"] + 20, "each sets off from Get a table"
