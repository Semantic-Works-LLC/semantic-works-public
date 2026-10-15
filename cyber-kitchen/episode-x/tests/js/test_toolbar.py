"""js/toolbar.js: the speed menu and the zoom."""
import pytest

from tests.support import run, settle, show


def view_box(page, node="desview"):
    return [round(float(v), 1) for v in page.evaluate(f"$('{node}').getAttribute('viewBox')").split()]


def wheel(page, delta, at=(0.5, 0.5), node="desview", ctrl=False):
    return page.evaluate("""([node, delta, fx, fy, ctrl]) => { const svg = $(node), box = svg.getBoundingClientRect(), x = box.left + box.width * fx, y = box.top + box.height * fy;
        const under = () => { const p = new DOMPoint(x, y).matrixTransform(svg.getScreenCTM().inverse()); return [p.x, p.y]; };
        const before = under(), event = new WheelEvent('wheel', { deltaY: delta, clientX: x, clientY: y, ctrlKey: ctrl, bubbles: true, cancelable: true });
        svg.dispatchEvent(event); return { before, after: under(), prevented: event.defaultPrevented }; }""", [node, delta, at[0], at[1], ctrl])


# ---------- speed ----------

def test_the_speed_menu_offers_five_speeds_and_starts_at_one(page):
    assert page.evaluate("[SPEEDS, speed, $('speed-label').textContent, $('speed-menu').hidden]") == [[1, 2, 4, 8, 16], 1, "1×", True]
    page.click("#speed-toggle")
    assert page.evaluate("[...$('speed-menu').children].map(item => item.textContent + item.getAttribute('aria-checked'))") == ["1×true", "2×false", "4×false", "8×false", "16×false"]


def test_choosing_a_speed_sets_it_and_closes_the_menu(page):
    page.click("#speed-toggle")
    page.click("#speed-menu [data-speed='8']")
    assert page.evaluate("[speed, $('speed-label').textContent, $('speed-menu').hidden, $('speed-toggle').title, $('speed-toggle').getAttribute('aria-expanded')]") == [8, "8×", True, "Speed: 8×. Choose a speed", "false"]


def test_only_one_menu_is_open_at_a_time(page):
    page.click("#speed-toggle")
    page.click("#picker-toggle")
    assert page.evaluate("[$('speed-menu').hidden, $('picker').hidden, $('view-menu').hidden]") == [True, False, True]
    page.click("#view-toggle")
    assert page.evaluate("[$('speed-menu').hidden, $('picker').hidden, $('view-menu').hidden]") == [True, True, False]
    page.click("#speed-toggle")
    assert page.evaluate("[$('speed-menu').hidden, $('picker').hidden, $('view-menu').hidden]") == [False, True, True]
    page.click("#speed-toggle")
    assert page.evaluate("$('speed-menu').hidden")


# ---------- the whole picture ----------

def test_the_whole_picture_is_what_is_drawn_with_a_small_margin(page):
    drawn = page.evaluate("(() => { const b = $('desview').getBBox(); return [b.x, b.y, b.width, b.height]; })()")
    box = view_box(page)
    assert box[0] == pytest.approx(max(0, drawn[0] - 12), abs=0.1) and box[2] == pytest.approx(drawn[2] + 24, abs=12.1)
    assert box[2] < 1200, "narrower than the frame the view was designed in: the room fills the space"
    assert page.evaluate("$('desview').dataset.frame") == "0 44 1200 644"


def test_a_view_that_is_not_on_screen_yet_uses_its_designed_frame(page):
    state = page.evaluate("(() => { view = 'score'; const s = zoomState(); view = 'des'; return [s.x, s.y, s.w, s.h, $('scoreview').dataset.whole ?? null]; })()")
    assert state == [0, 0, 1200, 644, None]


def test_refit_measures_again(page):
    before = view_box(page)
    page.evaluate("el('rect', { x: 0, y: 44, width: 1200, height: 10, fill: 'none' }, $('des-static')); zoomBy(2); refitView()")
    assert view_box(page)[2] > before[2] and page.evaluate("zoomState().zoom.k") == 1


# ---------- the buttons ----------

def test_at_the_whole_picture_only_zooming_in_is_possible(page):
    assert page.evaluate("['zoom-in', 'zoom-out', 'zoom-fit'].map(id => $(id).disabled)") == [False, True, True]


def test_plus_zooms_in_about_the_middle_gliding_there(page):
    whole = view_box(page)
    page.click("#zoom-in")
    assert view_box(page) == whole, "nothing moves until a frame is drawn"
    page.evaluate("__runFrames(100)")
    part = view_box(page)[2]
    assert whole[2] / 1.5 < part < whole[2], "part of the way there"
    settle(page, 1)
    zoomed = view_box(page)
    assert zoomed[2] == pytest.approx(whole[2] / 1.5, abs=0.2) and zoomed[0] + zoomed[2] / 2 == pytest.approx(whole[0] + whole[2] / 2, abs=0.2)
    assert page.evaluate("[$('desview').classList.contains('zoomed'), $('zoom-out').disabled, $('zoom-fit').disabled]") == [True, False, False]


