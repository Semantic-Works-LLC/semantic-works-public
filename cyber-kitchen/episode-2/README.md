# Semantic Works: Cyber Kitchen — Episode 2 (The Workflow)

Episode 2 takes the animated restaurant floor from [Episode 1](../episode-1/README.md) and adds a second way to look at the same simulation: as work flowing through steps and queues, with a measure and a target for everything on screen. It was built in one conversation between Pavel and Claude on 11 October 2026.

The full conversation, with Pavel's requests as understood, is in [TRANSCRIPT.md](TRANSCRIPT.md). A slide-by-slide account of the journey, with the finished page running live on its second slide, can be [followed online](https://semantic-works.com/public/cyber-kitchen/episode-2/journey/); the file itself is [journey/index.html](journey/index.html).

## How we started

Pavel wanted a second view beside the floor plan: a graph of the flow of work, something he could later use to optimise the restaurant. He did not know how to model it. He could see that some things stand still (tables, stoves) and some move (guests, waiters, food), and asked for a recommendation before any building.

Claude's recommendation was to model the work, not the movement:

- **Flow item:** the thing that gets finished. A party, which becomes an order ticket, which becomes plates of food.
- **Step:** something that happens to the item, or a place where it waits.
- **Resource:** limited capacity a step needs. Tables, waiters, cooks, stoves, the pizza oven and the coffee machine. Waiters and cooks are resources too, even though they move.

Food was kept as a stage of the order, not a separate item, because in this simulation one cook makes a whole order and it goes out together.

## What we built

The page now has a new **service view** beside the restaurant floor; an icon button next to "Show details" switches between the two.

![The service view 2:30 into service, with the order rail selected and its metrics card open](tests/screenshots/10-service-rail-selected-metrics.png)

- **Restaurant floor.** The floor plan from Episode 1, unchanged in how it works.
- **Service view.** Not tied to the room:
  - **Top row:** eight boxes for the states of a party, left to right: at the door, walk in, read menu, wait to order, order, wait for food, eat, leave.
  - **Two queues below:** the order rail (tickets) and the pass (food), drawn as dashed orange boxes.
  - **The kitchen:** a Cook box with a slot for each stove, the pizza oven and the coffee machine.
  - **Staff in motion:** waiters carry tickets down to the rail and food up from the pass; cooks go from the rail to a station to the pass. An order is always with someone or in a queue.
  - **Tables panel:** the twelve tables as coloured squares, in the floor plan's colours.
- **One selection, both views.** Every object on the floor can also be selected in the service view, and the selected object is outlined in cyan in both.
- **About card.** Static text only: what the object is, its purpose, why it is there.
- **Metrics card** under the about card, for every selectable object:
  - its objective and how that is measured;
  - the number so far and a verdict against a target;
  - a chart of its history;
  - a second chart on clock time, showing the last three minutes sliding past a yellow "now" line that sits in the same place for every object.
- **Staffing controls.** Minus and plus buttons in the service view change the number of waiters and cooks, from zero to six of each, while the simulation runs.
- **Faster clock.** 8× and 16× were added to the speed buttons.

## How we built it

- **Small steps, checked live.** Pavel spoke each request, Claude changed the page, and the open browser reloaded by itself.
- **Features first, tests later.** Early on Pavel asked for no new tests and no test runs so the work could move faster. The test suite was built in one go near the end.
- **Modules and a build step.** Until late in the episode all the JavaScript sat inside the HTML file. It was then split into 23 small files and a build step that copies them into the page unchanged, so the page stays one standalone file.
- **Assumptions stated.** All timings in the simulation are invented, as in Episode 1. So are the targets in the metrics, except the 80% limit for kitchen equipment, which is Pavel's. The green and red verdicts say nothing about the real restaurant yet.

## Run it

```bash
make serve
```

Then open http://localhost:8000. The page needs only Python 3 and a browser, loads nothing from the internet and uses no JavaScript libraries. The built page, `site/index.html`, also works opened straight from disk with no server.

```bash
make build
make test
```

`make build` assembles the page from its parts. `make test` builds, runs every test, checks coverage and refreshes the screenshots. `make help` lists every command.

## What we improved

The service view was the fifth attempt. In the order they came:

