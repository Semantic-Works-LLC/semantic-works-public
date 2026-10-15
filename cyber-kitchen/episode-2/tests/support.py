"""Helpers shared by the browser tests.

The `page` fixture loads the app with a seeded random generator and a frozen animation loop,
so a test advances the simulation itself by calling the page's own tick() and draw().
"""


def run(page, seconds, dt=0.05):
    """Advance the simulation by this many simulated seconds, then redraw."""
    page.evaluate("([n, dt]) => { for (let i = 0; i < n; i++) tick(dt); draw(); }", [round(seconds / dt), dt])


def run_until(page, condition, limit=900):
    """Advance until the JavaScript condition holds; fail if it never does."""
    reached = page.evaluate(
        f"() => {{ let n = 0; while (!({condition}) && n++ < {limit * 20}) tick(0.05); draw(); return !!({condition}); }}")
    assert reached, f"never reached: {condition}"


def click(page, expression):
    """Click an SVG or HTML element given as a JavaScript expression."""
    page.evaluate(f"({expression}).dispatchEvent(new MouseEvent('click', {{ bubbles: true }}))")


def card(page):
    """The about card as a dict, or None when nothing is selected."""
    return page.evaluate("""() => {
        const about = document.querySelector('#about .about');
        if (!about) return null;
        const rows = [...about.querySelectorAll('dt')].map(dt => [dt.textContent, dt.nextElementSibling.textContent]);
        return { kind: about.querySelector('.kind').textContent, name: about.querySelector('h3').textContent,
                 ...Object.fromEntries(rows) };
    }""")


def metrics(page):
    """The metrics card as a dict, or None when it is not shown."""
    return page.evaluate("""() => {
        const card = document.querySelector('#metrics .metrics');
        if (!card) return null;
        const lists = [...card.querySelectorAll('dl')], head = card.querySelector('.metric-value');
        const pairs = dl => Object.fromEntries([...dl.querySelectorAll('dt')].map(dt => [dt.textContent, dt.nextElementSibling.textContent]));
        return { ...pairs(lists[0]), value: head.querySelector('b').textContent, unit: head.querySelector('span').textContent,
                 verdict: head.querySelector('.verdict').textContent, grade: head.querySelector('.verdict').className.replace('verdict ', ''),
                 notes: [...card.querySelectorAll('.metric-note')].map(p => p.textContent),
                 charts: card.querySelectorAll('svg.chart').length, numbers: lists[1] ? pairs(lists[1]) : {} };
    }""")


def spec(page, info):
    """What metricsFor() says about an object, without the chart elements."""
    return page.evaluate(f"""() => {{
        const spec = metricsFor({info});
        return {{ ...spec, chart: spec.chart.tagName, timeline: spec.timeline.tagName }};
    }}""")


def picker_groups(page):
    """Visible picker groups as {heading: [visible button names]}."""
    return page.evaluate("""() => Object.fromEntries([...document.querySelectorAll('#picker details')]
        .filter(group => !group.hidden)
        .map(group => [group.firstChild.textContent,
                       [...group.querySelectorAll('.actor')].filter(b => !b.hidden).map(b => b.textContent)]))""")


def seat_everyone(page, count=12):
    """Fill the room: spawn parties until `count` tables are taken."""
    page.evaluate(f"() => {{ let n = 0; while (tables.filter(t => t.status !== 'free').length < {count} && n++ < 500) spawnParty(); }}")


def show_service(page):
    """Switch to the service view and draw it once."""
    page.click("#view-toggle")
    page.evaluate("draw()")


def settle(page):
    """Let every token in the service view finish gliding to its place."""
    page.evaluate("() => { for (let i = 0; i < 60; i++) { loopLast = performance.now() - 100; draw(); } }")


def fixed_random(page, value, script):
    """Run a script in the page with Math.random() pinned to one value."""
    return page.evaluate(f"() => {{ const real = Math.random; Math.random = () => {value}; try {{ return (() => {{ {script} }})(); }} finally {{ Math.random = real; }} }}")
