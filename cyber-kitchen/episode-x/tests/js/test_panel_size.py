"""js/panel-size.js: the divider between the picture and the details can be dragged."""
from tests.conftest import open_page

KEY = "cyber-kitchen.details-width"
WIDTH = "getComputedStyle(document.documentElement).getPropertyValue('--panel-width').trim()"


def drag(page, by, release="pointerup"):
    page.evaluate("""([by, release]) => { const divider = $('panel-divider'); divider.setPointerCapture = () => {};
        const at = x => ({ bubbles: true, clientX: x, pointerId: 1 });
        divider.dispatchEvent(new PointerEvent('pointerdown', at(1000)));
        divider.dispatchEvent(new PointerEvent('pointermove', at(1000 - by / 2)));
        window.midway = [divider.classList.contains('dragging'), document.querySelector('.workspace').classList.contains('resizing'), localStorage.getItem('cyber-kitchen.details-width')];
        divider.dispatchEvent(new PointerEvent(release, at(1000 - by))); }""", [by, release])


def test_the_panel_starts_at_the_standard_width(page):
    assert page.evaluate(WIDTH) == "340px" and page.evaluate("PANEL_WIDTH.standard") == 340


def test_dragging_left_widens_the_panel_and_the_width_is_kept(page):
    page.click("#panel-toggle")
    page.wait_for_timeout(350)
    drag(page, 100)
    assert page.evaluate(WIDTH) == "440px" and page.evaluate(f"localStorage.getItem('{KEY}')") == "440"
    assert page.evaluate("midway") == [True, True, None], "nothing is saved until the divider is let go"
    assert page.evaluate("[$('panel-divider').classList.contains('dragging'), document.querySelector('.workspace').classList.contains('resizing')]") == [False, False]


def test_a_cancelled_drag_also_ends_the_drag(page):
    page.click("#panel-toggle")
    page.wait_for_timeout(350)
    drag(page, -40, release="pointercancel")
    assert page.evaluate(WIDTH) == "300px" and page.evaluate("$('panel-divider').classList.contains('dragging')") is False


def test_moving_or_letting_go_without_a_drag_does_nothing(page):
    page.evaluate("$('panel-divider').dispatchEvent(new PointerEvent('pointermove', { clientX: 5 })); $('panel-divider').dispatchEvent(new PointerEvent('pointerup', { clientX: 5 }))")
    assert page.evaluate(WIDTH) == "340px" and page.evaluate(f"localStorage.getItem('{KEY}')") is None


def test_the_width_stays_between_its_least_and_room_for_the_picture(page):
    assert page.evaluate("[setPanelWidth(10, false), setPanelWidth(5000, false)]") == [260, 1400 - 32 - 320]


def test_double_click_goes_back_to_the_standard_width(page):
    page.evaluate("setPanelWidth(500, true); $('panel-divider').dispatchEvent(new MouseEvent('dblclick'))")
    assert page.evaluate(WIDTH) == "340px" and page.evaluate(f"localStorage.getItem('{KEY}')") == "340"


def test_the_width_survives_collapsing_and_a_reload(page):
    page.evaluate("setPanelWidth(420, true); setPanel(true); setPanel(false); setPanel(true)")
    assert page.evaluate(WIDTH) == "420px"
    page.reload()
    assert page.evaluate(WIDTH) == "420px"


def test_a_narrower_window_narrows_a_panel_that_no_longer_fits(page):
    page.evaluate("setPanelWidth(900, false)")
    page.set_viewport_size({"width": 900, "height": 900})
    page.wait_for_timeout(100)
    assert page.evaluate(WIDTH) == f"{900 - 32 - 320}px"


def test_the_page_works_with_storage_switched_off(browser, site_server):
    page, finish = open_page(browser, site_server[0], init_script="Object.defineProperty(window, 'localStorage', { get() { throw new Error('storage is off'); } });")
    assert page.evaluate(WIDTH) == "340px" and page.evaluate("setPanelWidth(400, true)") == 400
    finish()


def test_a_resize_with_no_width_set_falls_back_to_the_standard_width(page):
    page.evaluate("document.documentElement.style.removeProperty('--panel-width'); window.dispatchEvent(new Event('resize'))")
    assert page.evaluate(WIDTH) == "340px"
