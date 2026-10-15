"""js/cook-work.js: what a cook does, step by step."""
from tests.support import fixed_random, run, run_until


def test_cooks_use_stove_oven_and_coffee_machine_as_the_ticket_says(page):
    steps = page.evaluate("""[
        stepsFor(cooks[0], { stove: 2, oven: 0, coffee: 0 }), stepsFor(cooks[1], { stove: 0, oven: 3, coffee: 0 }),
        stepsFor(cooks[1], { stove: 1, oven: 1, coffee: 2 })].map(steps => steps.map(s => [s.station.name, s.time]))""")
    assert steps == [[["stove 1", 6.6]], [["the pizza oven", 7]],
                     [["stove 2", 5.3], ["the pizza oven", 5], ["the coffee machine", 2]]]


def test_releasing_a_station_frees_it(page):
    page.evaluate("Object.assign(pizzaOven, { on: true, busy: true, progress: 0.4 }); releaseStation(pizzaOven)")
    assert page.evaluate("[pizzaOven.on, pizzaOven.busy, pizzaOven.progress]") == [False, False, 0]


def test_a_cook_waits_when_the_shared_oven_is_busy(page):
    run_until(page, "cooks[0].state === 'grabbing'")
    page.evaluate("cooks[0].job.stove = 0; cooks[0].job.oven = 2; cooks[0].job.coffee = 0; pizzaOven.busy = true")
    run_until(page, "cooks[0].state === 'waitStation'")
    run(page, 2)
    assert page.evaluate("cooks[0].state") == "waitStation"
    page.evaluate("pizzaOven.busy = false")
    run_until(page, "cooks[0].state === 'working'")
    assert page.evaluate("[cooks[0].station === pizzaOven, pizzaOven.on, pizzaOven.busy, cooks[0].carry]") == [True, True, True, "ticket"]
    run(page, 1)
    assert page.evaluate("pizzaOven.progress > 0 && Number(pizzaOven.bar.getAttribute('width')) > 0 && Number(pizzaOven.flame.style.opacity) > 0")
    run_until(page, "cooks[0].state === 'toPass'")
    assert page.evaluate("[pizzaOven.on, pizzaOven.busy, pizzaOven.progress, cooks[0].carry]") == [False, False, 0, "plates"]


def test_a_cook_takes_the_oldest_ticket_and_puts_the_food_on_the_pass(page):
    fixed_random(page, 0, "spawnParty()")
    page.evaluate("nextArrival = 1e9; waiters.splice(1)")
    run_until(page, "rail.length === 1")
    page.evaluate("window.ticket = rail[0]")
    run_until(page, "ticket.stage === 'cooking'")
    assert page.evaluate("[rail.length, ticket.claimed, ticket.cook.name, ticket.cook.carry]") == [0, True, "Cook 1", "ticket"]
    run_until(page, "ticket.stage === 'pass'")
    assert page.evaluate("[pass.includes(ticket), ticket.claimed, cooks[0].carry, cooks[0].state]") == [True, False, None, "idle"]


def test_a_cook_with_nothing_to_do_walks_back_to_the_waiting_spot(page):
    fixed_random(page, 0, "spawnParty()")
    page.evaluate("nextArrival = 1e9")
    run_until(page, "delivered.length === 1")
    run(page, 20)
    assert page.evaluate("cooks.every(c => c.state === 'idle' && c.x === c.home.x && c.y === c.home.y)")
