"""js/helpers.js: small functions the rest of the page is built from."""


def test_dollar_finds_an_element_by_its_id(page):
    assert page.evaluate("$('pause').textContent") == "Pause"
    assert page.evaluate("$('no-such-thing')") is None


def test_rand_stays_inside_its_range(page):
    values = page.evaluate("Array.from({ length: 200 }, () => rand(5, 10))")
    assert all(5 <= value < 10 for value in values) and len(set(values)) > 100


def test_el_makes_an_svg_element_with_attributes_and_can_attach_it(page):
    made = page.evaluate("""() => {
        const parent = el("g", {}), child = el("rect", { x: 3, width: 20, class: "steel" }, parent), loose = el("circle", { r: 2 });
        return [child.namespaceURI, child.tagName, child.getAttribute("x"), child.getAttribute("class"),
                child.parentNode === parent, loose.parentNode];
    }""")
    assert made == ["http://www.w3.org/2000/svg", "rect", "3", "steel", True, None]


def test_text_makes_an_svg_text_element_with_content(page):
    made = page.evaluate("""() => { const node = text("Table 7", { x: 10 }, el("g", {})); return [node.tagName, node.textContent, node.getAttribute("x")]; }""")
    assert made == ["text", "Table 7", "10"]


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
