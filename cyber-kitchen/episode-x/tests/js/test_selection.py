"""js/selection.js: what is selected, and the details panel with its folding sections and tabs."""
from tests.support import about, click, run


def test_nothing_is_selected_at_first_and_the_panel_says_how_to_select(page):
    assert about(page) is None and page.evaluate("$('tabs').hidden")
    assert page.locator("#about .empty").inner_text().startswith("Nothing selected. Click anything in the live view")


def test_selecting_marks_the_object_opens_the_panel_and_unfolds_selection(page):
    assert page.evaluate("[$('panel').classList.contains('open'), folds.selection]") == [False, False]
    page.evaluate("select(DES_RES.tables.units[6].info)")
    assert page.evaluate("[$('panel').classList.contains('open'), folds.selection, DES_RES.tables.units[6].info.nodes.every(node => node.hasAttribute('data-selected'))]") == [True, True, True]
    assert page.evaluate("document.querySelector('.fold[data-fold=selection] .fold-body').hidden") is False


def test_selecting_something_else_unmarks_the_first_and_nothing_clears_it(page):
    page.evaluate("select(DES_RES.tables.units[6].info); select(DES_RES.oven.units[0].info)")
    assert page.evaluate("document.querySelectorAll('#desview [data-selected]').length") == 1
    page.evaluate("select(null)")
    assert page.evaluate("document.querySelectorAll('[data-selected]').length") == 0 and about(page) is None


def test_the_about_tab_shows_only_the_rows_that_have_text_and_ends_with_the_objective(page):
    page.evaluate("select(DES_TASKS.plating.info)")
    card = about(page)
    assert list(card) == ["name", "Purpose", "Needs", "Objective"] and card["name"] == "Plating"
    assert card["Objective"] == "Get cooked food out of the kitchen and onto the pass as soon as the whole order is ready."
    page.evaluate("select(DES_RES.cooks.info)")
    assert list(about(page)) == ["name", "Kind", "What it is", "Purpose", "Why it is here", "Objective"]


def test_an_about_row_can_be_live(page):
    page.evaluate("select({ nodes: [], name: 'Probe', kind: 'Test', extra: [['Clock', () => clockText(clock)], ['Skipped', () => 'no']], metrics: () => metricsFor(DES_RES.cooks.info) })")
    assert "Clock" not in about(page), "a live value does not belong on About"


def test_the_panel_button_opens_and_closes_the_panel(page):
    page.click("#panel-toggle")
    assert page.evaluate("[$('panel').classList.contains('open'), $('panel-divider').classList.contains('open'), $('panel-toggle').title, $('icon-collapse').hasAttribute('hidden'), $('icon-expand').hasAttribute('hidden')]") == [True, True, "Hide details", False, True]
    page.click("#panel-toggle")
    assert page.evaluate("[$('panel').classList.contains('open'), $('panel-toggle').title, $('panel-toggle').getAttribute('aria-pressed')]") == [False, "Show details", "false"]


def test_sections_start_folded_and_fold_by_their_header(page):
    page.click("#panel-toggle")
    assert page.evaluate("[...document.querySelectorAll('.fold-body')].map(body => body.hidden)") == [True, True, True]
    page.click(".fold[data-fold=legend] header")
    assert page.evaluate("[folds.legend, document.querySelector('.fold[data-fold=legend] .fold-toggle').getAttribute('aria-label')]") == [True, "Collapse Legend"]
    page.click(".fold[data-fold=legend] header")
    assert page.evaluate("[folds.legend, document.querySelector('.fold[data-fold=legend] .fold-toggle').getAttribute('aria-expanded')]") == [False, "false"]


def test_the_tab_and_the_folds_stay_as_they_were_left(page):
    page.evaluate("select(DES_TASKS.oven.info)")
    page.click("#tabs [data-tab=metrics]")
    page.click(".fold[data-fold=events] header")
    page.evaluate("select(DES_RES.cooks.info); setView('graph'); select(DES_RES.tables.info)")
    assert page.evaluate("[detailsTab, folds.events, $('metrics').hidden, $('about').hidden, $('tabs').querySelector('[aria-selected=true]').dataset.tab]") == ["metrics", True, False, True, "metrics"]


def test_only_the_chosen_tab_shows(page):
    page.evaluate("select(DES_TASKS.oven.info)")
    for tab in ["about", "metrics", "actions"]:
        page.click(f"#tabs [data-tab={tab}]")
        assert page.evaluate("['about', 'metrics', 'actions'].filter(id => !$(id).hidden)") == [tab]
    page.evaluate("select(null)")
    assert page.evaluate("['about', 'metrics', 'actions'].filter(id => !$(id).hidden)") == ["about"], "with nothing selected only the hint shows"


def test_metrics_are_drawn_only_when_they_can_be_seen(page):
    page.evaluate("select(DES_TASKS.oven.info)")
    assert page.evaluate("metricsShowing()") is False
    page.evaluate("setTab('metrics')")
    assert page.evaluate("metricsShowing() && $('metrics').children.length") == 1
    page.evaluate("setFold('selection', false)")
    assert page.evaluate("[metricsShowing(), $('metrics').children.length]") == [False, 0]
    page.evaluate("setFold('selection', true); setPanel(false)")
    assert page.evaluate("metricsShowing()") is False


def test_the_event_stream_lists_the_latest_events_newest_first_under_their_count(page):
    run(page, 60)
    page.evaluate("setPanel(true); setFold('events', true)")
    lines = page.locator("#events").inner_text().split("\n")
    assert page.locator("#events-total").inner_text() == f"{page.evaluate('desEngine.eventsProcessed')} events processed"
    assert len(lines) == page.evaluate("desRecent.length") and float(lines[0].split()[0]) >= float(lines[-1].split()[0])
    assert lines[-1].split()[1:3] == ["PARTY_ARRIVED", "P1"]


def test_the_event_stream_holds_still_while_it_is_scrolled_or_out_of_sight(page):
    run(page, 120)
    page.evaluate("setPanel(true); setFold('events', true); $('events').scrollTop = 40")
    before = page.locator("#events").inner_text()
    run(page, 30)
    page.evaluate("renderEvents()")
    assert page.locator("#events").inner_text() == before and page.locator("#events-total").inner_text() != ""
    page.evaluate("$('events').scrollTop = 0; renderEvents()")
    after = page.locator("#events").inner_text()
    assert after != before
    page.evaluate("setFold('events', false)")
    run(page, 30)
    page.evaluate("renderEvents(); setFold('events', true); setPanel(false); renderEvents()")
    assert page.evaluate("$('events').textContent.length") > 0


def test_the_picker_opens_empty_filtered_and_focused(page):
    page.evaluate("$('picker-filter').value = 'old'; setPicker(true)")
    assert page.evaluate("[$('picker').hidden, $('picker-filter').value, document.activeElement.id, $('picker-toggle').getAttribute('aria-expanded')]") == [False, "", "picker-filter", "true"]
    page.evaluate("setPicker(false)")
    assert page.evaluate("$('picker').hidden")
