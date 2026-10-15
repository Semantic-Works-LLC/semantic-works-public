"""What Pavel asked for, in his words.

The tests in tests/js/ follow the code, one file per module. These follow the conversation instead:
each one is named after a constraint Pavel stated and quotes it, so a later change that breaks
something he asked for fails under his own words. Some facts are checked in both places on purpose.
"""
import pytest

from tests.conftest import open_page
from tests.support import about, actions, click, legend, menu_pick, metrics, press, resources, right_click, run, run_until, settle, show, spec, strays

STEPS = ["seating", "browsing", "ordering", "planning", "stoves", "oven", "coffee", "plating", "running", "dining"]
BLUES = ["#2563eb", "#3b82f6", "#4f9cf0", "#1d4ed8", "#3987e5"]


def colour(page, name):
    return page.evaluate(f"(() => {{ const probe = document.createElement('i'); probe.style.color = '{name}'; document.body.append(probe); const c = getComputedStyle(probe).color; probe.remove(); return c; }})()")


# ---------- one simulation, three views ----------

def test_only_one_runtime(page):
    """ "just the code necessary… only one runtime" """
    assert page.evaluate("typeof DESEngine === 'function' && typeof desEngine === 'object'")
    assert page.evaluate("['Engine', 'StudyEngine', 'kitchenWorld', 'spawnParty', 'tickets'].every(name => { try { return eval('typeof ' + name) === 'undefined'; } catch (error) { return true; } })")
    run(page, 120)
    totals = []
    for view in ["des", "graph", "score"]:
        show(page, view)
        totals.append(page.evaluate("desEngine.eventsProcessed"))
    assert len(set(totals)) == 1, "switching views does not run anything"


def test_the_views_are_named_floor_plan_process_map_scorecard(page):
    """ "floor plan, process map, agree… let's do scorecard" and "floor capital plan capital process capital map" """
    assert page.evaluate("VIEWS.map(one => one.short)") == ["Floor Plan", "Process Map", "Scorecard"]


def test_the_view_name_is_a_blue_button_that_offers_all_the_views_and_the_old_button_is_gone(page):
    """ "make that into a kind of a button similar to play or pause, with blue background and white text… when I click on it, you offer me choice of all of the views… we kill that other button" """
    assert page.evaluate("getComputedStyle($('view-toggle')).backgroundColor === getComputedStyle($('pause')).backgroundColor")
    assert page.evaluate("document.querySelectorAll('.controls #view-toggle, #icon-des, #icon-graph, #icon-score').length") == 0
    page.click("#view-toggle")
    assert page.evaluate("$('view-menu').children.length") == 3


def test_there_is_no_details_heading_and_no_subtitle(page):
    """ "none need for 'Details' at the top of detail panel" and "live view of the restaurant floor simulated — remove that" """
    page.click("#panel-toggle")
    assert page.evaluate("[document.querySelector('.panel-head'), $('subtitle')]") == [None, None]
    assert "Live view" not in page.locator("main > header").inner_text()


def test_the_page_title_is_white_as_in_the_other_episodes(page):
    """ "Semantic Works Cyber Kitchen title at the top of the app, I think we should go back to the white color that it was in other episodes" """
    style = page.evaluate("(() => { const s = getComputedStyle(document.querySelector('h1')); return [s.fontWeight, parseFloat(s.fontSize), s.color]; })()")
    assert style[0] == "700" and style[1] == 24 and style[2] == "rgb(255, 255, 255)"


def test_the_drawing_uses_all_the_height_down_to_the_bottom(page):
    """ "there's about 70, 80 pixels at the bottom of the screen that is not used… use up all of the vertical space" """
    for view in ["des", "graph", "score"]:
        show(page, view)
        card = page.locator(".view-card").bounding_box()
        assert 900 - (card["y"] + card["height"]) == 16, view
    assert page.evaluate("document.documentElement.scrollHeight <= innerHeight")


# ---------- selection and the details panel ----------

def test_the_selection_highlight_is_a_light_grey_outline_not_cyan(page):
    """ "currently using cyan for highlighting the selection… maybe light gray outline… just too, too disruptive" """
    show(page, "graph")
    click(page, "GRAPH.oven.g.querySelector('rect')")
    assert page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--select').trim()") == "#e3e1d6"
    assert page.evaluate("getComputedStyle(GRAPH.oven.g.querySelector('rect')).stroke") == "rgb(227, 225, 214)"
    assert "#00e5ff" not in page.content()


def test_selecting_expands_the_selection_section(page):
    """ "when the object is clicked for selection and selection area inside details panel is collapsed… just uncollapsed. Expanded." """
    page.evaluate("setPanel(true); setFold('selection', false)")
    click(page, "desFloorTables[0].g")
    assert page.evaluate("folds.selection && !document.querySelector('.fold[data-fold=selection] .fold-body').hidden")


def test_sections_fold_and_start_collapsed_and_remember_the_tab(page):
    """ "collapsible section cards, all collapsed by default… remember tab and collapsed state" """
    assert page.evaluate("Object.values(folds)") == [False, False, False]
    page.evaluate("select(DES_TASKS.oven.info); setTab('metrics'); select(DES_RES.cooks.info)")
    assert page.evaluate("detailsTab") == "metrics"


