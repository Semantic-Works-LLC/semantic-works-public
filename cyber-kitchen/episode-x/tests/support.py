"""Helpers shared by the browser tests.

The `page` fixture loads the app with a frozen animation loop and a stopwatch that only moves when a
test moves it, so a test advances the simulation itself by calling the page's own tick() and draw().
The simulation is seeded, so the same steps always give the same restaurant.
"""

VIEWS = {"des": "Floor Plan", "graph": "Process Map", "score": "Scorecard"}


def run(page, seconds, dt=0.05):
    """Advance the simulation by this many simulated seconds, then redraw and let the picture settle."""
    page.evaluate("([n, dt]) => { for (let i = 0; i < n; i++) tick(dt); }", [round(seconds / dt), dt])
    settle(page)


def run_until(page, condition, limit=1800):
    """Advance until the JavaScript condition holds; fail if it never does."""
    reached = page.evaluate(
        f"() => {{ let n = 0; while (!({condition}) && n++ < {limit * 20}) tick(0.05); return !!({condition}); }}")
    assert reached, f"never reached: {condition}"
    settle(page)


def settle(page, frames=360):
    """Draw this many frames a sixtieth of a second apart, so every token finishes its way."""
    # The map measures its card a moment after the card changes size, on a real timer. Measuring here as
    # well means the layout never depends on whether that timer has fired yet.
    page.evaluate("n => { graphMeasure(); for (let i = 0; i < n; i++) { __advance(16.7); draw(); } while (__runFrames(400)) {} draw(); }", frames)


def show(page, view):
    """Switch to a view ("des", "graph" or "score") and draw it."""
    page.evaluate(f"setView('{view}')")
    settle(page, 2)


def click(page, expression):
    """Click an SVG or HTML element given as a JavaScript expression."""
    page.evaluate(f"({expression}).dispatchEvent(new MouseEvent('click', {{ bubbles: true }}))")


def right_click(page, expression):
    """Right-click an element; returns the labels of the menu that opened (empty when none did)."""
    return page.evaluate(f"""() => {{
        ({expression}).dispatchEvent(new MouseEvent('contextmenu', {{ bubbles: true, cancelable: true, clientX: 300, clientY: 300 }}));
        const menu = document.getElementById('graph-menu');
        return menu.hidden ? [] : [...menu.children].map(item => item.textContent);
    }}""")


def menu_pick(page, label):
    """Choose an item of the open right-click menu by the start of its label."""
    page.evaluate("label => [...document.getElementById('graph-menu').children].find(item => item.textContent.startsWith(label)).click()", label)


def about(page):
    """The About tab as {label: text}, with the selected object's name under "name"; None when nothing is selected."""
    return page.evaluate("""() => {
        if (!selected) return null;
        const rows = [...document.querySelectorAll('#about dt')].map(dt => [dt.textContent, dt.nextElementSibling.textContent]);
        return { name: document.querySelector('#selected-head h3').textContent, ...Object.fromEntries(rows) };
    }""")


def metrics(page):
    """The Metrics tab as a dict (after switching to it), or None when nothing is selected."""
    return page.evaluate("""() => {
        if (!selected) return null;
        setPanel(true); setFold('selection', true); setTab('metrics'); renderMetrics();
        const card = document.querySelector('#metrics .metrics'), head = card.querySelector('.metric-value'), list = card.querySelector('dl');
        return { headings: [...card.querySelectorAll('h4')].map(h => h.textContent),
                 measure: card.querySelector('.measure')?.textContent ?? null,
                 value: head.querySelector('b').textContent, unit: head.querySelector('span').textContent,
                 verdict: head.querySelector('.verdict').textContent, grade: head.querySelector('.verdict').className.replace('verdict ', ''),
                 notes: [...card.querySelectorAll('.metric-note')].map(p => p.textContent),
                 charts: card.querySelectorAll('svg.chart').length,
                 numbers: list ? Object.fromEntries([...list.querySelectorAll('dt')].map(dt => [dt.textContent, dt.nextElementSibling.textContent])) : {} };
    }""")


def spec(page, info):
    """What metricsFor() says about an object, without the chart elements."""
    return page.evaluate(f"""() => {{
        const spec = metricsFor({info});
        return {{ ...spec, chart: spec.chart.tagName, timeline: spec.timeline.tagName,
                  chartMarks: spec.chart.querySelectorAll('rect').length, timelineMarks: spec.timeline.querySelectorAll('rect').length }};
    }}""")


def actions(page):
    """The Actions tab as {button label: enabled?}, in order."""
    return page.evaluate("""() => {
        setPanel(true); setFold('selection', true); setTab('actions'); renderActions();
        return Object.fromEntries([...document.querySelectorAll('#actions button')].map(b => [b.textContent, !b.disabled]));
    }""")


def press(page, key):
    """Press an Actions tab button by its key: pin, unpin, out or back."""
    page.evaluate(f"document.querySelector('#actions [data-action={key}]').click()")
    settle(page, 4)


def legend(page):
    """The Legend section as a list: headings and intros as strings, entries as "- text"."""
    return page.evaluate("""() => [...document.querySelector('#legend > div').children].flatMap(node =>
        node.tagName === 'UL' ? [...node.children].map(item => '- ' + item.children[1].textContent) : [node.textContent])""")


def picker_groups(page):
    """Visible picker groups as {heading: [visible button names]}."""
    return page.evaluate("""() => Object.fromEntries([...document.querySelectorAll('#picker details')]
        .filter(group => !group.hidden)
        .map(group => [group.firstChild.textContent,
                       [...group.querySelectorAll('.actor')].filter(b => !b.hidden).map(b => b.textContent)]))""")


def resources(page):
    """The engine's resources as {id: {capacity, allocated, units}}; a unit is "free", "busy", "out" or "off"."""
    return page.evaluate("""() => Object.fromEntries(Object.entries(desEngine.snapshot().resources).map(([id, r]) => [id, {
        capacity: r.capacity, allocated: r.allocated,
        units: r.units.map(unit => unit === false ? 'off' : unit === DES_OUT ? 'out' : unit ? 'busy' : 'free') }]))""")


def counts(page):
    """The engine's running totals."""
    return page.evaluate("""() => { const s = desEngine.snapshot(); return { arrived: s.arrived, departed: s.departed, balked: s.balked,
        happy: s.happy, abandoned: s.abandoned, order: s.abandonedFor.order, food: s.abandonedFor.food, inside: s.parties.size, events: s.eventsProcessed }; }""")


def strays(page):
    """Process Map tokens that are neither inside a shown box nor on their way: there should be none."""
    return page.evaluate("""() => [...graphTokens].filter(([, token]) => !(token.route || []).length && !Object.values(GRAPH).some(box =>
        (!graphShown || graphShown.has(box.key)) && token.x >= box.x + box.dx - 3 && token.x <= box.right + box.dx + 3
        && token.y >= box.y + box.dy - 3 && token.y <= box.bottom + box.dy + 3)).map(([key]) => key)""")
