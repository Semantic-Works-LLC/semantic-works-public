"""js/tracking.js: the measuring that runs on every tick and feeds the metrics."""
import pytest

from tests.support import fixed_random, run, run_until


def test_a_stay_starts_now_and_old_finished_stays_are_dropped(page):
    made = page.evaluate("""() => {
        clock = 500;
        const list = [{ start: 10, end: 20 }, { start: 300, end: 310 }, { start: 400, end: 450 }, { start: 5, end: null }];
        const one = stay(list);
        return [one, list.map(s => s.start)];
    }""")
    assert made == [{"start": 500, "end": None}, [400, 5, 500]]   # anything that ended more than three minutes ago goes


def test_leaving_a_step_closes_the_stay_and_adds_to_the_steps_record(page):
    result = page.evaluate("""() => {
        clock = 30;
        const party = { step: 'menu', stepSince: 22, stay: { start: 22, end: null }, spent: {} };
        leaveStep(party);
        leaveStep({});   // a party that never entered a step: nothing to close
        return [party.stay, party.spent, FLOW.menu.done, FLOW.menu.total, FLOW.menu.history];
    }""")
    assert result == [{"start": 22, "end": 30}, {"menu": 8}, 1, 8, [8]]


def test_a_step_keeps_only_its_latest_forty_times(page):
    history = page.evaluate("""() => {
        for (let i = 1; i <= 45; i++) { clock = i; leaveStep({ step: 'menu', stepSince: 0, stay: {}, spent: {} }); }
        return FLOW.menu.history;
    }""")
    assert history == list(range(6, 46)) and page.evaluate("[FLOW.menu.done, KEEP]") == [45, 40]


def test_every_table_person_station_and_queue_has_a_gauge(page):
    assert page.evaluate("gauges.length") == 12 + 4 + 4 + 3
    assert page.evaluate("tables.every(t => t.gauge && t.info.subject === t) && stations.every(s => s.gauge && s.info.subject === s)")
    assert page.evaluate("[...waiters, ...cooks].every(s => s.gauge && s.info.subject === s && s.was === 'idle')")
    assert page.evaluate("STEPS.every(step => step.info.subject === step)")
    assert page.evaluate("Object.keys(QUEUE_LENGTH)") == ["door", "rail", "pass"]


def test_a_gauge_adds_up_its_reading_and_keeps_a_fifteen_second_history(page):
    page.evaluate("nextArrival = 1e9; window.g = gauge(() => clock < 20 ? 1 : 0)")
    run(page, 14)
    assert page.evaluate("[g.history.length, g.changes.length, g.changes[0][1]]") == [0, 1, 1]
    run(page, 16.5)
    assert page.evaluate("g.history.length") == 2
    assert page.evaluate("g.history[0]") == pytest.approx(1, abs=0.01)
    assert page.evaluate("g.history[1]") == pytest.approx(1 / 3, abs=0.02)
    assert page.evaluate("g.sum") == pytest.approx(20, abs=0.1)
    assert page.evaluate("g.changes.map(change => change[1])") == [1, 0]
    assert page.evaluate("g.changes[1][0]") == pytest.approx(20, abs=0.06)


def test_gauges_keep_forty_slices_and_only_recent_changes(page):
    page.evaluate("() => { for (let i = 0; i < 20 * 660; i++) tick(0.05); }")
    assert page.evaluate("gauges.every(g => g.history.length === 40)")   # 44 slices have gone by
    busiest = "waiters[0].gauge.changes"
    assert page.evaluate(f"{busiest}.length") > 3
    assert page.evaluate(f"{busiest}.filter(change => change[0] < clock - WINDOW - 60).length") <= 1   # old changes are dropped


def test_queue_gauges_read_the_door_the_rail_and_the_pass(page):
    page.evaluate("tables.forEach(t => setStatus(t, 'eating')); spawnParty(); rail.push({}, {}); pass.push({})")
    assert page.evaluate("[QUEUE_LENGTH.door.read(), QUEUE_LENGTH.rail.read(), QUEUE_LENGTH.pass.read()]") == [1, 2, 1]


def test_tracking_counts_what_staff_finish_and_who_sits_where(page):
    fixed_random(page, 0.99, "spawnParty()")
    page.evaluate("nextArrival = 1e9; window.t = parties[0].table")
    run_until(page, "parties.length === 0")
    assert page.evaluate("[t.seated, t.guests, t.was]") == [1, 6, "free"]
    assert page.evaluate("waiters.map(w => [w.counts.taking || 0, w.counts.serving || 0]).reduce((a, b) => [a[0] + b[0], a[1] + b[1]])") == [1, 1]
    assert page.evaluate("cooks.reduce((n, c) => n + (c.counts.plating || 0), 0)") == 1


def test_tracking_gives_each_party_a_step_a_start_and_a_stay(page):
    page.evaluate("spawnParty(); trackFlow(0)")
    assert page.evaluate("[parties[0].step, parties[0].stepSince, parties[0].start, parties[0].stay === FLOW.walkIn.stays[0]]") == ["walkIn", 0, 0, True]
    run_until(page, "parties[0].step === 'menu'")
    assert page.evaluate("[parties[0].start, FLOW.walkIn.stays[0].end === parties[0].stepSince, parties[0].spent.walkIn > 0]") == [0, True, True]


def test_food_is_on_its_way_to_the_pass_once_the_cook_has_finished(page):
    check = "onItsWayToPass({ stage: '%s', cook: { state: '%s' } })"
    assert page.evaluate(check % ("cooking", "toPass")) and page.evaluate(check % ("cooking", "plating"))
    assert not page.evaluate(check % ("cooking", "working"))
    assert not page.evaluate("onItsWayToPass({ stage: 'rail' })")