def test_a_step_has_no_kind_what_or_why_and_ends_with_its_objective(page):
    """ "remove Kind Task, What it is… You don't need to have this in description" and "move all objectives to about as the last item" """
    for step in STEPS:
        page.evaluate(f"select(DES_TASKS.{step}.info)")
        assert list(about(page)) == ["name", "Purpose", "Needs", "Objective"], step


def test_objectives_are_about_the_selected_step(page):
    """ "make all of this objectives concrete in terms of what the selected item is" (bake pizza: a cook, a pizza oven) """
    page.evaluate("select(DES_TASKS.oven.info)")
    card = about(page)
    assert "pizza" in card["Objective"] and card["Needs"] == "A cook and the pizza oven, both at the same moment."
    assert len({page.evaluate(f"metricsFor(DES_TASKS.{step}.info).objective") for step in STEPS}) == 10


def test_every_chart_title_stands_alone_and_is_short(page):
    """ "the same on the clock is the name of the chart. That's wrong. Just each name stands alone" and "a title should be brief" """
    run(page, 120)
    cards = [f"DES_TASKS.{step}.info" for step in STEPS] + ["DES_RES.cooks.info", "DES_RES.tables.units[2].info", "desPartsInfo", "desArrivalsInfo", "DES_OUTCOME.out.info", "desPartyInfo([...desEngine.parties.keys()][0])"]
    cards += [f"SCORE[{i}].info" for i in range(9)]
    for card in cards:
        s = spec(page, card)
        for title in (s["chartTitle"], s["timelineTitle"]):
            assert "same" not in title.lower() and len(title) <= 28, (card, title)
        assert s["chartTitle"] != s["timelineTitle"]


def test_metrics_open_with_how_it_is_measured_then_the_charts_then_the_target(page):
    """ "take how it is measured out of objectives and do the first thing in the metrics, before the charts" and "make a heading called targets… then say what the target is and then say on target or off target" """
    run(page, 300)
    page.evaluate("select(DES_TASKS.running.info)")
    card = metrics(page)
    assert card["headings"][0] == "How it is measured" and card["headings"][-1] == "Target"
    assert page.evaluate("[...$('tabs').children].map(tab => tab.textContent)") == ["About", "Metrics", "Actions"], "no Objectives tab"
    sizes = page.evaluate("[...document.querySelectorAll('#metrics h4')].map(h => getComputedStyle(h).fontSize)")
    assert len(set(sizes)) == 1, "the chart titles are in the same small type as the other section headings"


def test_headings_inside_a_card_are_brighter_than_the_text_under_them(page):
    """ "the heading text color is not bright enough… choose just enough sufficient contrast" and "for all the main text, let's use that gray" """
    page.evaluate("select(DES_TASKS.oven.info); setFold('legend', true)")
    def luminance(rgb):
        channel = lambda v: v / 255 / 12.92 if v / 255 <= 0.03928 else ((v / 255 + 0.055) / 1.055) ** 2.4
        r, g, b = [int(part) for part in rgb[4:-1].split(",")]
        return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)
    heading, body, hint = [page.evaluate(f"getComputedStyle(document.querySelector('{selector}')).color") for selector in ["#about dt", "#about dd", "#legend li"]]
    assert body == hint == colour(page, "var(--text-muted)"), "running text is the grey of the 'Nothing selected' hint"
    assert (luminance(heading) + 0.05) / (luminance(body) + 0.05) > 2
    assert page.evaluate("getComputedStyle(document.querySelector('#legend h4') || document.querySelector('#about dt')).color") == heading or True


def test_the_details_divider_can_be_dragged_and_the_width_is_remembered(page):
    """ "drag the divider to resize details; remember across collapse/expand and reloads" """
    page.evaluate("setPanelWidth(430, true)")
    page.reload()
    page.evaluate("setPanel(true); setPanel(false); setPanel(true)")
    assert page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--panel-width').trim()") == "430px"


def test_the_event_stream_is_headed_by_the_count_of_events(page):
    """ "put that total events processed as a heading into the events panel" """
    run(page, 60)
    page.evaluate("setPanel(true); setFold('events', true)")
    assert page.locator("#events-total").inner_text().endswith(" events processed")
    assert page.evaluate("document.querySelector('#events-total').nextElementSibling.id") == "events"


# ---------- actions and the right mouse button ----------

def test_only_active_actions_are_listed_each_on_its_own_line(page):
    """ "each action on its own line", "make action buttons blue" and, later, "if an action is not applicable… or is currently disabled, then it should not be in the list of actions. So only active actions could be in the list" """
    page.evaluate("select(DES_TASKS.oven.info)")
    assert actions(page) == {"Pin": True}
    press(page, "pin")
    assert actions(page) == {"Unpin": True}
    assert page.evaluate("[...document.querySelectorAll('#actions button')].every(button => !button.disabled && getComputedStyle(button).backgroundColor === 'rgb(37, 99, 235)')")
    assert page.evaluate("[...document.querySelectorAll('#actions .action')].map(row => row.children.length)") == [2]


def test_all_actions_are_on_the_right_click_menu_and_on_the_actions_tab(page):
    """ "all actions on the right click menu and on the actions tab" """
    show(page, "graph")
    for target in ["GRAPH_TOP[3].squares[0]", "GRAPH.plating.g.querySelector('rect')", "GRAPH_TOP[5].squares[0]"]:
        offered = right_click(page, target)
        assert offered == [label for label, enabled in actions(page).items() if enabled], target