1. **Flow graph.** Twelve steps in a loop with a resources panel. Pavel did not like how it looked.
2. **Status board.** Tables, kitchen, and people and equipment as three sections of cards. Liked at first, then given arrows and gliding cards, then found hard to read.
3. **Workflow, left to right.** One row of boxes with lanes for guests, orders, waiters and cooks. "Much better", but it showed the pass as a state of the table, and the cook never visibly put food on it.
4. **The same with queues drawn differently** and the cook walking food to the pass.
5. **Service view.** Pavel's own idea: party states as the foundation, the two queues modelled explicitly, staff moving between them. The other views were then deleted.

Other feedback along the way:

- **Selection highlight.** It was lost by mistake when the extra views were removed. It came back in cyan, a colour used for nothing else.
- **Selectable everywhere.** Stoves and the coffee machine could not be selected in the service view at first; now every floor object can.
- **One legend.** Both views show the same legend and use the same colours.
- **Kitchen scenery.** Prep counter, sink and fridge are no longer selectable; they are only drawn on the floor plan.
- **Clock-time charts.** The first metrics charts were ordered by party, not by time. A second chart on absolute time was added under each.
- **Unrequested changes.** Pavel pointed out that Claude had made changes he did not ask for. From then on Claude made only the requested change and listed anything else as a suggestion.
- **Unused text.** The "what it is doing right now" descriptions, no longer shown anywhere, were removed.

## How we finished

| Suite | Tests | Coverage |
|---|---|---|
| Python server (`tests/test_server.py`) | 20 | 100% of `server.py` |
| Browser tests of the page (`tests/js/`, `tests/test_page.py`) | 191 | 100% of the lines in every one of the 23 modules |
| **Total** | **211, all passing when last run** | |

- **One test file per module.** `tests/js/test_staff.py` tests `js/staff.js`, and so on. A test fails if a module has no test file.
- **Page-level tests** in `tests/test_page.py` cover the build (every module inlined unchanged and in order), opening the built page from disk, layout, live reload and the screenshots.
- **Coverage is reported per module** at the end of the run and in `coverage/js-coverage.html`.
- **Eleven screenshots** in `tests/screenshots/`: seven of the restaurant floor and four of the service view.

These are open:

- **Screenshots are unstable.** From run to run a few dozen edge pixels can differ although the page is identical, so a "changed" screenshot is a prompt to look, not a failure. The cause was not found.
- **Looks are not asserted.** Colours, spacing and whether a chart reads well are checked only by eye and by the screenshots.
- **`build.py` has no tests of its own.** The page-level tests check its output.
- **Leftovers in the code.** Four live lines that nothing shows, each station's unused verb and remembered table, and two sentences that still assume exactly two cooks.
- **Paying is not simulated.** Guests finish eating and leave.
- **Not a discrete-event simulation.** The clock moves in small fixed steps and every person is updated on each one.

## Files

| Path | What it is |
|---|---|
| `js/` | The page's JavaScript, as 23 small files, one per area (staff, guests, metrics, charts and so on) |
| `js/modules.txt` | The order in which those files go into the page |
| `index.template.html` | The page's HTML and CSS, with a marker where the JavaScript goes |
| `build.py` | Copies the files from `js/` into the template, unchanged, and writes `site/index.html` |
| `site/index.html` | The finished page: one standalone file. Generated; do not edit |
| `server.py` | The live-reload web server from Episode 1 |
| `Makefile` | Commands: `build`, `serve`, `test`, `test-py`, `test-js`, `coverage`, `setup`, `clean` |
| `tests/js/` | Browser tests, one file per module |
| `tests/test_page.py` | Page-level browser tests, including the screenshots |
| `tests/test_server.py` | Python tests for the server |
| `tests/support.py`, `tests/conftest.py`, `tests/jscoverage.py`, `tests/summary.py` | Test helpers, fixtures, the JavaScript coverage measurement and the end-of-run summary |
| `tests/screenshots/` | The eleven UI screenshots |
| `requirements-dev.txt` | Test tools only: pytest, coverage, playwright |
| `TRANSCRIPT.md` | The full conversation record |
| `journey/index.html` | The presentation of how the episode was built: one file with its pictures and the finished page inside it |
