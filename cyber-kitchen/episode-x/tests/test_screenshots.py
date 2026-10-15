"""Screenshots of every view, in tests/screenshots/<view>/.

They are meant to be checked in, so a later change to the look of the page shows up as a changed image
in version control. The page is made deterministic for them: the simulation is seeded, and time only
moves when the test moves it (see INIT_SCRIPT in conftest.py).

What is left is the browser's own drawing. From run to run a few dozen to a couple of hundred pixels
come out slightly lighter or darker although the page is identical: on the rounded edges of the page's
buttons and cards, along the panel's scrollbar and, when the machine is busy, on the edges of small text
and thin lines in the pictures. The largest such difference measured was 10 levels of 255, on 162
pixels of 1.26 million. So a screenshot counts as matching when it differs from the checked-in file by
no more than TOLERANCE, and the file is then left exactly as it is, byte for byte. A real change is far
larger: rewording one heading moved about 900 pixels by up to 111 levels.

A screenshot that does not match FAILS its test. What the page looks like now is written beside the
report, in coverage/screenshots/, so the two can be compared. If the new look is what is wanted, run
`make screenshots` (the same tests with UPDATE_SCREENSHOTS=1), which replaces the checked-in files.
"""
import base64
import os

import pytest

from tests.conftest import SCREENSHOTS
from tests.support import click, right_click, run, run_until, settle, show

TOLERANCE = {"level": 16, "pixels": 3000}   # at most this many pixels may differ, each by at most this much per channel (of 255)
UPDATE = os.environ.get("UPDATE_SCREENSHOTS") == "1"
ACTUAL = SCREENSHOTS.directory.parent.parent / "coverage" / "screenshots"   # where a screenshot that does not match is put
MISMATCHES = []   # the screenshots of the test that is running which did not match


@pytest.fixture(autouse=True)
def every_screenshot_matches():
    """Take all the screenshots of a test, then fail it if any of them did not match."""
    MISMATCHES.clear()
    yield
    assert not MISMATCHES, ("these screenshots do not match the checked-in ones (the new ones are in coverage/screenshots/; "
                            "run `make screenshots` to accept them): " + "; ".join(MISMATCHES))


def difference(page, old, new):
    """Compare two PNG files pixel by pixel, in the browser. Returns None for different sizes, else [pixels that differ, biggest difference]."""
    return page.evaluate("""async ([a, b]) => {
        const load = async data => { const image = new Image(); image.src = 'data:image/png;base64,' + data; await image.decode();
            const canvas = new OffscreenCanvas(image.width, image.height), context = canvas.getContext('2d'); context.drawImage(image, 0, 0);
            return context.getImageData(0, 0, image.width, image.height); };
        const one = await load(a), two = await load(b);
        if (one.width !== two.width || one.height !== two.height) return null;
        let pixels = 0, most = 0;
        for (let i = 0; i < one.data.length; i += 4) {
            const d = Math.max(Math.abs(one.data[i] - two.data[i]), Math.abs(one.data[i + 1] - two.data[i + 1]), Math.abs(one.data[i + 2] - two.data[i + 2]));
            if (d) { pixels++; if (d > most) most = d; }
        }
        return [pixels, most];
    }""", [base64.b64encode(old).decode(), base64.b64encode(new).decode()])


def steady(page):
    """Wait out the panel's slide, lay the picture out for the card it now has, and let everything settle."""
    page.wait_for_timeout(450)
    settle(page)


def snap(page, name):
    path = SCREENSHOTS.directory / f"{name}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    before = path.read_bytes() if path.exists() else None
    steady(page)
    shot = page.screenshot(animations="disabled")
    assert len(shot) > 10_000
    state = "new"
    if before is not None:
        found = difference(page, before, shot)
        same = found is not None and found[0] <= TOLERANCE["pixels"] and found[1] <= TOLERANCE["level"]
        state = "unchanged" if same else "CHANGED (another size)" if found is None else f"CHANGED ({found[0]} pixels, by up to {found[1]} of 255)"
    if state == "new" or (UPDATE and state != "unchanged"):
        path.write_bytes(shot)
    elif state != "unchanged":
        actual = ACTUAL / f"{name}.png"
        actual.parent.mkdir(parents=True, exist_ok=True)
        actual.write_bytes(shot)
        MISMATCHES.append(f"{name}.png {state[8:]}")
    SCREENSHOTS.results.append((name + ".png", state))


