"""js/legend.js: what the marks on each view mean."""
from tests.support import legend, show


def test_the_floor_plan_legend(page):
    lines = legend(page)
    assert lines[:5] == ["- Free table", "- Table: reading the menu", "- Table: wants to order, or ordering", "- Table: waiting for the food", "- Table: eating"]
    assert lines[5:8] == ["- Waiter", "- Cook", "- Guest"] and lines[8].startswith("- Red line across a table or a machine: out of service.")
    assert len(lines) == 9 and not any("Meter" in line or "Outcome" in line for line in lines)


def test_the_process_map_legend_has_a_section_for_each_part_of_the_map(page):
    show(page, "graph")
    lines = legend(page)
    headings = [line for line in lines if not line.startswith("- ") and len(line) < 22]
    assert headings == ["Actors & resources", "Tasks", "Outcomes"]
    assert lines[1] == "Who is in the restaurant, and what it has to work with: parties, staff, tables and kitchen equipment."
    assert lines[lines.index("Actors & resources") + 2:lines.index("Tasks")] == [
        "- Grey edge: actors. The people: parties, waiters and cooks",
        "- Violet edge: resources. The things they use: tables, stoves, the pizza oven and the coffee machine",
        "- Crossed square: one that is active. A party in the building, or a waiter, cook, table or machine that is taken right now",
        "- Hollow square: one that is free",
        "- Red line: one that is out of service. A person off sick, a machine broken down, a table closed"]
    assert lines[-2:] == ["- Green edge: the visit ended well. The party dined", "- Red edge: the visit was lost. The party was turned away at the door, or left without eating"]
    assert sum(line.startswith("- ") for line in lines[lines.index("Tasks"):lines.index("Outcomes")]) == 4


def test_the_scorecard_legend_says_what_the_outline_colours_mean(page):
    show(page, "score")
    lines = legend(page)
    assert lines[0] == "Figures" and lines[2] == "Colour" and lines[3] == "The colour of a box's outline says how the figure stands against its objective."
    assert [line.split(":")[0] for line in lines[4:]] == ["- Green", "- Orange", "- Red", "- Grey"]
    strokes = page.evaluate("[...document.querySelectorAll('#legend li svg rect')].map(rect => rect.getAttribute('stroke'))")
    assert strokes == ["var(--eating)", "var(--ready)", "var(--waiting)", "#2c2c2a"]


def test_every_entry_has_a_drawn_sample(page):
    for view in ["des", "graph", "score"]:
        show(page, view)
        assert page.evaluate("[...document.querySelectorAll('#legend li')].every(item => item.children.length === 2 && item.firstChild.firstElementChild)"), view


def test_the_legend_uses_no_blue_for_resources(page):
    show(page, "graph")
    marks = page.evaluate("$('legend').innerHTML")
    assert "#a78bfa" in marks and "#3b82f6" not in marks and "#4f9cf0" not in marks