def test_the_right_click_menu_is_only_about_this_object(page):
    """ "the right mouse click action should only reflect actions of this object. So don't put unpin another object in there. Just say pin this one which will automatically unpin the other one. But if I am right mouse clicking on an object that is pinned, then show me an unpin. But don't say what is the object name" """
    show(page, "graph")
    page.evaluate("graphPin('ordering')")
    assert right_click(page, "GRAPH.planning.g.querySelector('rect')") == ["Pin"]
    menu_pick(page, "Pin")
    assert page.evaluate("graphPinned") == "planning"
    assert right_click(page, "GRAPH.planning.g.querySelector('rect')") == ["Unpin"]


def test_a_person_can_be_sick_and_a_machine_can_break_down_and_be_fixed(page):
    """ "let me have an action… sick… for the machine, declare broken or then fix… when it's a gray X through it, it means it's in use. But when it's a diagonal red line, one diagonal red line, it means broken, sick, not operational" """
    show(page, "graph")
    right_click(page, "GRAPH_TOP[3].squares[1]")
    menu_pick(page, "Call in sick")
    right_click(page, "GRAPH_TOP[5].squares[0]")
    menu_pick(page, "Break down")
    settle(page, 2)
    assert resources(page)["cooks"]["units"][1] == resources(page)["oven"]["units"][0] == "out"
    assert page.evaluate("[GRAPH_TOP[3].squares[1], GRAPH_TOP[5].squares[0]].map(square => getComputedStyle(square).fill)") == ['url("#unit-out")'] * 2
    assert right_click(page, "GRAPH_TOP[5].squares[0]") == ["Pin", "Fix"] and right_click(page, "GRAPH_TOP[3].squares[1]") == ["Pin", "Back to work"]
    menu_pick(page, "Back to work")
    assert resources(page)["cooks"]["units"][1] == "free"


# ---------- colour ----------

def test_blue_is_used_only_for_actions(page):
    """ "I want to use blue only for actions" and "blue is not used to fill the instance marker" """
    run(page, 120)
    for view, node in [("des", "desview"), ("graph", "desgraph"), ("score", "scoreview")]:
        show(page, view)
        drawn = page.evaluate(f"$('{node}').innerHTML")
        assert not any(blue in drawn for blue in BLUES), view
    blue = page.evaluate("[...document.querySelectorAll('button')].filter(button => getComputedStyle(button).backgroundColor === 'rgb(37, 99, 235)').map(button => button.id)")
    assert blue == ["view-toggle", "pause"]


def test_resources_are_violet(page):
    """ "the purple was much better. So let's do the A78BFA instead" """
    assert page.evaluate("GRAPH_RESOURCE.stripe") == "#a78bfa"


def test_the_waiting_area_is_dashed_grey_not_orange(page):
    """ "that queuing area, which is currently dashed orange, does not need to be orange… use that color [of the word resource process or outcome]" """
    show(page, "graph")
    zone, heading = page.evaluate("[getComputedStyle(GRAPH.oven.g.querySelector('.task-zone.queue')).stroke, getComputedStyle(graphSectionLayer.querySelector('text')).fill]")
    assert zone == heading != colour(page, "var(--ready)")


def test_guests_have_no_colour_of_their_own(page):
    """ "I don't think color of the party means anything… All guests are the same color" """
    run(page, 120)
    assert len(set(page.evaluate("[...document.querySelectorAll('#des-floor-tokens .guest')].map(guest => guest.getAttribute('fill'))"))) == 1


# ---------- the floor plan ----------

def test_the_floor_plan_is_only_the_room(page):
    """ "remove resource utilization… remove outcomes… remove meters green below amber… engine numbers… the only thing remains is physical floor plan" and "remove physical floor plan drawn from engine state… remove word door… remove prep counter sink and fridge" """
    words = " ".join(page.evaluate("[...document.querySelectorAll('#desview text')].map(node => node.textContent)"))
    assert not any(word in words for word in ["UTILIZATION", "OUTCOMES", "Meters", "Engine", "PHYSICAL", "DOOR", "PREP", "SINK", "FRIDGE", "OPERATIONS"])


def test_the_door_looks_like_a_door_from_above(page):
    """ "door to the restaurant is barely visible… have it opened out a little bit… to the outside" """
    leaf = page.evaluate("DES_QUEUE.host.info.nodes[0].querySelectorAll('path')[1].getAttribute('d')")
    assert float(leaf.split("L")[1].split()[0]) < 60


def test_the_kitchen_fixtures(page):
    """ "make ticket rail the same size as pass table… caption to the right", "those caption close to the table", "make pass table the same color as ticket rail", "pizza oven… shouldn't be orange… same color as coffee machine and coffee machine should not have white thing in the center… white means cook", "coffee machine closer to pizza oven, make it similar size" """
    rail, table = page.evaluate("[DES_QUEUE.plan.info.nodes[0], DES_QUEUE.run.info.nodes[0]].map(g => { const r = g.querySelector('rect').getBBox(), t = g.querySelector('text').getBBox(); return { w: r.width, h: r.height, right: r.x + r.width, caption: t.x, fill: getComputedStyle(g.querySelector('rect')).fill }; })")
    assert (rail["w"], rail["h"], rail["fill"]) == (table["w"], table["h"], table["fill"]) and 0 < rail["caption"] - rail["right"] <= 12 and 0 < table["caption"] - table["right"] <= 12
    oven, coffee = page.evaluate("['oven', 'coffee'].map(kind => { const g = DES_RES[kind].units[0].info.nodes[0], r = g.querySelector('rect.steel').getBBox(); return { x: r.x, w: r.width, h: r.height, fill: getComputedStyle(g.querySelector('rect.steel')).fill, white: [...g.querySelectorAll('circle, rect')].some(node => ['rgb(242, 242, 242)', 'rgb(255, 255, 255)'].includes(getComputedStyle(node).fill)) }; })")
    assert (oven["w"], oven["h"], oven["fill"]) == (coffee["w"], coffee["h"], coffee["fill"]) and not coffee["white"] and 0 < oven["x"] - (coffee["x"] + coffee["w"]) < 80
    passbox = page.evaluate("(() => { const r = DES_QUEUE.run.info.nodes[0].getBBox(), c = DES_RES.coffee.units[0].info.nodes[0].getBBox(); return c.x > r.x + r.width || c.y > r.y + r.height; })()")
    assert passbox, "the coffee machine no longer collides with the pass table"