def details(page, info, tab, legend=False, events=False):
    """Select something and show one tab of its card, with the other sections folded or not."""
    page.evaluate(f"select({info}); setPanel(true); setFold('selection', true); setTab('{tab}'); setFold('legend', {str(legend).lower()}); setFold('events', {str(events).lower()}); renderActions()")


BUSY = 150   # seconds into service: the seeded restaurant is always at the same moment


# ---------- Floor Plan ----------

def test_floor_plan(page):
    folder = "floor-plan/"
    snap(page, folder + "01-opening")
    run(page, BUSY)
    snap(page, folder + "02-busy")
    page.evaluate("setPanel(true); setFold('legend', true)")
    snap(page, folder + "03-details-legend")
    page.evaluate("setFold('legend', false)")
    click(page, "desFloorTables[4].g")
    snap(page, folder + "04-table-selected-about")
    details(page, "DES_RES.tables.units[4].info", "metrics")
    snap(page, folder + "05-table-selected-metrics")
    details(page, "DES_RES.cooks.units[0].info", "actions")
    snap(page, folder + "06-cook-selected-actions")
    details(page, "desPartyInfo([...desEngine.parties.keys()][0])", "metrics")
    snap(page, folder + "07-party-selected-metrics")
    page.evaluate("select(null); setFold('events', true)")
    snap(page, folder + "08-details-event-stream")


def test_floor_plan_states(page):
    folder = "floor-plan/"
    page.evaluate("for (let i = 0; i < 12; i++) if (i !== 2 && i !== 9) desEngine.setOut('tables', i, true)")
    run_until(page, "desEngine.queues.host.length === 3")
    click(page, "DES_QUEUE.host.info.nodes[0].querySelector('.des-rail')")
    snap(page, folder + "09-waiting-area-host-queue")
    page.evaluate("select(null); setPanel(false); for (let i = 0; i < 12; i++) desEngine.setOut('tables', i, false); desEngine.setOut('tables', 5, true); desEngine.setOut('tables', 6, true); desEngine.setOut('oven', 0, true); desEngine.setOut('cooks', 1, true)")
    run(page, 90)
    snap(page, folder + "10-out-of-service")
    right_click(page, "DES_EQUIPMENT.oven[0].flame")
    page.evaluate("setPanel(false)")
    snap(page, folder + "11-right-click-menu")
    page.evaluate("document.body.click(); select(null); setPanel(false)")
    page.click("#picker-toggle")
    snap(page, folder + "12-picker")
    page.click("#view-toggle")
    snap(page, folder + "13-view-menu")
    page.click("#speed-toggle")
    snap(page, folder + "14-speed-menu")
    page.evaluate("document.body.click(); zoomBy(2.5); const zoom = zoomState().zoom; zoom.cx = 480; zoom.cy = 300; applyZoom()")
    snap(page, folder + "15-zoomed-in-on-the-kitchen")


# ---------- Process Map ----------

def test_process_map(page):
    folder = "process-map/"
    show(page, "graph")
    snap(page, folder + "01-opening")
    run(page, BUSY)
    snap(page, folder + "02-busy")
    page.evaluate("setPanel(true); setFold('legend', true)")
    snap(page, folder + "03-details-legend")
    details(page, "DES_TASKS.plating.info", "about")
    snap(page, folder + "04-step-selected-about")
    details(page, "DES_TASKS.plating.info", "metrics")
    snap(page, folder + "05-step-selected-metrics")
    details(page, "DES_TASKS.plating.info", "actions")
    snap(page, folder + "06-step-selected-actions")
    details(page, "DES_RES.cooks.info", "metrics")
    snap(page, folder + "07-resource-selected-metrics")
    details(page, "DES_OUTCOME.out.info", "metrics")
    snap(page, folder + "08-outcome-selected-metrics")
    details(page, "desArrivalsInfo", "metrics")
    snap(page, folder + "09-door-selected-metrics")
    details(page, "desPartiesInfo", "metrics")
    snap(page, folder + "10-parties-selected-metrics")
    click(page, "GRAPH_TOP[0].squares[1]")
    snap(page, folder + "11-one-party-selected-about")


