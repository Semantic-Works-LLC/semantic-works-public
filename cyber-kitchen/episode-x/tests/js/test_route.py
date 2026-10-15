"""js/route.js: tokens follow the arrows from box to box, corner by corner."""
import pytest

GRAPH = """
    const centres = { a: { x: 0, y: 0 }, b: { x: 100, y: 0 }, c: { x: 200, y: 0 }, d: { x: 100, y: 100 }, lone: { x: 500, y: 500 } };
    const edges = [
        { from: 'a', to: 'b', points: [{ x: 10, y: 0 }, { x: 90, y: 0 }] },
        { from: 'b', to: 'c', points: [{ x: 110, y: 0 }, { x: 190, y: 0 }] },
        { from: 'b', to: 'd', points: [{ x: 100, y: 10 }, { x: 100, y: 90 }] },
        { from: 'a', to: 'c', points: [{ x: 0, y: -10 }, { x: 0, y: -50 }, { x: 200, y: -50 }, { x: 200, y: -10 }] },
    ];
    const route = makeRouter(edges, key => centres[key]);
"""


def test_a_route_is_the_points_of_the_arrow(page):
    assert page.evaluate(f"(() => {{ {GRAPH} return route('a', 'b'); }})()") == [{"x": 10, "y": 0}, {"x": 90, "y": 0}]


def test_the_fewest_arrows_are_taken(page):
    assert len(page.evaluate(f"(() => {{ {GRAPH} return route('a', 'c'); }})()")) == 4, "the direct arrow, not the two through b"


def test_a_box_that_is_only_passed_through_is_crossed_at_its_centre(page):
    points = page.evaluate(f"(() => {{ {GRAPH} return route('a', 'd'); }})()")
    assert points == [{"x": 10, "y": 0}, {"x": 90, "y": 0}, {"x": 100, "y": 0}, {"x": 100, "y": 10}, {"x": 100, "y": 90}]


def test_there_is_no_route_to_itself_backwards_or_to_an_unconnected_box(page):
    assert page.evaluate(f"(() => {{ {GRAPH} return [route('a', 'a'), route('c', 'a'), route('a', 'lone'), route('lone', 'a')]; }})()") == [None] * 4


def test_head_for_gives_a_token_its_route_and_its_new_box(page):
    token = page.evaluate(f"(() => {{ {GRAPH} const t = {{ at: 'a', x: 0, y: 0 }}; headFor(t, 'b', route); headFor(t, 'b', route); return t; }})()")
    assert token["at"] == "b" and len(token["route"]) == 2


def test_a_token_still_on_its_way_finishes_that_way_first(page):
    token = page.evaluate(f"(() => {{ {GRAPH} const t = {{ at: 'a', x: 0, y: 0 }}; headFor(t, 'b', route); headFor(t, 'd', route); return t; }})()")
    assert token["at"] == "d"
    assert token["route"] == [{"x": 10, "y": 0}, {"x": 90, "y": 0}, {"x": 100, "y": 0}, {"x": 100, "y": 10}, {"x": 100, "y": 90}]


def test_with_no_arrow_to_follow_a_token_appears_in_place(page):
    token = page.evaluate(f"(() => {{ {GRAPH} const t = {{ at: 'c', x: 200, y: 0, tx: 7, ty: 9 }}; headFor(t, 'a', route); return t; }})()")
    assert (token["x"], token["y"], token["route"]) == (7, 9, [])
    fresh = page.evaluate(f"(() => {{ {GRAPH} const t = {{ x: 1, y: 2, tx: 7, ty: 9 }}; headFor(t, 'a', route); return t; }})()")
    assert (fresh["x"], fresh["y"], fresh["at"]) == (7, 9, "a")
    unplaced = page.evaluate(f"(() => {{ {GRAPH} const t = {{ at: 'c', x: 1, y: 2 }}; headFor(t, 'a', route); return t; }})()")
    assert (unplaced["x"], unplaced["y"]) == (1, 2)


def test_move_token_follows_the_corners_and_never_cuts_them(page):
    path = page.evaluate(f"""(() => {{ {GRAPH} const t = {{ at: 'a', x: 0, y: -10, tx: 200, ty: -10 }}; headFor(t, 'c', route);
        const seen = []; let n = 0; while (t.route.length && n++ < 500) {{ moveToken(t, 1 / 60, 0.1); seen.push([Math.round(t.x), Math.round(t.y)]); }}
        return seen; }})()""")
    assert path[-1] == [200, -10]
    assert all(x == 0 or x == 200 or y == -50 for x, y in path), "always on one of the three straight pieces of the arrow"


def test_move_token_without_a_route_glides_to_its_place(page):
    assert page.evaluate("(() => { const t = { x: 0, y: 0, tx: 10, ty: 20 }; moveToken(t, 1 / 60, 0.5); return [t.x, t.y]; })()") == [5, 10]
    assert page.evaluate("(() => { const t = { x: 0, y: 0, tx: 10, ty: 20, route: [] }; moveToken(t, 1 / 60, 0.5); return [t.x, t.y]; })()") == [5, 10]


def test_a_token_with_far_to_go_moves_faster(page):
    near, far = page.evaluate("""[100, 2000].map(length => { const t = { x: 0, y: 0, route: [{ x: length, y: 0 }] }; moveToken(t, 0.1, 0.1); return t.x; })""")
    assert near == pytest.approx(15) and far == pytest.approx(2000 / 0.7 * 0.1)
