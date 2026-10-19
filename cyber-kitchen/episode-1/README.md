# Semantic Works: Cyber Kitchen — Episode 1 (The Restaurant)

An animated, clickable floor plan of a restaurant, built in one conversation between Pavel and Claude on 11 October 2026. Pavel had been invited to advise a restaurant owner on how the restaurant operates; this page is a first model of what he saw there.

The full conversation, with Pavel's requests as understood, is in [TRANSCRIPT.md](TRANSCRIPT.md). A slide-by-slide account of the journey, with the finished page running live on its second slide, can be [followed online](https://semantic-works.com/public/cyber-kitchen/episode-1/journey/); the file itself is [journey/index.html](journey/index.html). A video of the episode can be [watched on YouTube](https://youtu.be/BYiXYf1y-2I).

## How we started

Pavel set two ground rules before any restaurant talk:

1. **Keep a record.** Every turn of the conversation goes into `TRANSCRIPT.md`, with what Pavel said clearly separated from what Claude answered.
2. **Work on a live page.** Claude starts a local Python web server and a Hello World page; Pavel keeps it open in a browser, and every change Claude makes appears there on its own.

Claude wrote `server.py`, a small web server that watches the `site/` folder and tells the open page to reload when a file changes. To prove the live update worked, Claude replaced Hello World with a pie chart and a table that select each other when clicked. Pavel then asked whether any internet-hosted JavaScript libraries were involved. None were, and that became a standing rule for the project.

## What we built

Pavel described the restaurant from memory: a dozen tables (some round for four, a couple for two, the rest for six), a kitchen, a couple of waiters, paper order tickets that a cook picks up, and a small table where finished plates come out for the waiters.

From that, the page became a live view of the restaurant:

![The restaurant floor 2:30 into service, with table 3 selected and its details panel open](tests/screenshots/05-busy-table-selected.png)

- **Dining room** with twelve numbered tables and a front door. Guests arrive in parties, walk the aisles to a table that fits, read the menu, order, wait, eat and leave. When the room is full they queue at the door, and some are turned away.
- **Two waiters** who take orders, hang the ticket on the order rail, and later carry plates from the pass table to the guests.
- **Kitchen** with two cooks, two stoves, a pizza oven and a coffee machine. Cooks take a ticket off the rail and work through it: stove dishes, then pizza, then coffee.
- **Order tickets** that carry real items from an invented menu and can be followed from the table to the rail, the cook, the pass and back.
- **Table colours** for each stage: yellow reading the menu, orange wanting to order, red waiting for food, green eating.
- **Counters** under the picture, and Pause / 1× / 2× / 4× controls.
- **Selection.** Click any working object and a details panel slides out on the right with an "about" card: what kind of object it is, its purpose, why it is there, and what it is doing right now.
- **Picker.** A magnifying-glass button opens a list of every selectable object by name, grouped by category, with a filter box.

## How we built it

- **One HTML file.** Everything on the page is hand-written SVG, CSS and JavaScript inside `site/index.html`.
- **Standard-library Python.** `server.py` uses only what ships with Python, and pushes reloads over Server-Sent Events.
- **Small steps, checked live.** Pavel spoke each request (most of the conversation was dictated), Claude changed the page, and the open browser showed the result within about a second.
- **Assumptions stated, not hidden.** Pavel did not know how many cooks there were or how long anything takes, so Claude chose: four round four-tops, two two-tops and six six-tops; two cooks; the room layout; the menu; and every timing. **All numbers in the simulation are invented.** The crowding, queues and turned-away parties it shows come from those invented numbers, not from the real restaurant.

## Run it

```bash
make serve
```

Then open http://localhost:8000. The page needs only Python 3 and a browser. It loads nothing from the internet and uses no JavaScript libraries, because it has to run on a corporate laptop that does not allow them.

```bash
make test
```

Runs all tests, both coverage checks and refreshes the UI screenshots. `make help` lists every command.

## What we improved

Pavel's feedback, in the order it came:

- **Colours.** The first status colours were hard to tell apart, and the second attempt still had orange and red too close. The fix was more separated colours and filling the whole table top, not just its outline.
- **Kitchen equipment.** A coffee machine and a pizza oven were added, and the cooks were made to use them.
- **Panel height.** Opening the details panel made the layout jump. The view and the panel now share one fixed height, and the panel only takes width.
- **Wasted space.** A blank strip beside the panel (Claude's layout bug) was removed, and the page now uses the full window width.
- **Clickable tickets.** Tickets became real objects showing what was ordered and how long they have been waiting.
- **Hard-to-click actors.** Because people move, a list of all actors was added to the panel. It was then extended to every object, simplified to plain name buttons with no status or colours, and finally moved out of the panel into the pop-up picker so the panel no longer shifts.

## How we finished

The episode ended with a test suite, at Pavel's request, run from a Makefile at the project root.

| Suite | Tests | Coverage |
|---|---|---|
| Python server (`server.py`) | 20 | 100% (86/86 statements, 20/20 branches) |
| Browser tests of the page's JavaScript and UI | 48 | 100% (751/751 lines) |
| **Total** | **68, all passing when last run** | |

- **Browser tests** drive the real page in headless Chromium through Playwright, with a seeded random generator so the simulation is repeatable.
- **Screenshots.** Each run writes seven PNGs to `tests/screenshots/` (empty restaurant and a fixed busy moment, with the panel closed, open, and with the picker open) so that later changes to the look of the page can be seen.
- **A real bug was found.** The tests showed that asking the server for a missing page crashed the request instead of returning "not found". It is fixed in `server.py`.

Pavel stopped the work before the last loose ends were tied off. These are open:

- **Two screenshots are unreliable.** `06-busy-cook-selected.png` and `07-busy-picker-open.png` came out with slightly different pixels in roughly one run in eight. The cause was not found. No test fails because of it.
- **The readable summary at the end of `make test` is untested.** `tests/summary.py` and the matching changes to `tests/conftest.py` and the Makefile's `test` target were written but never run. The counts in the table above come from runs made before those changes.
- **Screenshots depend on the browser.** Google Chrome and Playwright's Chromium give different pixels, so screenshots should always be generated with the same one.
- **A running server needs a restart** to pick up the missing-page fix.

## Files

| File | What it is |
|---|---|
| `site/index.html` | The whole page: floor plan, simulation, panel and picker |
| `server.py` | The live-reload web server |
| `Makefile` | Commands: `serve`, `test`, `test-py`, `test-js`, `coverage`, `setup`, `clean` |
| `tests/test_server.py` | Python tests for the server |
| `tests/test_page.py` | Browser tests for the page, including the screenshots |
| `tests/conftest.py`, `tests/jscoverage.py` | Test fixtures and the JavaScript coverage measurement |
| `tests/summary.py` | End-of-run summary (untested) |
| `tests/screenshots/` | The seven UI screenshots |
| `requirements-dev.txt` | Test tools only: pytest, coverage, playwright |
| `TRANSCRIPT.md` | The full conversation record |
| `journey/index.html` | The presentation of how the episode was built: one file with its pictures and the finished page inside it |
