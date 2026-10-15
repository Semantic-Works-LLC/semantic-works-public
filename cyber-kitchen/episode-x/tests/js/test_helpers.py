"""js/helpers.js: making SVG nodes, and writing a time as minutes and seconds."""


def test_el_makes_an_svg_node_with_attributes_and_appends_it(page):
    made = page.evaluate("""() => {
        const parent = el('g', {}), node = el('rect', { x: 3, width: 10, class: 'probe' }, parent);
        return [node.namespaceURI, node.tagName, node.getAttribute('x'), node.getAttribute('class'), node.parentNode === parent, el('circle', { r: 2 }).parentNode];
    }""")
    assert made == ["http://www.w3.org/2000/svg", "rect", "3", "probe", True, None]


def test_text_makes_a_text_node_with_content(page):
    assert page.evaluate("(() => { const t = text('hello', { x: 1 }, el('g', {})); return [t.tagName, t.textContent, t.getAttribute('x')]; })()") == ["text", "hello", "1"]


def test_dollar_finds_an_element_by_id(page):
    assert page.evaluate("$('pause') === document.getElementById('pause') && $('nothing-here') === null")


def test_clock_text_is_minutes_and_two_digit_seconds(page):
    assert page.evaluate("[0, 9.9, 60, 75, 600, 3599.5].map(clockText)") == ["0:00", "0:09", "1:00", "1:15", "10:00", "59:59"]
