"""js/guests.js: parties arriving, queuing, sitting, eating and leaving."""
from tests.support import card, click, fixed_random, run, run_until, seat_everyone


def test_party_sizes_follow_the_weights(page):
    sizes = page.evaluate("""() => {
        const real = Math.random, out = [];
        for (const r of [0, 0.1, 0.4, 0.6, 0.8, 0.99, 2]) { Math.random = () => r; out.push(pickSize()); }
        Math.random = real;
        return out;
    }""")
    assert sizes == [1, 2, 3, 4, 5, 6, 2]


def test_a_party_gets_the_smallest_table_that_fits(page):
    assert page.evaluate("[1, 2, 3, 4, 5, 6].map(size => findTable(size).capacity)") == [2, 2, 4, 4, 6, 6]
    page.evaluate("tables.filter(t => t.capacity === 2).forEach(t => setStatus(t, 'eating'))")
    assert page.evaluate("findTable(2).capacity") == 4
    page.evaluate("tables.forEach(t => setStatus(t, 'eating'))")
    assert page.evaluate("findTable(1)") is None


def test_guests_walk_in_sit_down_and_read_the_menu(page):
    page.evaluate("spawnParty()")
    assert page.evaluate("[parties.length, parties[0].state, parties[0].table.status]") == [1, "arriving", "reserved"]
    assert page.locator("#guests .guest").count() == page.evaluate("parties[0].size")
    run_until(page, "parties[0].state === 'seated'")
    assert page.evaluate("parties[0].table.status") == "reading"
    run(page, 3)
    assert page.evaluate("parties[0].members.every((m, i) => m.x === parties[0].table.seats[i].x && m.y === parties[0].table.seats[i].y)")
    run_until(page, "parties[0].table.status === 'ready'")
    assert page.locator(".table.ready .bubble").count() == 1


def test_parties_queue_at_the_door_and_are_turned_away_when_it_is_full(page):
    seat_everyone(page)
    assert page.evaluate("tables.every(t => t.status === 'reserved')")
    page.evaluate("nextArrival = 1e9")
    queued_before = page.evaluate("parties.filter(p => p.state === 'queue').length")
    page.evaluate("() => { const real = Math.random; Math.random = () => 0.99; for (let i = 0; i < 5; i++) spawnParty(); Math.random = real; }")
    assert page.evaluate("parties.filter(p => p.state === 'queue').length") == 3
    assert page.evaluate("turnedAway") == 5 - (3 - queued_before)
    run(page, 4)
    assert page.evaluate("parties.filter(p => p.state === 'queue').every(p => p.members[0].x === 18)")
    assert page.locator("#s-queue").inner_text() == "3"
    assert int(page.locator("#s-lost").inner_text()) >= 2
    # a six-top frees up: the first party in the queue takes it
    page.evaluate("() => { const t = tables.find(t => t.capacity === 6); parties.splice(parties.indexOf(t.party), 1)[0].members.forEach(m => m.el.remove()); t.party = null; setStatus(t, 'free'); }")
    run(page, 0.1)
    assert page.evaluate("parties.filter(p => p.state === 'queue').length") == 2


def test_party_names_for_one_guest_and_for_groups(page):
    names = page.evaluate("""() => {
        const real = Math.random, out = [];
        for (const r of [0, 0.8]) { Math.random = () => r; spawnParty(); const info = parties.at(-1).info; out.push(info.name, info.listName, info.what); }
        Math.random = real;
        return out;
    }""")
    assert names == ["Party 1: 1 guest", "Party 1", "One customer.",
                     "Party 2: 5 guests", "Party 2", "5 customers who came together and share a table."]


def test_a_new_party_has_a_number_a_colour_and_a_record_of_its_own(page):
    page.evaluate("spawnParty(); spawnParty()")
    assert page.evaluate("parties.map(p => [p.id, p.color, p.spent, p.info.subject === p])") == [[1, "#3987e5", {}, True], [2, "#d95926", {}, True]]


def test_a_party_can_say_what_it_ordered(page):
    page.evaluate("tables.forEach(t => setStatus(t, 'eating')); spawnParty(); window.p = parties[0]")
    ordered = "p.info.extra[0][1]()"
    assert page.evaluate(ordered) == "Nothing yet." and page.evaluate("'now' in p.info") is False
    page.evaluate("tables.forEach(t => setStatus(t, 'free'))")
    run_until(page, "p.table && p.table.status === 'eating'")
    assert page.evaluate(ordered) == page.evaluate("p.ticket.lines")


def test_a_selected_party_is_marked_until_it_leaves_and_then_the_card_closes(page):
    fixed_random(page, 0.99, "spawnParty()")
    page.evaluate("window.p = parties[0]; nextArrival = 1e9")
    click(page, "p.members[0].el")
    assert card(page)["kind"] == "Guests"
    assert page.locator("#guests [data-selected]").count() == 6
    run_until(page, "p.state === 'leaving'")
    assert page.evaluate("[served, p.table.party, p.table.status]") == [1, None, "free"]
    run_until(page, "!parties.includes(p)")
    assert card(page) is None
    assert page.locator("#guests .guest").count() == 0
    assert page.evaluate("p.spent.leaving > 0")   # the last step is closed off when the party goes
