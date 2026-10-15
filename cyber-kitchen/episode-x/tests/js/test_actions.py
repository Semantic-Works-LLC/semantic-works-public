"""js/actions.js: the Actions tab and the right-click menu, which offer the same actions."""
from tests.support import about, actions, menu_pick, press, resources, right_click, run, run_until, show


# ---------- the Actions tab ----------

def test_only_the_actions_that_apply_are_listed_each_on_its_own_line_with_what_it_does(page):
    page.evaluate("select(DES_RES.cooks.units[0].info)")
    assert actions(page) == {"Pin": True, "Call in sick": True}
    rows = page.evaluate("[...document.querySelectorAll('#actions .action')].map(row => [row.children.length, row.children[1].textContent.length > 20])")
    assert rows == [[2, True]] * 2
    assert page.evaluate("ACTIONS.map(action => action.key)") == ["pin", "unpin", "out", "back"]


def test_action_buttons_are_blue(page):
    page.evaluate("select(DES_RES.cooks.units[0].info)")
    actions(page)
    assert page.evaluate("getComputedStyle(document.querySelector('#actions [data-action=pin]')).backgroundColor") == "rgb(37, 99, 235)"


def test_the_list_follows_what_can_be_done_now(page):
    page.evaluate("select(DES_TASKS.oven.info)")
    assert actions(page) == {"Pin": True}
    press(page, "pin")
    assert actions(page) == {"Unpin": True}
    press(page, "unpin")
    assert actions(page) == {"Pin": True}


def test_the_list_is_not_rebuilt_while_nothing_changes(page):
    page.evaluate("select(DES_TASKS.oven.info)")
    actions(page)
    assert page.evaluate("(() => { const button = document.querySelector('#actions button'); renderActions(); renderActions(); return document.querySelector('#actions button') === button; })()")


def test_the_words_for_out_of_service_follow_what_is_selected(page):
    labels = {}
    for name, info in [("waiter", "DES_RES.waiters.units[0].info"), ("oven", "DES_RES.oven.units[0].info"), ("table", "DES_RES.tables.units[0].info"), ("step", "DES_TASKS.oven.info"), ("pool", "DES_RES.cooks.info")]:
        page.evaluate(f"select({info})")
        labels[name] = list(actions(page))
    assert labels == {"waiter": ["Pin", "Call in sick"], "oven": ["Pin", "Break down"], "table": ["Pin", "Close table"], "step": ["Pin"], "pool": ["Pin"]}


def test_something_with_no_actions_says_so(page):
    page.evaluate("select(desPartsInfo)")
    assert actions(page) == {} and page.locator("#actions .empty").inner_text() == "No actions apply to this right now."
    page.evaluate("select(DES_TASKS.oven.info)")
    assert actions(page) == {"Pin": True} and page.evaluate("document.querySelector('#actions .empty')") is None


def test_with_nothing_selected_or_the_tab_hidden_there_are_no_buttons(page):
    page.evaluate("select(DES_TASKS.oven.info)")
    actions(page)
    page.evaluate("setTab('about'); renderActions()")
    assert page.evaluate("$('actions').children.length") == 0
    page.evaluate("select(null); renderActions()")
    assert page.evaluate("$('actions').children.length") == 0
    page.evaluate("select(DES_TASKS.oven.info)")
    assert actions(page) == {"Pin": True}, "and they come back"


def test_pin_from_another_view_goes_to_the_process_map(page):
    page.evaluate("select(DES_RES.tables.units[6].info)")
    actions(page)
    press(page, "pin")
    assert page.evaluate("[view, graphPinned]") == ["graph", "unit:tables:6"]
    press(page, "unpin")
    assert page.evaluate("[view, graphPinned]") == ["graph", None]


def test_a_button_whose_action_stopped_applying_does_nothing(page):
    page.evaluate("select(DES_RES.oven.units[0].info)")
    actions(page)
    page.evaluate("desEngine.setOut('oven', 0, true); document.querySelector('#actions [data-action=out]').click()")
    assert page.evaluate("desEngine.resources.oven.units[0]") == 0 and actions(page) == {"Pin": True, "Fix": True}


def test_sick_and_back_to_work(page):
    page.evaluate("select(DES_RES.cooks.units[1].info)")
    actions(page)
    press(page, "out")
    assert resources(page)["cooks"]["units"][1] == "out" and actions(page) == {"Pin": True, "Back to work": True}
    press(page, "back")
    assert resources(page)["cooks"]["units"][1] == "free" and actions(page) == {"Pin": True, "Call in sick": True}


