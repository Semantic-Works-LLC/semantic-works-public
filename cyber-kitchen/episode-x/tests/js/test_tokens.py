"""js/tokens.js: tokens glide to their place, and leave when their thing has left the simulation."""
import pytest


SETUP = """() => {
    window.bag = new Map(); window.info = { nodes: [], name: 'Probe', kind: 'Test', metrics: () => metricsFor(DES_RES.cooks.info) };
    const token = viewToken(bag, 'des-floor-tokens', 'one', info, g => el('circle', { r: 5 }, g));
    token.x = 0; token.y = 0; token.tx = 100; token.ty = 50;
    return token.g.parentNode.id;
}"""


def test_set_text_writes_only_when_the_text_differs(page):
    assert page.evaluate("""() => { const node = document.createElement('p'); let writes = 0;
        new MutationObserver(() => 0); setText(node, 5); const first = node.firstChild; setText(node, '5'); return [node.textContent, node.firstChild === first]; }""") == ["5", True]


def test_a_token_is_made_once_and_drawn_into_its_layer(page):
    assert page.evaluate(SETUP) == "des-floor-tokens"
    assert page.evaluate("viewToken(bag, 'des-floor-tokens', 'one', info, () => { throw new Error('built twice'); }) === bag.get('one') && bag.size === 1")


def test_clicking_a_token_selects_what_it_stands_for(page):
    page.evaluate(SETUP)
    page.evaluate("bag.get('one').g.dispatchEvent(new MouseEvent('click', { bubbles: true }))")
    assert page.evaluate("selected === info")


def test_a_token_glides_part_of_the_way_each_frame(page):
    page.evaluate(SETUP)
    page.evaluate("glideTokens(bag, 0.5)")
    assert page.evaluate("[bag.get('one').x, bag.get('one').y, bag.get('one').g.getAttribute('transform')]") == [50, 25, "translate(50.0 25.0)"]


def test_a_token_shows_as_selected_for_its_own_card_or_one_it_also_stands_for(page):
    page.evaluate(SETUP)
    marked = page.evaluate("""() => { const t = bag.get('one'), out = [];
        selected = info; glideTokens(bag, 0.1); out.push(t.g.hasAttribute('data-selected'));
        selected = DES_RES.cooks.info; glideTokens(bag, 0.1); out.push(t.g.hasAttribute('data-selected'));
        t.also.push(DES_RES.cooks.info); glideTokens(bag, 0.1); out.push(t.g.hasAttribute('data-selected'));
        selected = null; glideTokens(bag, 0.1); out.push(t.g.hasAttribute('data-selected')); return out; }""")
    assert marked == [True, False, True, False]


def test_a_token_that_is_no_longer_live_goes_home_and_is_removed(page):
    page.evaluate(SETUP)
    gone = page.evaluate("""() => { const t = bag.get('one'); t.live = false; t.home = { x: -20, y: 270 };
        let frames = 0; while (bag.size && frames++ < 200) glideTokens(bag, 0.3);
        return [bag.size, t.g.isConnected, frames < 200, t.tx, t.ty]; }""")
    assert gone == [0, False, True, -20, 270]


def test_a_token_with_no_home_leaves_by_the_right_edge(page):
    page.evaluate(SETUP)
    assert page.evaluate("(() => { const t = bag.get('one'); t.live = false; t.y = 40; glideTokens(bag, 0.5); return [t.tx, t.ty]; })()") == [1240, 40]
