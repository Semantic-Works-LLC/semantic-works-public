"""js/staff.js: waiters and cooks, how they walk, and changing how many there are."""
from tests.support import card, click, run, run_until, seat_everyone


def test_two_waiters_and_two_cooks_to_start_with(page):
    assert page.evaluate("waiters.map(w => [w.name, w.number, w.kind])") == [["Waiter 1", 1, "waiter"], ["Waiter 2", 2, "waiter"]]
    assert page.evaluate("cooks.map(c => [c.name, c.number, c.kind])") == [["Cook 1", 1, "cook"], ["Cook 2", 2, "cook"]]
    assert page.evaluate("[TEAM.waiter.wanted, TEAM.cook.wanted, STAFF_MAX]") == [2, 2, 6]
    assert page.locator("#staff > g").count() == 4


def test_staff_cards(page):
    click(page, "waiters[0].g")
    shown = card(page)
    assert shown["kind"] == "Waiter" and shown["name"] == "Waiter 1"
    click(page, "cooks[1].g")
    assert card(page)["kind"] == "Cook" and card(page)["name"] == "Cook 2"
    assert page.evaluate("waiters[0].g.hasAttribute('data-selected')") is False
    assert set(shown) == {"kind", "name", "What it is", "Purpose", "Why it is here"}


def test_waiters_walk_the_aisles_and_cooks_walk_straight(page):
    page.evaluate("go(waiters[0], tables[0].sp); go(cooks[0], { x: 1085, y: 200 })")
    assert page.evaluate("[waiters[0].path.length > 1, cooks[0].path.length, waiters[0].at === tables[0].sp]") == [True, 1, True]
    assert page.evaluate("advance(cooks[0], 0.1)") is False
    assert page.evaluate("advance(cooks[0], 60)") is True
    assert page.evaluate("[cooks[0].x, cooks[0].y]") == [1085, 200]
    assert page.evaluate("advance(waiters[0], 60) && waiters[0].x === tables[0].sp.x && waiters[0].y === tables[0].sp.y")


def test_adding_staff_gives_them_the_next_number_and_a_place_to_stand(page):
    page.evaluate("changeStaff('waiter', 1); changeStaff('cook', 1); changeStaff('cook', 1)")
    assert page.evaluate("waiters.map(w => w.name)") == ["Waiter 1", "Waiter 2", "Waiter 3"]
    assert page.evaluate("[waiters[2].home, waiters[2].speed, waiters[2].state]") == [{"x": 728, "y": 350}, 130, "idle"]
    assert page.evaluate("cooks.map(c => [c.name, c.stove.name])") == [["Cook 1", "stove 1"], ["Cook 2", "stove 2"], ["Cook 3", "stove 1"], ["Cook 4", "stove 2"]]
    assert page.evaluate("[TEAM.waiter.wanted, TEAM.cook.wanted]") == [3, 4]
    assert page.locator("#staff > g").count() == 7
    assert page.evaluate("[waiters[2].gauge !== undefined, waiters[2].info.subject === waiters[2]]") == [True, True]
    run(page, 120)
    assert page.evaluate("Object.keys(waiters[2].counts).length") > 1   # the new waiter has been working


def test_staff_numbers_stop_at_six_and_at_zero(page):
    page.evaluate("for (let i = 0; i < 9; i++) changeStaff('waiter', 1)")
    assert page.evaluate("[waiters.length, TEAM.waiter.wanted]") == [6, 6]
    page.evaluate("for (let i = 0; i < 9; i++) changeStaff('cook', -1); tick(0.05)")
    assert page.evaluate("[cooks.length, TEAM.cook.wanted]") == [0, 0]
    assert page.locator("#staff > g").count() == 6


def test_a_free_person_leaves_at_once(page):
    page.evaluate("changeStaff('waiter', -1)")
    assert page.evaluate("waiters.map(w => !!w.leaving)") == [False, True]
    before = page.evaluate("gauges.length")
    page.evaluate("tick(0.05)")
    assert page.evaluate("waiters.map(w => w.name)") == ["Waiter 1"]
    assert page.evaluate("gauges.length") == before - 1
    assert page.locator("#staff > g").count() == 3


def test_a_busy_person_finishes_the_job_first_and_can_be_kept_after_all(page):
    seat_everyone(page, 6)
    page.evaluate("nextArrival = 1e9")
    run_until(page, "waiters.every(w => w.state !== 'idle')")
    page.evaluate("changeStaff('waiter', -1)")
    assert page.evaluate("[waiters.length, waiters[1].leaving, TEAM.waiter.wanted]") == [2, True, 1]
    page.evaluate("tick(0.05)")
    assert page.evaluate("waiters.length") == 2   # still carrying on with the job in hand
    page.evaluate("changeStaff('waiter', 1)")
    assert page.evaluate("[waiters.length, waiters[1].leaving, TEAM.waiter.wanted]") == [2, False, 2]   # kept, not replaced
    page.evaluate("changeStaff('waiter', -1)")
    run_until(page, "waiters.length === 1")
    assert page.evaluate("tickets.every(t => t.waiter === waiters[0] || t.stage !== 'carried')")


def test_a_freed_number_is_used_again(page):
    page.evaluate("changeStaff('waiter', 1); waiters[0].leaving = true; tick(0.05); changeStaff('waiter', 1)")
    assert sorted(page.evaluate("waiters.map(w => w.name)")) == ["Waiter 1", "Waiter 2", "Waiter 3"]


def test_dismissing_the_selected_person_clears_the_selection(page):
    click(page, "cooks[1].g")
    page.evaluate("changeStaff('cook', -1); tick(0.05)")
    assert card(page) is None and page.evaluate("cooks.length") == 1
