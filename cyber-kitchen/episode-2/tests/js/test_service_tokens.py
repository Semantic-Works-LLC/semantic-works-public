"""js/service-tokens.js: floor objects shared with the service view, and the tokens that glide in it."""
from tests.support import card, click


def test_floor_objects_are_found_by_name_and_know_their_queue(page):
    assert page.evaluate("floorObject('Order rail') === fixedObjects[1]")
    assert page.evaluate("['Front door', 'Order rail', 'Pass table'].map(name => floorObject(name).subject)") == ["door", "rail", "pass"]
    assert page.evaluate("floorObject('Sink')") is None


def test_also_selectable_adds_a_second_drawing_of_the_same_object(page):
    page.evaluate("window.extra = el('g', {}, $('loop-static')); alsoSelectable(extra, tables[0].info)")
    assert page.evaluate("[tables[0].info.nodes.length, extra.hasAttribute('data-selectable')]") == [3, True]
    click(page, "extra")
    assert card(page)["name"] == "Table 1"
    assert page.evaluate("tables[0].info.nodes.every(node => node.hasAttribute('data-selected'))")


def test_set_text_only_writes_when_the_text_changes(page):
    result = page.evaluate("""() => {
        const node = document.createElement('p');
        setText(node, 5); const first = node.firstChild;
        setText(node, '5'); const untouched = node.firstChild === first;
        setText(node, 6);
        return [untouched, node.textContent];
    }""")
    assert result == [True, "6"]


def test_a_token_is_made_once_and_reused(page):
    result = page.evaluate("""() => {
        const tokens = new Map(); let built = 0;
        const info = tables[0].info;
        const a = viewToken(tokens, 'loop-tokens', 'x', info, g => { built++; el('circle', { r: 3 }, g); });
        a.live = false;
        const b = viewToken(tokens, 'loop-tokens', 'x', info, () => built++);
        return [a === b, built, b.live, tokens.size, a.x, a.g.parentNode.id, a.g.hasAttribute('data-selectable')];
    }""")
    assert result == [True, 1, True, 1, None, "loop-tokens", True]


def test_clicking_a_token_selects_what_it_stands_for(page):
    page.evaluate("window.token = viewToken(new Map(), 'loop-tokens', 'x', tables[4].info, () => {})")
    click(page, "token.g")
    assert card(page)["name"] == "Table 5"


def test_party_order_and_staff_tokens_are_drawn_like_on_the_floor(page):
    drawn = page.evaluate("""() => {
        const party = el('g', {}), order = el('g', {}), token = {}, waiter = el('g', {}), cook = el('g', {});
        partyToken(party, { color: '#199e70', size: 4 });
        orderToken(order, token, { table: { id: 9 } });
        staffToken('W3', true)(waiter); staffToken('C1', false)(cook);
        showAsFood(token, false); const paper = [token.paper.getAttribute('visibility'), token.dish.getAttribute('visibility')];
        showAsFood(token, true); const food = [token.paper.getAttribute('visibility'), token.dish.getAttribute('visibility')];
        return [party.firstChild.getAttribute('fill'), party.textContent, order.textContent, paper, food,
                waiter.textContent, waiter.firstChild.getAttribute('fill'), cook.textContent, cook.firstChild.getAttribute('fill')];
    }""")
    assert drawn == ["#199e70", "4", "9", ["visible", "hidden"], ["hidden", "visible"], "W3", "#0d0d0d", "C1", "#fff"]


def test_tokens_glide_part_of_the_way_each_frame(page):
    moved = page.evaluate("""() => {
        const tokens = new Map(), token = viewToken(tokens, 'loop-tokens', 'x', tables[0].info, () => {});
        Object.assign(token, { x: 0, y: 0, tx: 100, ty: 50 });
        glideTokens(tokens, 0.5);
        return [token.x, token.y, token.g.getAttribute('transform')];
    }""")
    assert moved == [50, 25, "translate(50.0 25.0)"]


def test_a_token_is_marked_when_its_object_or_a_related_one_is_selected(page):
    marks = page.evaluate("""() => {
        const tokens = new Map(), token = viewToken(tokens, 'loop-tokens', 'x', tables[0].info, () => {});
        Object.assign(token, { x: 0, y: 0, tx: 0, ty: 0, also: [tables[1].info] });
        const marked = info => { select(info); glideTokens(tokens, 1); return token.g.hasAttribute('data-selected'); };
        return [marked(null), marked(tables[0].info), marked(tables[1].info), marked(tables[2].info)];
    }""")
    assert marks == [False, True, True, False]


def test_a_token_whose_thing_is_gone_leaves_and_is_then_removed(page):
    result = page.evaluate("""() => {
        const tokens = new Map(), make = key => Object.assign(viewToken(tokens, 'loop-tokens', key, tables[0].info, () => {}), { x: 100, y: 40, tx: 100, ty: 40, live: false });
        const party = make('party'), order = make('order');
        order.home = { x: 300, y: 90 };
        glideTokens(tokens, 0.5);
        const heading = [[party.tx, party.ty], [order.tx, order.ty]];
        for (let i = 0; i < 30; i++) glideTokens(tokens, 0.5);
        return [heading, tokens.size, party.g.parentNode, order.g.parentNode];
    }""")
    assert result == [[[1240, 40], [300, 90]], 0, None, None]   # a party leaves at the right edge, an order goes to its party