def test_process_map_pin_and_unpin(page):
    folder = "process-map/pinned/"
    show(page, "graph")
    run(page, BUSY)
    for number, (key, name) in enumerate([("plating", "step-plate-food"), ("oven", "step-bake-pizza"), ("ordering", "step-order"), ("source", "door"),
                                          ("hungry", "outcome-left-slow-kitchen"), ("out", "outcome-dined"), ("res:cooks", "resource-cooks"),
                                          ("res:waiters", "resource-waiters"), ("res:tables", "resource-tables"), ("unit:cooks:0", "unit-cook-1"),
                                          ("unit:tables:6", "unit-table-7"), ("parties", "all-parties")], start=1):
        page.evaluate(f"graphPin('{key}')")
        run(page, 4)
        snap(page, f"{folder}{number:02d}-{name}")
    page.evaluate("window.mine = [...desEngine.parties.values()].find(party => party.state === 'COOKING' || party.state === 'WAITING_FOR_COOK').id; graphPin('party:' + mine)")
    snap(page, folder + "13-party-waiting-for-its-food")
    run_until(page, "desEngine.parties.get(mine)?.state === 'EATING_AND_BILLING'")
    snap(page, folder + "14-party-dining")
    run_until(page, "!desEngine.parties.has(mine)")
    page.evaluate("select(desPartyInfo(mine)); setTab('metrics')")
    snap(page, folder + "15-party-visit-over-still-pinned")
    page.evaluate("select(null); setPanel(false); graphPin('res:cooks'); select(DES_TASKS.oven.info); setTab('actions')")
    snap(page, folder + "16-pinned-is-not-selected")
    page.evaluate("select(DES_RES.cooks.info); renderActions()")
    snap(page, folder + "17-pinned-and-selected-offers-unpin")
    page.evaluate("document.querySelector('#actions [data-action=unpin]').click(); select(null); setPanel(false)")
    snap(page, folder + "18-unpinned-the-whole-map-again")


def test_process_map_states(page):
    folder = "process-map/"
    show(page, "graph")
    run(page, 60)
    page.evaluate("desEngine.setOut('oven', 0, true); desEngine.setOut('cooks', 1, true); desEngine.setOut('tables', 5, true); desEngine.changeCapacity('waiters', 1)")
    run(page, 150)
    snap(page, folder + "12-out-of-service-and-three-waiters")
    right_click(page, "GRAPH_TOP[5].squares[0]")
    page.evaluate("setPanel(false)")
    snap(page, folder + "13-right-click-a-broken-oven")
    page.evaluate("document.body.click(); select(null); setPanel(false)")
    right_click(page, "GRAPH_TOP[3].squares[0]")
    page.evaluate("setPanel(false)")
    snap(page, folder + "14-right-click-a-cook")
    page.evaluate("document.body.click(); select(null); setPanel(false); desEngine.changeCapacity('cooks', -1)")
    run_until(page, "desEngine.abandonedFor.food >= 2 && desEngine.balked >= 2")
    snap(page, folder + "15-losing-parties")
    page.evaluate("zoomBy(2.2); const zoom = zoomState().zoom; zoom.cx = 500; zoom.cy = 420; applyZoom()")
    snap(page, folder + "16-zoomed-in-on-the-kitchen-steps")


def test_process_map_on_a_tall_window(browser, site_server):
    from tests.conftest import open_page
    page, finish = open_page(browser, site_server[0] + "#graph", width=900, height=1200)
    run(page, BUSY)
    snap(page, "process-map/17-tall-window-outcomes-at-the-bottom")
    finish()


# ---------- Scorecard ----------

def test_scorecard(page):
    folder = "scorecard/"
    show(page, "score")
    snap(page, folder + "01-opening")
    run(page, 600, dt=0.1)
    snap(page, folder + "02-after-ten-minutes")
    page.evaluate("setPanel(true); setFold('legend', true)")
    snap(page, folder + "03-details-legend")
    details(page, "SCORE[8].info", "about")
    snap(page, folder + "04-happy-visits-about")
    details(page, "SCORE[8].info", "metrics")
    snap(page, folder + "05-happy-visits-metrics")
    details(page, "SCORE[6].info", "metrics")
    snap(page, folder + "06-gap-metrics")
    details(page, "SCORE[0].info", "metrics")
    snap(page, folder + "07-events-metrics")
    details(page, "SCORE[7].info", "actions")
    snap(page, folder + "08-wait-for-food-no-actions")
    page.evaluate("select(null); setPanel(false); for (let i = 0; i < 2; i++) { desEngine.changeCapacity('cooks', -1); desEngine.changeCapacity('waiters', -1); }")
    run(page, 240, dt=0.1)
    snap(page, folder + "09-no-staff-wait-for-food-is-infinite")
    details(page, "SCORE[7].info", "metrics")
    snap(page, folder + "10-wait-for-food-infinite-metrics")