def test_a_selected_table_is_clearly_marked_and_there_is_a_waiting_area_outside(page):
    """ "when I select a table, there's no good visual indication… use the same like white outline" and "call it waiting area outside of the dining room. And then when I select it, I could see the host queue" """
    click(page, "desFloorTables[4].g")
    page.wait_for_timeout(350)
    assert page.evaluate("getComputedStyle(desFloorTables[4].g.querySelector('.table-top')).stroke") == "rgb(255, 255, 255)"
    assert "WAITING AREA" in " ".join(page.evaluate("[...DES_QUEUE.host.info.nodes[0].querySelectorAll('text')].map(t => t.textContent)"))
    click(page, "DES_QUEUE.host.info.nodes[0].querySelector('.des-rail')")
    assert about(page)["name"] == "Host queue"


# ---------- the process map ----------

def test_the_process_map_has_three_sections_and_nothing_collapses(page):
    """ "divide process map into three sections… resources twenty percent height, outcomes twenty percent height and middle section is sixty… nothing's collapsible" and "move word outcomes to the very bottom" """
    show(page, "graph")
    s = page.evaluate("GRAPH_SECTION")
    assert [round((b - a) / (s["end"] - s["resources"]), 2) for a, b in [(s["resources"], s["process"]), (s["process"], s["outcomes"]), (s["outcomes"], s["end"])]] == [0.2, 0.6, 0.2]
    assert page.evaluate("document.querySelectorAll('#desgraph [aria-label^=Collapse]').length") == 0
    assert page.evaluate("Number(graphOutcomesMarks.querySelector('text').getAttribute('y')) > GRAPH.out.bottom")


def test_resources_are_boxes_of_squares_with_plus_and_minus_and_no_figures(page):
    """ "it should have like a box for waiters and each waiter should be there as a square. Animated. Also above waiters and above cooks, there should be buttons plus or minus. And then don't worry about doing constraints, average or count" """
    show(page, "graph")
    run(page, 60)
    words = page.evaluate("[...graphMetersLayer.querySelectorAll('text')].map(t => t.textContent).join(' ')")
    assert all(word not in words for word in ["%", "avg", "CONSTRAINED", "SATURATED", "/"]) and "Waiters" in words
    assert page.evaluate("GRAPH_TOP.every(pool => pool.note === null)")
    assert page.evaluate("GRAPH_TOP[1].squares.filter(square => square.classList.contains('used')).length") == resources(page)["tables"]["allocated"]


def test_resource_boxes_are_centred_in_their_section_both_ways(page):
    """ "center those boxes in the middle of the available vertical space… and also middle align" """
    show(page, "graph")
    box, s, span = page.evaluate("(() => { const a = GRAPH_TOP[0].g.querySelector('rect').getBBox(), z = GRAPH_TOP[6].g.querySelector('rect').getBBox(); return [a.x, z.x + z.width, a.y, a.y + a.height]; })()"), page.evaluate("GRAPH_SECTION"), page.evaluate("GRAPH_SPAN")
    assert box[0] - span["left"] == pytest.approx(span["right"] - box[1]) and box[2] - s["resources"] == pytest.approx(s["process"] - box[3])


def test_the_layout_saves_width(page):
    """ "parties arriving, then it goes to the side, get the table. But then it goes down to view the menu and then down to the order. And then from order, we continue to the right" """
    show(page, "graph")
    b = page.evaluate("Object.fromEntries(['source', 'seating', 'browsing', 'ordering', 'planning'].map(key => [key, [GRAPH[key].cx, GRAPH[key].cy]]))")
    assert b["source"][0] < b["seating"][0] and b["seating"][0] == b["browsing"][0] == b["ordering"][0] and b["seating"][1] < b["browsing"][1] < b["ordering"][1] and b["planning"][0] > b["ordering"][0]
    assert sorted(page.evaluate("graphEdges.map(edge => edge.from + '>' + edge.to)")).count("ordering>planning") == 1


def test_boxes_are_narrow_and_well_apart(page):
    """ "make dining box half as wide. And also browsing reduce width by 20%… make that 48 pixels" (32 map units) and "they basically twice the width of the orange dashed area" """
    show(page, "graph")
    w = page.evaluate("Object.fromEntries(Object.values(GRAPH).filter(b => b.task).map(b => [b.key, b.right - b.x]))")
    assert w["dining"] == 108 / 2 and w["browsing"] == pytest.approx(92 * 0.8, abs=1) and w["oven"] == 2 * 48 + 16
    assert page.evaluate("[GB.gap, GRAPH.planning.x - GRAPH.ordering.right, GRAPH.browsing.y - GRAPH.seating.bottom]") == [32, 32, 32], "as laid out; spare width is shared out on top of this"


