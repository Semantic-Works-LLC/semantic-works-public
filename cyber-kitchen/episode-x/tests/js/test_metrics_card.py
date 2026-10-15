"""js/metrics-card.js: the Metrics tab, in sections with small headings."""
from tests.support import metrics, run


def test_the_sections_come_in_order(page):
    run(page, 300)
    page.evaluate("select(DES_TASKS.running.info)")
    card = metrics(page)
    assert card["headings"] == ["How it is measured", "Wait time by party", "Wait time on the clock", "Target"]
    assert card["measure"].startswith("Time the food stands on the pass") and card["charts"] == 2
    order = page.evaluate("[...document.querySelector('#metrics .metrics').children].map(node => node.className || node.tagName)")
    assert order[:5] == ["section", "measure", "figure", "figure", "section"] and order[5] == "measure" and order[6] == "metric-value"


def test_each_chart_is_a_figure_with_a_heading_a_grey_ground_and_a_caption(page):
    run(page, 120)
    page.evaluate("select(DES_RES.cooks.info)")
    metrics(page)
    figures = page.evaluate("""[...document.querySelectorAll('#metrics figure')].map(figure => [figure.children[0].tagName + '.' + figure.children[0].className, figure.children[1].className,
        figure.children[1].firstChild.tagName, figure.children[2].tagName, getComputedStyle(figure.children[1]).backgroundColor])""")
    assert figures == [["H4.section", "plot", "svg", "FIGCAPTION", "rgb(42, 42, 42)"]] * 2


def test_the_target_is_said_once_under_its_heading_then_the_verdict(page):
    run(page, 300)
    page.evaluate("select(DES_TASKS.running.info)")
    card = metrics(page)
    assert page.evaluate("[...document.querySelectorAll('#metrics .measure')][1].textContent") == "At most 0:10."
    assert not any(note.startswith("Target") for note in card["notes"]) and card["verdict"] in ("On target", "A little over target", "Over target")
    assert card["grade"] in ("good", "warn", "bad") and card["numbers"]["Waiting now"] != ""


def test_a_card_with_no_target_note_has_only_the_heading(page):
    page.evaluate("select(desPartsInfo)")
    card = metrics(page)
    assert card["headings"][-1] == "Target" and page.evaluate("document.querySelectorAll('#metrics .measure').length") == 1
    assert card["verdict"] == "No target" and card["grade"] == "none" and card["numbers"] == {}


def test_a_card_with_no_measure_starts_with_its_charts(page):
    page.evaluate("select({ nodes: [], name: 'Probe', metrics: () => ({ ...metricsFor(DES_RES.cooks.info), measure: '' }) })")
    assert metrics(page)["headings"][0] == "Use every 15 seconds"
    assert page.evaluate("document.querySelector('#metrics .metrics').firstElementChild.tagName") == "FIGURE"


def test_the_card_is_emptied_when_it_cannot_be_seen(page):
    page.evaluate("select(DES_RES.cooks.info)")
    metrics(page)
    page.evaluate("setTab('about'); renderMetrics()")
    assert page.evaluate("$('metrics').children.length") == 0
