"""js/scorecard.js: the owner's nine figures, each with its own card and coloured by its target."""
import pytest

from tests.support import about, click, metrics, run, run_until, show, spec

ORDER = ["Events so far", "λ · arrivals per minute", "L · in the building now", "L · average", "W · average time inside",
         "λ × W · predicted L", "Gap · average L, λ × W", "Average wait for food", "Happy visits"]


def tile(page, name):
    return page.evaluate("""name => { drawScore(); const t = SCORE.find(one => one.name === name);
        return { value: t.text.textContent, edge: t.box.getAttribute('class').replace('des-stage', '').replace('score-tile', '').trim() || 'plain' }; }""", name)


def test_nine_boxes_three_by_three_from_the_most_granular_to_the_outcome(page):
    show(page, "score")
    assert page.evaluate("SCORE.map(one => one.label)") == ORDER
    places = page.evaluate("SCORE.map(one => [Number(one.box.getAttribute('x')), Number(one.box.getAttribute('y'))])")
    assert len({x for x, _ in places}) == 3 and len({y for _, y in places}) == 3 and places == sorted(places, key=lambda p: (p[1], p[0]))


def test_before_anything_has_happened(page):
    show(page, "score")
    assert [tile(page, name)["value"] for name in ["Events so far", "Average time inside", "Happy visits", "Average wait for food", "Gap between average and predicted"]] == ["0", "–", "–", "–", "–"]
    assert {tile(page, one)["edge"] for one in page.evaluate("SCORE.map(one => one.name)")} == {"plain"}


def test_the_boxes_show_the_engines_figures(page):
    show(page, "score")
    run(page, 600)
    t = page.evaluate("desEngine.telemetry()")
    assert tile(page, "Events so far")["value"] == f"{page.evaluate('desEngine.eventsProcessed'):,}"
    assert tile(page, "Parties in the building now")["value"] == str(t["L"])
    assert tile(page, "Arrivals per minute")["value"] == f"{t['lambda'] * 60:.1f}" and tile(page, "Parties in the building, average")["value"] == f"{t['averageL']:.1f}"
    assert tile(page, "Parties in the building, predicted")["value"] == f"{t['predictedL']:.1f}"
    gap = tile(page, "Gap between average and predicted")["value"]
    assert gap[0] in "+−" and gap.endswith("%)")


def test_a_box_with_a_target_is_outlined_by_how_it_stands(page):
    show(page, "score")
    run(page, 600)
    assert tile(page, "Happy visits")["edge"] in ("won", "near", "lost") and tile(page, "Events so far")["edge"] == "plain"
    edges = page.evaluate("Object.entries({ good: 'won', warn: 'near', bad: 'lost', none: '' }).every(([grade, edge]) => SCORE_EDGE[grade] === edge)")
    assert edges
    colours = page.evaluate("""['won', 'near', 'lost'].map(edge => { const box = SCORE[0].box; box.setAttribute('class', 'des-stage ' + edge); return getComputedStyle(box).stroke; })""")
    assert colours == [page.evaluate(f"(() => {{ const probe = document.createElement('i'); probe.style.color = 'var(--{name})'; document.body.append(probe); return getComputedStyle(probe).color; }})()") for name in ["eating", "ready", "waiting"]]


def test_each_box_is_selected_by_itself_and_is_of_kind_scorecard(page):
    show(page, "score")
    for index, name in enumerate(page.evaluate("SCORE.map(one => one.name)")):
        click(page, f"SCORE[{index}].box")
        card = about(page)
        assert card["name"] == name and card["Kind"] == "Scorecard" and card["Purpose"] and card["Objective"]
        assert page.evaluate("document.querySelectorAll('#scoreview [data-selected]').length") == 1


@pytest.mark.parametrize("index", range(9))
def test_every_box_has_its_own_charts_and_target(page, index):
    show(page, "score")
    run(page, 300)
    click(page, f"SCORE[{index}].box")
    card = metrics(page)
    assert card["headings"][0] == "How it is measured" and card["headings"][-1] == "Target" and card["charts"] == 2
    assert len(card["headings"]) == 4 and card["headings"][1] != card["headings"][2] and "The same" not in "".join(card["headings"])
    assert page.evaluate("document.querySelectorAll('#metrics .plot svg rect').length") > 3


def test_three_boxes_have_targets_and_six_are_kept_for_the_record(page):
    run(page, 600)
    targets = page.evaluate("SCORE.map(one => metricsFor(one.info).notes.find(isTargetNote))")
    assert [t for t in targets if t.startswith("Target")] == ["Target: at most 2 parties apart.", "Target: at most 1:00.", "Target: at least 80%."]
    assert targets.count("No target: kept for the record.") == 6