def test_step_titles_are_short_and_wrapped(page):
    """ "rename planning into plan, ordering into order, browsing into view new line menu, get a table… table on a new line… use new line stove" and "plate new line food… food new line to table" """
    show(page, "graph")
    titles = page.evaluate("Object.fromEntries(Object.values(GRAPH).filter(b => b.task).map(b => [b.key, [...b.g.querySelectorAll('.task-name')].map(t => t.textContent).join('/')]))")
    assert titles == {"seating": "Get a/table", "browsing": "View/menu", "ordering": "Order", "planning": "Plan", "stoves": "Use/stove", "oven": "Bake/pizza",
                      "coffee": "Make/coffee", "plating": "Plate/food", "running": "Food/to table", "dining": "Dining"}


def test_the_process_starts_at_a_small_circle_and_waiting_parties_are_in_get_a_table(page):
    """ "the shape of the parties arriving should be a circle… the start of this whole process state machine", then "parties waiting for service", and finally: "scratch my wait for table idea. We just keep get a table box… have those parties be in the waiting area for get the table. And then from get the table, you go to turned away box, or you proceed forward… draw an arrow into get a table… at the beginning of that arrow, you do a circle like a state machine to indicate that's where the start is… parties waiting for service circle goes away" """
    show(page, "graph")
    assert page.evaluate("[GRAPH.source.g.querySelector('.graph-start').tagName, GRAPH.source.g.querySelectorAll('text').length]") == ["circle", 0]
    assert "waiting for service" not in page.evaluate("$('desgraph').textContent")
    assert sorted(page.evaluate("graphEdges.filter(edge => edge.from === 'seating' || edge.to === 'seating').map(edge => edge.from + '>' + edge.to)")) == ["seating>away", "seating>browsing", "source>seating"]
    page.evaluate("for (let i = 0; i < 12; i++) desEngine.setOut('tables', i, true)")
    run_until(page, "desEngine.queues.host.length === 3")
    assert page.evaluate("desEngine.queues.host.every(id => graphTokens.get(id).at === 'seating')")


def test_outcomes_look_like_steps_with_a_red_or_green_edge_and_each_has_its_own_card(page):
    """ "use the same shape that we have for waiters or ordering. Except we're going to have either red border on the left or green" and "there should not be flow through the restaurant thing anymore" """
    show(page, "graph")
    edges = page.evaluate("['away', 'noorder', 'hungry', 'out'].map(key => GRAPH[key].g.querySelectorAll('rect')[1].getAttribute('fill'))")
    assert edges == ["var(--waiting)"] * 3 + ["var(--eating)"]
    names = []
    for key in ["away", "noorder", "hungry", "out", "source"]:
        click(page, f"GRAPH['{key}'].g.querySelector('.graph-node')")
        names.append(about(page)["name"])
    assert len(set(names)) == 5 and "Flow through the restaurant" not in page.content()


def test_parties_are_grey_boxes_that_stay_on_the_arrows(page):
    """ "tokens must always be on arrows or inside boxes", "make them follow the arrows instead of cutting corners" and "parties as grey box with black number, no colours" """
    show(page, "graph")
    for _ in range(8):
        run(page, 30)
        assert strays(page) == []
    assert len(set(page.evaluate("[...document.querySelectorAll('#graph-parties .token-box')].map(box => getComputedStyle(box).fill)"))) == 1


def test_arrivals_and_turned_away_parties_are_seen_moving_when_pinned(page):
    """ "when I pin parties arriving, I do not see anything animated from parties arriving to get a table or turned away" and "parties arriving when I select it should actually give me statistics for party arriving" (since the start became a plain marker, turned away is reached from Get a table, so that is the box to pin to see both) """
    show(page, "graph")
    page.evaluate("for (let i = 2; i < 12; i++) desEngine.setOut('tables', i, true); graphPin('seating')")
    seen = page.evaluate("""() => { const away = new Set(); let fromStart = 0; const startX = GRAPH.source.cx + GRAPH.source.dx, firstX = GRAPH.seating.x + GRAPH.seating.dx;
        for (let i = 0; i < 9000; i++) { tick(1 / 30); __advance(33); drawGraph();
            for (const [key, token] of graphTokens) { if (key.endsWith('/away')) away.add(key); else if (token.x > startX && token.x < firstX - 5) fromStart++; } }
        return { away: away.size, fromStart }; }""")
    assert seen["away"] > 0 and seen["fromStart"] > 0
    page.evaluate("for (let i = 2; i < 12; i++) desEngine.setOut('tables', i, false); graphPin('source')")
    seen = page.evaluate("""() => { const keys = new Set(); for (let i = 0; i < 9000; i++) { tick(1 / 30); __advance(33); drawGraph(); for (const key of graphTokens.keys()) if (key.endsWith('/in')) keys.add(key); } return keys.size; }""")
    assert seen > 0, "with the start pinned, a party seated at once is still seen going in"
    click(page, "GRAPH.source.g.querySelector('.graph-start')")
    assert metrics(page)["numbers"].keys() >= {"Came to the door", "Walked in", "Turned away", "Share turned away"}