def test_a_busy_unit_asked_to_go_can_be_kept_from_the_tab(page):
    run_until(page, "Boolean(desEngine.resources.cooks.units[0])")
    page.evaluate("select(DES_RES.cooks.units[0].info)")
    actions(page)
    press(page, "out")
    assert actions(page) == {"Pin": True, "Back to work": True}
    press(page, "back")
    assert page.evaluate("desEngine.resources.cooks.goingOut.size") == 0


def test_a_party_can_be_pinned_but_not_taken_out_of_service(page):
    run_until(page, "desEngine.parties.size > 0")
    page.evaluate("select(desPartyInfo([...desEngine.parties.keys()][0]))")
    assert actions(page) == {"Pin": True}


# ---------- the right-click menu ----------

def test_right_click_selects_and_offers_that_objects_own_actions(page):
    show(page, "graph")
    assert right_click(page, "GRAPH.plating.g.querySelector('rect')") == ["Pin"] and about(page)["name"] == "Plating"
    assert right_click(page, "GRAPH_TOP[3].squares[0]") == ["Pin", "Call in sick"] and about(page)["name"] == "Cook 1"
    assert right_click(page, "GRAPH_TOP[5].g.querySelector('rect')") == ["Pin"] and about(page)["name"] == "Pizza oven"
    assert right_click(page, "GRAPH.out.g.querySelector('rect')") == ["Pin"] and about(page)["name"] == "Dined"


def test_the_menu_never_names_the_object_and_never_offers_to_unpin_another(page):
    show(page, "graph")
    page.evaluate("graphPin('ordering')")
    assert right_click(page, "GRAPH.planning.g.querySelector('rect')") == ["Pin"]
    assert right_click(page, "$('desgraph')") == [], "empty space has no actions, even while something is pinned"
    assert right_click(page, "GRAPH.ordering.g.querySelector('rect')") == ["Unpin"], "the pinned thing itself offers Unpin"


def test_pinning_from_the_menu_unpins_whatever_was_pinned(page):
    show(page, "graph")
    page.evaluate("graphPin('ordering')")
    right_click(page, "GRAPH.planning.g.querySelector('rect')")
    menu_pick(page, "Pin")
    assert page.evaluate("graphPinned") == "planning" and page.evaluate("$('graph-menu').hidden")
    right_click(page, "GRAPH.planning.g.querySelector('rect')")
    menu_pick(page, "Unpin")
    assert page.evaluate("graphPinned") is None


def test_the_menu_works_on_the_floor_plan_too(page):
    run(page, 60)
    assert right_click(page, "desFloorTables[3].g.querySelector('.table-top')") == ["Pin", "Close table"]
    menu_pick(page, "Close")
    run_until(page, "desEngine.resources.tables.units[3] === DES_OUT")
    assert right_click(page, "desFloorTables[3].g.querySelector('.table-top')") == ["Pin", "Open table"]
    assert right_click(page, "DES_EQUIPMENT.oven[0].flame") == ["Pin", "Break down"]
    assert right_click(page, "desTokens.get('cook0').g") == ["Pin", "Call in sick"]


def test_something_with_no_actions_gets_no_menu(page):
    run(page, 60)
    assert right_click(page, "[...desTokens.values()].find(token => token.key.includes(':')).g") == ["Pin"]
    assert about(page)["name"].startswith("Party ")
    assert right_click(page, "DES_QUEUE.run.info.nodes[0]") == [] and about(page)["name"] == "Pass", "it is still selected"
    show(page, "score")
    assert right_click(page, "SCORE[0].box") == [] and right_click(page, "$('scoreview')") == []


def test_an_earlier_menu_does_not_stay_up(page):
    show(page, "graph")
    assert right_click(page, "GRAPH.plating.g.querySelector('rect')") == ["Pin"]
    assert right_click(page, "$('desgraph')") == [] and page.evaluate("$('graph-menu').hidden")


def test_the_menu_closes_on_a_click_elsewhere_and_on_escape(page):
    show(page, "graph")
    for close in ["document.body.click()", "document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))"]:
        right_click(page, "GRAPH.plating.g.querySelector('rect')")
        page.evaluate(close)
        assert page.evaluate("$('graph-menu').hidden")
    right_click(page, "GRAPH.plating.g.querySelector('rect')")
    page.evaluate("document.dispatchEvent(new KeyboardEvent('keydown', { key: 'x' }))")
    assert page.evaluate("$('graph-menu').hidden") is False


def test_the_menu_opens_at_the_pointer_but_stays_on_screen(page):
    show(page, "graph")
    place = page.evaluate("""() => { GRAPH.plating.g.querySelector('rect').dispatchEvent(new MouseEvent('contextmenu', { bubbles: true, cancelable: true, clientX: 5000, clientY: 5000 }));
        const box = $('graph-menu').getBoundingClientRect(); return [box.right <= innerWidth, box.bottom <= innerHeight]; }""")
    assert place == [True, True]