def test_the_gap_is_judged_by_its_size(page):
    verdicts = page.evaluate("""[0.5, 2.3, 9].map(gap => { scoreAt = clock; scoreNow = { L: 1, averageL: 5 + gap, lambda: 1, W: 5, predictedL: 5, sample: 3 };
        const tile = SCORE.find(one => one.label.startsWith('Gap')); return [tile.value(), tile.verdict()[1]]; })""")
    assert verdicts == [["+0.5 (9%)", "good"], ["+2.3 (32%)", "warn"], ["+9.0 (64%)", "bad"]]
    below = page.evaluate("(() => { scoreAt = clock; scoreNow = { L: 1, averageL: 3, lambda: 1, W: 5, predictedL: 5, sample: 3 }; return SCORE.find(one => one.label.startsWith('Gap')).value(); })()")
    assert below == "−2.0 (67%)"


def test_telemetry_is_read_once_per_tick(page):
    assert page.evaluate("scoreT() === scoreT()")
    run(page, 1)
    assert page.evaluate("(() => { const before = scoreNow; tick(0.05); return scoreT() !== before; })()")


# ---------- the wait for food ----------

def test_the_wait_for_food_is_the_average_over_the_last_three_minutes(page):
    run(page, 600)
    shown = tile(page, "Average wait for food")
    assert shown["value"] == page.evaluate("clockText(scoreFoodLog.reduce((s, one) => s + one.waited, 0) / scoreFoodLog.reduce((s, one) => s + one.served, 0))")
    assert page.evaluate("scoreFoodLog.every(one => one.at >= clock - WINDOW)") and shown["edge"] in ("won", "near", "lost")


def test_with_no_cooks_or_no_waiters_the_wait_is_infinite_and_red(page):
    run(page, 300)
    page.evaluate("desEngine.changeCapacity('cooks', -1); desEngine.changeCapacity('cooks', -1)")
    run_until(page, "desEngine.resources.cooks.capacity === 0")
    assert tile(page, "Average wait for food") == {"value": "∞", "edge": "lost"}
    card = spec(page, "SCORE.find(one => one.name === 'Average wait for food').info")
    assert card["value"] == "∞" and card["unit"] == "no food is being served" and card["verdict"] == ["Off target", "bad"]
    run(page, 900, dt=0.25)
    assert tile(page, "Average wait for food")["value"] == "∞", "it does not drift back to an old number"
    page.evaluate("desEngine.changeCapacity('cooks', 1); desEngine.changeCapacity('cooks', 1)")
    run(page, 400)
    assert tile(page, "Average wait for food")["value"] != "∞"


def test_parties_waiting_with_nothing_served_also_counts_as_infinite(page):
    page.evaluate("desEngine.setOut('stoves', 0, true); desEngine.setOut('stoves', 1, true); desEngine.setOut('oven', 0, true)")
    run_until(page, "[...desEngine.parties.values()].some(party => party.timestamps.orderPlaced !== undefined)")
    assert tile(page, "Average wait for food") == {"value": "∞", "edge": "lost"}


def test_the_card_of_the_wait_for_food_measures_each_party(page):
    run(page, 600)
    card = spec(page, "SCORE.find(one => one.name === 'Average wait for food').info")
    assert card["chartTitle"] == "Wait time by party" and card["unit"] == "on average, over the last three minutes" and "∞" in card["measure"]


# ---------- the footnote ----------

def test_the_footnote_explains_the_page_and_littles_law_in_small_centred_type(page):
    show(page, "score")
    lines = page.evaluate("[...document.querySelectorAll('#score-static > text')].map(line => [line.textContent, getComputedStyle(line).fontSize, getComputedStyle(line).textAnchor])")
    assert lines[0][0] == "This is the dashboard of the key business objectives, measured over the last three minutes."
    assert lines[1][0].startswith("Little's Law:") and len(lines) == 4 and {size for _, size, _ in lines} == {"5.7px"} and {anchor for _, _, anchor in lines} == {"middle"}
    centre = page.evaluate("(() => { const boxes = SCORE.map(one => one.box.getBBox()); return (Math.min(...boxes.map(b => b.x)) + Math.max(...boxes.map(b => b.x + b.width))) / 2; })()")
    assert page.evaluate("[...document.querySelectorAll('#score-static > text')].map(line => { const b = line.getBBox(); return b.x + b.width / 2; })") == pytest.approx([centre] * 4, abs=1)
    assert not page.evaluate("[...document.querySelectorAll('#score-static text')].some(line => line.textContent.includes('OPERATIONS'))")


def test_the_gap_with_nobody_inside_on_average(page):
    assert page.evaluate("(() => { scoreAt = clock; scoreNow = { L: 0, averageL: 0, lambda: 1, W: 5, predictedL: 0, sample: 3 }; return SCORE.find(one => one.label.startsWith('Gap')).value(); })()") == "+0.0 (0%)"