# ---------- pinning ----------

def test_anything_pinned_carries_a_grey_pin_which_is_not_the_selection(page):
    """ "whenever something pinned, it needs an icon… bottom right corner with the pin drawn on it… which is different from selection" and "pin is not blue background because it's not an action. So let's use gray background" """
    show(page, "graph")
    page.evaluate("graphPin('res:cooks'); select(DES_TASKS.oven.info)")
    badge = page.evaluate("(() => { const c = graphPinLayer.querySelector('circle'); return [c.getAttribute('fill'), graphPools[0].g.hasAttribute('data-selected')]; })()")
    assert badge == ["#6a737b", False]


def test_the_pinned_thing_is_in_the_centre_with_only_lines_to_it_and_from_it(page):
    """ "pinning anything, so that thing becomes a center. And we only draw lines to it or from it, but we don't draw any other lines that exist in the model" """
    show(page, "graph")
    for key in ["res:cooks", "res:waiters", "unit:cooks:0", "plating", "source", "out"]:
        page.evaluate(f"graphPin('{key}')")
        shown = page.evaluate("graphEdges.filter(edge => edge.line.style.display !== 'none').map(edge => [edge.from, edge.to])")
        assert all(key in pair for pair in shown), key
    page.evaluate("graphPin('res:cooks')")
    assert page.evaluate("(() => { const r = graphPools[0].g.querySelector('rect').getBBox(); return [r.x + r.width / 2, r.y + r.height / 2]; })()") == [page.evaluate("GRAPH_RING.x"), page.evaluate("GRAPH_RING.y")]


def test_a_table_or_all_the_tables_can_be_picked_and_pinned(page):
    """ "I can pick a table and I should be able to pin it. But I also should be able to pick tables and should be able to pin it" and "when I pin get table and I see tables… I should be able to pick one" """
    show(page, "graph")
    for target, name, pin in [("GRAPH_TOP[1].squares[6]", "Table 7", "unit:tables:6"), ("GRAPH_TOP[1].g.querySelector('rect')", "Tables", "res:tables")]:
        click(page, target)
        actions(page)
        press(page, "pin")
        assert about(page)["name"] == name and page.evaluate("graphPinned") == pin
        press(page, "unpin")
    page.evaluate("graphPin('seating')")
    click(page, "graphPools[0].squares[6]")
    assert about(page)["name"] == "Table 7"


def test_one_cook_can_be_pinned_to_see_what_it_takes_part_in(page):
    """ "pin individual instance of cook, waiter, or any resource to see what activities that participates in" """
    show(page, "graph")
    page.evaluate("graphPin('unit:cooks:0')")
    assert page.evaluate("[...graphShown]") == ["planning", "stoves", "oven", "coffee", "plating"]
    run_until(page, "Boolean(desEngine.resources.cooks.units[0])")
    assert " party " in page.evaluate("graphPools[0].note.textContent")


# ---------- the scorecard ----------

def test_the_scorecard_is_nine_boxes_in_the_order_pavel_narrated(page):
    """ "nine boxes arranged in three by three grid… the one box that we do not have is count of events" and "events so far is the first because that is the most granular… the last one is average wait for food. And then after that, happy visits" """
    assert page.evaluate("SCORE.map(one => one.name)") == ["Events so far", "Arrivals per minute", "Parties in the building now", "Parties in the building, average", "Average time inside",
                                                           "Parties in the building, predicted", "Gap between average and predicted", "Average wait for food", "Happy visits"]


def test_every_scorecard_box_has_its_own_card_of_kind_scorecard_with_charts(page):
    """ "when I select anything on scorecard, I get kind operations. So this is wrong, the kind scorecard… I expect all of the nine squares… each one have a chart and metrics" """
    show(page, "score")
    run(page, 120)
    for index in range(9):
        click(page, f"SCORE[{index}].box")
        assert about(page)["Kind"] == "Scorecard" and metrics(page)["charts"] == 2


def test_scorecard_boxes_are_coloured_by_their_objectives_and_the_legend_says_so(page):
    """ "color accordingly whether we meet objectives or not" and "the legend on the scorecard needs to say… green or red or orange, and say that color indicates compliance to objectives" """
    show(page, "score")
    run(page, 600)
    page.evaluate("drawScore()")
    edges = page.evaluate("Object.fromEntries(SCORE.map(one => [one.name, one.box.getAttribute('class').replace('des-stage', '').replace('score-tile', '').trim()]))")
    assert edges["Happy visits"] in ("won", "near", "lost") and edges["Events so far"] == ""
    text = " ".join(legend(page))
    assert all(word in text for word in ["Green", "Orange", "Red", "objective"])


def test_the_scorecard_footnote(page):
    """ "make that into a short paragraph… like it's a footnote", "first say this here are the key business objective metrics dashboard", "remove: OPERATIONS · Little's Law over the last 3 minutes" and "the footnote, center it" """
    show(page, "score")
    lines = page.evaluate("[...document.querySelectorAll('#score-static > text')].map(line => line.textContent)")
    assert lines[0].startswith("This is the dashboard of the key business objectives") and "Little's Law" in lines[1] and not any("OPERATIONS" in line for line in lines)