def test_minus_zooms_out_and_stops_at_the_whole_picture(page):
    whole = view_box(page)
    page.evaluate("zoomBy(1.5); zoomBy(1 / 1.5)")
    settle(page, 1)
    assert view_box(page) == whole and page.evaluate("zoomState().zoom.k") == 1
    page.evaluate("zoomBy(0.2)")
    assert page.evaluate("zoomState().zoom.k") == 1


def test_zoom_stops_at_eight_times(page):
    page.evaluate("for (let i = 0; i < 10; i++) zoomBy(1.5)")
    assert page.evaluate("[zoomState().zoom.k, $('zoom-in').disabled]") == [8, True]


def test_fit_shows_the_whole_picture_again(page):
    whole = view_box(page)
    page.evaluate("zoomBy(3)")
    settle(page, 1)
    page.click("#zoom-fit")
    settle(page, 1)
    assert view_box(page) == whole


def test_a_glide_is_dropped_when_the_view_changes_meanwhile(page):
    page.click("#zoom-in")
    before = view_box(page)
    page.evaluate("view = 'graph'; __runFrames(100); view = 'des'")
    assert view_box(page) == before


# ---------- dragging and the trackpad ----------

def test_dragging_a_zoomed_picture_moves_it_and_does_not_count_as_a_click(page):
    page.evaluate("zoomBy(2)")
    settle(page, 1)
    before = view_box(page)
    moved = page.evaluate("""() => { const svg = $('desview'), at = (x, y) => ({ bubbles: true, clientX: x, clientY: y, button: 0 }); let clicks = 0;
        svg.addEventListener('click', () => clicks++);
        svg.dispatchEvent(new PointerEvent('pointerdown', at(600, 400)));
        window.dispatchEvent(new PointerEvent('pointermove', at(602, 400)));          // too small to be a drag yet
        const still = svg.getAttribute('viewBox');
        window.dispatchEvent(new PointerEvent('pointermove', at(500, 350)));
        window.dispatchEvent(new PointerEvent('pointerup', at(500, 350)));
        svg.dispatchEvent(new MouseEvent('click', { bubbles: true }));
        return { still, clicks }; }""")
    after = view_box(page)
    assert [round(float(v), 1) for v in moved["still"].split()] == before
    assert after[0] > before[0] and after[1] > before[1] and after[2:] == before[2:], "dragged left and up: the picture shows what was to the right and below"
    assert moved["clicks"] == 0
    page.wait_for_timeout(20)
    page.evaluate("$('desview').dispatchEvent(new MouseEvent('click', { bubbles: true }))")


def test_a_click_without_a_drag_still_counts(page):
    page.evaluate("zoomBy(2)")
    assert page.evaluate("""() => { const svg = $('desview'); let clicks = 0; svg.addEventListener('click', () => clicks++);
        svg.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, clientX: 600, clientY: 400, button: 0 }));
        window.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, clientX: 600, clientY: 400 }));
        svg.dispatchEvent(new MouseEvent('click', { bubbles: true })); return clicks; }""") == 1


def test_the_whole_picture_cannot_be_dragged_and_moving_without_a_drag_does_nothing(page):
    before = view_box(page)
    page.evaluate("""() => { $('desview').dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, clientX: 600, clientY: 400, button: 0 }));
        window.dispatchEvent(new PointerEvent('pointermove', { clientX: 300, clientY: 200 })); window.dispatchEvent(new PointerEvent('pointerup', {})); }""")
    assert view_box(page) == before


def test_the_picture_never_shows_past_its_edge(page):
    page.evaluate("zoomBy(2); const z = zoomState().zoom; z.cx = -5000; z.cy = 99999; applyZoom()")
    box, whole = view_box(page), page.evaluate("$('desview').dataset.whole.split(' ').map(Number)")
    assert box[0] == pytest.approx(whole[0], abs=0.1) and box[1] + box[3] == pytest.approx(whole[1] + whole[3], abs=0.1)


def test_two_fingers_up_zooms_in_about_the_pointer(page):
    result = wheel(page, -120, at=(0.7, 0.3))
    assert result["prevented"] and page.evaluate("zoomState().zoom.k") == pytest.approx(2.718 ** 0.36, rel=0.01)
    assert result["after"] == pytest.approx(result["before"], abs=0.5), "what is under the pointer stays under it"


def test_two_fingers_down_zooms_out_to_the_whole_picture_and_no_further(page):
    whole = view_box(page)
    wheel(page, -300)
    wheel(page, 5000)
    assert page.evaluate("zoomState().zoom.k") == 1 and view_box(page) == whole and page.evaluate("$('zoom-fit').disabled")


def test_a_pinch_zooms_faster_and_stops_at_eight_times(page):
    wheel(page, -30, ctrl=True)
    assert page.evaluate("zoomState().zoom.k") == pytest.approx(2.718 ** 0.3, rel=0.01)
    wheel(page, -5000)
    assert page.evaluate("zoomState().zoom.k") == 8


def test_zoom_works_the_same_on_every_view(page):
    for view, node in [("graph", "desgraph"), ("score", "scoreview")]:
        show(page, view)
        whole = view_box(page, node)
        wheel(page, -200, node=node)
        assert view_box(page, node)[2] < whole[2], view


def test_the_minus_and_fit_buttons(page):
    page.evaluate("zoomBy(1.5 * 1.5)")
    settle(page, 1)
    page.click("#zoom-out")
    settle(page, 1)
    assert page.evaluate("zoomState().zoom.k") == pytest.approx(1.5)
