"""js/drawing.js: drawing the moving parts of the restaurant floor, and the counters."""
from tests.support import card, click, fixed_random, run, run_until, seat_everyone


def test_starts_empty_with_all_counters_at_zero(page):
    page.evaluate("draw()")
    assert page.locator(".stat .value").all_inner_texts() == ["0:00", "0", "0", "0", "0", "0", "0", "0"]


def test_counters_match_the_simulation(page):
    run(page, 120.5)
    expected = page.evaluate("""[
        parties.filter(p => p.state !== 'queue').reduce((sum, p) => sum + p.size, 0),
        parties.filter(p => p.state === 'queue').length, rail.length,
        cooks.filter(c => ['toStation', 'working', 'waitStation'].includes(c.state)).length, pass.length, served, turnedAway]""")
    assert page.locator(".stat .value").all_inner_texts()[1:] == [str(n) for n in expected]
    assert page.locator("#s-clock").inner_text() == "2:00"


def test_people_are_drawn_where_they_are_and_show_what_they_carry(page):
    run_until(page, "waiters.some(w => w.carry === 'ticket')")
    waiter = "waiters.find(w => w.carry === 'ticket')"
    assert page.evaluate(f"{waiter}.g.getAttribute('transform') === `translate(${{{waiter}.x}} ${{{waiter}.y}})`")
    assert page.evaluate(f"[{waiter}.ticket.getAttribute('visibility'), {waiter}.tray.getAttribute('visibility')]") == ["visible", "hidden"]
    run_until(page, "waiters.some(w => w.carry === 'plates')")
    assert page.evaluate("waiters.find(w => w.carry === 'plates').tray.getAttribute('visibility')") == "visible"
    assert page.evaluate("parties.every(p => p.members.every(m => Number(m.el.getAttribute('cx')) === m.x && Number(m.el.getAttribute('cy')) === m.y))")


def test_a_station_glows_and_fills_its_bar_while_in_use(page):
    run_until(page, "stations.some(s => s.on && s.progress > 0.3)")
    busy, idle = "stations.find(s => s.on)", "stations.find(s => !s.on)"
    assert page.evaluate(f"Number({busy}.flame.style.opacity) >= 0.3 && Number({busy}.bar.getAttribute('width')) > 15")
    assert page.evaluate(f"[{idle}.flame.style.opacity, {idle}.bar.getAttribute('width')]") == ["0", "0"]


def test_rail_and_pass_show_tickets_and_overflow(page):
    seat_everyone(page, 8)
    page.evaluate("nextArrival = 1e9; cooks.splice(0)")   # no cooks: tickets pile up on the rail
    run_until(page, "rail.length === 8")
    assert page.locator("#rail [data-selectable]").count() == 5
    assert page.locator("#rail .small-label").text_content() == "+3"
    assert page.locator("#s-rail").inner_text() == "8"
    page.evaluate("waiters.splice(0); rail.splice(0).forEach(t => { pass.push(t); moveTicket(t, 'pass'); }); draw()")
    assert page.locator("#rail [data-selectable]").count() == 0
    assert page.locator("#pass [data-selectable]").count() == 6
    assert page.locator("#s-pass").inner_text() == "8"


def test_a_selected_ticket_is_marked_wherever_it_is_drawn(page):
    fixed_random(page, 0, "spawnParty()")
    page.evaluate("nextArrival = 1e9")
    run_until(page, "rail.length === 1")
    page.evaluate("window.ticket = rail[0]; draw()")
    click(page, "document.querySelector('#rail [data-selectable]')")
    assert card(page)["kind"] == "Order ticket"
    assert page.locator("#rail [data-selected]").count() == 1
    run_until(page, "ticket.stage === 'cooking'")
    assert page.locator("#view [data-selected]").count() == 0   # the paper is in the cook's hand now
    run_until(page, "ticket.stage === 'pass'")
    assert page.locator("#pass [data-selected]").count() == 1
    click(page, "tables[0].g")
    page.evaluate("draw()")
    assert page.locator("#pass [data-selected]").count() == 0


def test_food_on_the_pass_can_be_selected(page):
    seat_everyone(page, 3)
    run_until(page, "pass.length === 1")
    click(page, "document.querySelector('#pass [data-selectable]')")
    assert card(page)["kind"] == "Order ticket" and page.evaluate("selected === pass[0].info")


def test_the_service_view_is_drawn_only_while_it_is_showing(page):
    run(page, 20)
    assert page.evaluate("loopTokens.size") == 0
    page.click("#view-toggle")
    run(page, 1)
    assert page.evaluate("loopTokens.size") > 0