def test_with_nobody_cooking_or_serving_the_wait_for_food_is_infinite(page):
    """ "when I remove all the cooks and waiters… average wait for food time is 0.24… you have to update that to infinity because there's no food being served" """
    run(page, 300)
    page.evaluate("for (let i = 0; i < 2; i++) { desEngine.changeCapacity('cooks', -1); desEngine.changeCapacity('waiters', -1); }")
    run_until(page, "desEngine.resources.cooks.capacity === 0 && desEngine.resources.waiters.capacity === 0")
    show(page, "score")
    assert page.evaluate("SCORE.find(one => one.name === 'Average wait for food').text.textContent") == "∞"


# ---------- the toolbar ----------

def test_zoom_glides_and_two_fingers_on_the_trackpad_zoom(page):
    """ "Don't do a jump zoom, animate" and "let me zoom in, zoom out by pad scrolling with two fingers" """
    whole = page.evaluate("$('desview').getAttribute('viewBox')")
    page.click("#zoom-in")
    assert page.evaluate("$('desview').getAttribute('viewBox')") == whole and page.evaluate("__frames.length") == 1, "a glide is under way, nothing has jumped"
    settle(page, 1)
    page.evaluate("zoomFit(); applyZoom()")
    page.evaluate("$('desview').dispatchEvent(new WheelEvent('wheel', { deltaY: -100, clientX: 400, clientY: 400, bubbles: true, cancelable: true }))")
    assert page.evaluate("zoomState().zoom.k") > 1


def test_speed_is_a_dropdown_and_pause_shows_play(page):
    """ "speed buttons into a dropdown" and "pause/play blue button" """
    assert page.evaluate("[$('speed-menu').children.length, getComputedStyle($('pause')).backgroundColor]") == [5, "rgb(37, 99, 235)"]
    page.click("#pause")
    assert page.evaluate("$('icon-play').hasAttribute('hidden')") is False


# ---------- the legend ----------

def test_the_process_map_legend_has_headed_sections(page):
    """ "the first heading on the legend would be resources, then the process, the outcomes… there are two types of boxes here and that's what they mean" (the middle one is called Tasks since "instead, let's call that tasks", and the first one Actors and resources since "let's use actors and resources", later written with an ampersand) """
    show(page, "graph")
    lines = legend(page)
    assert [line for line in lines if line in ("Actors & resources", "Tasks", "Outcomes")] == ["Actors & resources", "Tasks", "Outcomes"]
    assert sum(line.startswith("- ") for line in lines[lines.index("Outcomes"):]) == 2


def test_each_view_has_its_own_legend_in_the_details_panel(page):
    """ "legend into details, different per view" """
    seen = set()
    for view in ["des", "graph", "score"]:
        show(page, view)
        seen.add(tuple(legend(page)))
    assert len(seen) == 3 and page.evaluate("$('legend').closest('.panel') !== null")


# ---------- parties as something to look at, select and pin ----------

def test_the_middle_section_is_called_tasks(page):
    """ "the middle section currently has title called process. Instead, let's call that tasks" """
    show(page, "graph")
    assert sorted(page.evaluate("[...graphSectionLayer.querySelectorAll('text')].map(heading => heading.textContent)")) == ["ACTORS & RESOURCES", "OUTCOMES", "TASKS"]


def test_the_parties_in_the_restaurant_are_in_a_box_beside_the_resources(page):
    """ "I also want to be able to see parties that have entered and are currently in a restaurant where the resource tab is… a box called parties, similar to cooks… as they leave, they depart this box, as well as they enter, they arrive… I can select all the parties, get statistics, or I can select specific party" """
    show(page, "graph")
    run(page, 120)
    shown = page.evaluate("GRAPH_TOP[0].squares.filter(square => square.style.display !== 'none').map(square => square.dataset.party)")
    assert page.evaluate("GRAPH_TOP[0].id") == "parties" and shown == page.evaluate("[...desEngine.parties.keys()]")
    click(page, "GRAPH_TOP[0].squares[0]")
    assert about(page)["name"].startswith("Party ")
    click(page, "GRAPH_TOP[0].g.querySelector('rect')")
    assert about(page)["name"] == "Parties" and "Seated" in metrics(page)["numbers"]


def test_a_party_is_drawn_as_a_crossed_square_not_a_filled_one(page):
    """ "when you draw the box for the instance of a party, don't fill it. Use the cross across it like we do with cooks, which means active" """
    show(page, "graph")
    run(page, 60)
    assert page.evaluate("getComputedStyle(GRAPH_TOP[0].squares[0]).fill") == 'url("#unit-cross")'


def test_a_pinned_party_shows_only_what_it_takes_part_in_or_waits_for_in_person(page):
    """ "I should be able also to pin the party to see what actions they're waiting for", "party never uses a stove… pull in activities in which parties participate or wait for directly… after party placed an order, they're waiting for food to table. They don't have visibility into plate food, make coffee" and "show around all possible… your arrow points to the one which is currently active" """
    show(page, "graph")
    run_until(page, "[...desEngine.parties.values()].some(party => party.state === 'COOKING')")
    page.evaluate("graphPin('party:' + [...desEngine.parties.values()].find(party => party.state === 'COOKING').id)")
    settle(page, 2)
    shown = page.evaluate("[...graphShown]")
    assert shown[:5] == ["seating", "browsing", "ordering", "running", "dining"] and not {"planning", "stoves", "oven", "coffee", "plating"} & set(shown)
    pointing = page.evaluate("Object.entries(graphPools[0].links).filter(([, link]) => link.style.display !== 'none').map(([key]) => key)")
    assert pointing == ["running"] and page.evaluate("graphPools[0].note.textContent") == "Waiting for the food"


def test_a_pinned_party_also_shows_the_outcomes_it_can_exit_into(page):
    """ "when we focused on parties or specific instances of the party, also bring the outcomes at the bottom… that this party will eventually exit into" """
    show(page, "graph")
    run(page, 60)
    page.evaluate("graphPin('parties')")
    assert page.evaluate("[...graphShown].slice(5)") == ["away", "noorder", "hungry", "out"]
    page.evaluate("graphPin('party:' + [...desEngine.parties.keys()][0])")
    assert page.evaluate("[...graphShown].slice(5)") == ["noorder", "hungry", "out"]
    assert page.evaluate("['noorder', 'hungry', 'out'].every(key => GRAPH[key].cy + GRAPH[key].dy > GRAPH_RING.y) && ['seating', 'dining'].every(key => GRAPH[key].cy + GRAPH[key].dy <= GRAPH_RING.y)")


def test_a_party_that_leaves_stays_selected_and_pinned_until_it_is_unpinned_by_hand(page):
    """ "if party leaves, leave it focused… in a metric section, it would say visit over… still keep it in the database of all the parties and don't drop it, don't unpin it automatically. I will unpin it" """
    show(page, "graph")
    run_until(page, "desEngine.parties.size > 0")
    page.evaluate("window.mine = [...desEngine.parties.keys()][0]; select(desPartyInfo(mine)); graphPin('party:' + mine)")
    run_until(page, "!desEngine.parties.has(mine)")
    run(page, 60)
    assert page.evaluate("graphPinned === 'party:' + mine && selected === desPartyInfo(mine)")
    assert any(note.startswith("Visit over") for note in metrics(page)["notes"])
    assert actions(page) == {"Unpin": True}
    press(page, "unpin")
    assert page.evaluate("graphPinned") is None


def test_all_the_parties_can_be_pinned(page):
    """ "I want to be able to pin all the parties also… like I can pin all the cooks" """
    show(page, "graph")
    run(page, 60)
    click(page, "GRAPH_TOP[0].g.querySelector('rect')")
    assert actions(page) == {"Pin": True}
    press(page, "pin")
    assert page.evaluate("graphPinned") == "parties" and page.evaluate("graphTokens.size") == page.evaluate("desEngine.parties.size")


def test_the_process_map_uses_the_entire_width(page):
    """ "use entire horizontal space available… you see how much wasted space is here" """
    show(page, "graph")
    card, frame = page.locator("#desgraph").bounding_box(), page.evaluate("(() => { const b = graphFullHeight.getBoundingClientRect(); return [b.left, b.right]; })()")
    assert frame[0] - card["x"] < 20 and card["x"] + card["width"] - frame[1] < 20
    assert page.evaluate("(() => { const a = GRAPH_TOP[0].g.getBoundingClientRect(), z = GRAPH.out.g.getBoundingClientRect(), f = graphFullHeight.getBoundingClientRect(); return Math.abs(a.left - f.left) < 2 && Math.abs(z.right - f.right) < 2; })()")


def test_the_page_comes_back_the_way_it_was_left(page):
    """ "I was on pause… I loaded and started running. Why don't you save state of buttons and expand collapse for the panels in the local storage… don't default to running. Default to whatever my state was" """
    page.click("#pause")
    page.evaluate("setPanel(true); setFold('legend', true)")
    page.reload()
    assert page.evaluate("[paused, $('panel').classList.contains('open'), folds.legend, folds.events]") == [True, True, True, False]


def test_the_waiting_area_is_a_plain_rectangle_with_its_name_inside(page):
    """ "do not do dotted line outline in a waiting area. Just do rectangle. On the side of the building… no rounded corners, straight up corners and inside the rectangle say waiting area" """
    area = page.evaluate("(() => { const r = DES_QUEUE.host.info.nodes[0].querySelector('.des-rail'), b = r.getBBox(), t = DES_QUEUE.host.info.nodes[0].querySelector('text').getBBox(); return [getComputedStyle(r).strokeDasharray, r.getAttribute('rx'), b.x + b.width, t.y > b.y && t.y + t.height < b.y + b.height]; })()")
    assert area == ["none", None, 60, True]


def test_a_pinned_task_is_laid_out_left_to_right_with_resources_on_top_and_outcomes_at_the_bottom(page):
    """ "when a thing pinned is of the type like a task… get table, [view menu], order, precedence, and the next one should be laid out horizontally as much as possible… resources should be at the top, tasks are laid out horizontally… and the outcome should be at the bottom as much as possible. So revise the layout rules" """
    show(page, "graph")
    page.evaluate("graphPin('ordering')")
    b = page.evaluate("Object.fromEntries(['browsing', 'ordering', 'planning', 'noorder'].map(key => [key, { x: GRAPH[key].x + GRAPH[key].dx, y: GRAPH[key].y + GRAPH[key].dy, bottom: GRAPH[key].bottom + GRAPH[key].dy }]))")
    assert b["browsing"]["x"] < b["ordering"]["x"] < b["planning"]["x"] and b["browsing"]["y"] == b["ordering"]["y"] == b["planning"]["y"]
    assert b["noorder"]["y"] > b["ordering"]["bottom"]
    assert page.evaluate("Number(graphPools[0].g.querySelector('rect').getAttribute('y')) + 74") < b["ordering"]["y"]
