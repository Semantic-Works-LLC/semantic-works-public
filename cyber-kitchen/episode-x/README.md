# Semantic Works: Cyber Kitchen — Episode X (500 Million Tokens to Cook One Process Map)

Episode 2 found a way to model the operations of a restaurant, but only on the fifth try, and it was still a picture of one restaurant. Episode X rebuilds the same restaurant on a formal method, discrete-event simulation (DES), and finishes with three views drawn from one engine, a measure and a target for everything, and a full test suite. It was built in one long conversation between Pavel and Claude on 13 October 2026.

The full conversation, with Pavel's requests as understood, is in [TRANSCRIPT.md](TRANSCRIPT.md). A slide-by-slide account of the journey, with the finished page running live inside it, is [journey/index.html](journey/index.html). The restaurant was first built in [Episode 1](../episode-1/README.md), and the five versions this episode began from are in [Episode 2](../episode-2/README.md).

## How we started

Pavel asked Gemini which formal method fits the modelling of a restaurant's operations. The first answers were correct and abstract. The useful one came when he asked how specific projects actually model a restaurant with DES. Their decisions, in plain words:

- **The entity is the party,** not each guest.
- **The order is a second entity:** the party stays at its table while the order travels through the kitchen.
- **Tables, waiters, cooks and equipment are pools** of units.
- **A dish needs two things at once:** a cook and a stove.
- **Waiting is kept apart from doing.**
- **Nothing depends on where things are drawn.**

## What we built

![The Process Map with one party selected: the side panel shows its metrics, its waits against their targets and its visit on the clock](tests/screenshots/process-map/11-one-party-selected-about.png)

- **One engine.** A seeded discrete-event simulation with a clock, a queue of events, pools of resources and queues. Any speed gives the same sequence of events.
- **Three views of it,** chosen with the blue button at the top:
  - **Floor Plan:** the room and the kitchen, and who is where. Nothing else.
  - **Process Map:** three sections. Actors and resources along the top, each a box of squares, one per unit: hollow when free, crossed when in use, a red diagonal when out of service. Tasks in the middle, left to right, each with a dashed waiting area on its left. Outcomes along the bottom, red or green.
  - **Scorecard:** nine figures for the whole restaurant, from events and arrivals to happy visits, each coloured by whether it meets its target, with Little's Law explained in a footnote.
- **Select and inspect anything,** in any view or by name. The same object is selected in every view.
- **Pin anything** on the Process Map, a task, a resource, one cook, one table, one party or all of them, to see only what it takes part in.
- **A side panel** that follows the selection, with three tabs:
  - **About:** what the object is and what it is for.
  - **Metrics:** how it is measured, two charts, its target and a verdict.
  - **Actions:** only what can be done to it: pin or unpin, call a cook or waiter in sick, break or fix equipment, close or open a table. The same actions are on the right-click menu.
- **Zoom** with the buttons or two fingers on a trackpad; speeds up to 16×; waiters and cooks can be added or taken away while it runs.
- **The page remembers how it was left:** view, speed, pause, panel, open sections and tab.

## How we built it

The build had five phases, with many turns back and forth inside each:

1. **Get the DES model to work.** Three attempts were not kept: tasks in lanes, a flowchart, and a view of stations that had good ideas but was too busy to follow. The fourth, a pipeline of tasks and queues, was functionally correct.
2. **Polish it into a clean interface.** Actors and outcomes were introduced, and queues were folded into the tasks. Each of these borrowed an idea from a rejected attempt.
3. **Make it intuitive to explore.** Select and inspect any element, zoom in and out, pin any one element to focus on it, a side panel that explains each element with its objectives and metrics, and actions attached to specific elements.
4. **Separate two kinds of metrics.** The observability of each task and resource stays next to the object it measures; the business metrics that cut across them are pulled out into the Scorecard.
5. **Build the full test suite,** with screenshots.

All timings and targets in the simulation are invented. The verdicts say nothing about a real restaurant yet.

## Run it

```bash
make serve
```

Then open http://localhost:8000. The page needs only Python 3 and a browser, loads nothing from the internet and uses no JavaScript libraries. The built page, `site/index.html`, also works opened straight from disk with no server.

```bash
make build
make test
make screenshots
```

`make build` assembles the page from its parts. `make test` builds, runs every test, checks both coverage figures and compares the page against the reference screenshots. `make screenshots` accepts a changed look by replacing the reference screenshots. `make help` lists every command.

## How we finished

| Suite | Tests | Coverage |
|---|---|---|
| Python server (`tests/test_server.py`) | 20 | 100% of `server.py` |
| Browser tests of the page | 469 | 100% of the 2,443 lines of JavaScript |
| **Total** | **489, all passing when last run** | |

- **One test file per module.** `tests/js/test_des_graph.py` tests `js/des-graph.js`, and so on, plus `tests/js/test_des_graph_pin.py` for pinning.
- **Requirement tests** in `tests/test_requirements.py` are named after what Pavel asked for and quote his words, for example `test_the_right_click_menu_is_only_about_this_object`.
- **Time is frozen** in the browser, so every run is the same.
- **Sixty reference screenshots** in `tests/screenshots/`, one folder per view (`floor-plan/`, `process-map/`, `process-map/pinned/`, `scorecard/`). Each run compares the page against them, allowing for a few pixels of antialiasing noise; a changed picture fails the run and is written to `coverage/screenshots/` for comparison.

These are open:

- **The verdicts mean nothing yet.** Every timing and every target is invented.
- **Paying is not simulated.** Guests finish eating and leave.
- **One restaurant.** Twelve tables and one kitchen are written into the page.
- **Looks are checked only against pictures.** A reference screenshot says the page has not changed, not that it reads well.
- **The business metrics are a beginning.** Episode 3 will build them out toward the owner's actual objectives.

## Files

| Path | What it is |
|---|---|
| `js/` | The page's JavaScript, as 23 small files: the engine (`des-engine.js`), the three views (`des-view.js`, `des-graph.js`, `scorecard.js`), the cards (`des-info.js`), selection, actions, metrics, charts and so on |
| `js/modules.txt` | The order in which those files go into the page |
| `index.template.html` | The page's HTML and CSS, with a marker where the JavaScript goes |
| `build.py` | Copies the files from `js/` into the template, unchanged, and writes `site/index.html` |
| `site/index.html` | The finished page: one standalone file. Generated; do not edit |
| `server.py` | The live-reload web server from Episode 1 |
| `Makefile` | Commands: `build`, `serve`, `test`, `test-py`, `test-js`, `screenshots`, `coverage`, `setup`, `clean` |
| `tests/js/` | Browser tests, one file per module |
| `tests/test_requirements.py` | Tests named after Pavel's requests, quoting him |
| `tests/test_page.py` | Page-level browser tests: the build, layout, live reload |
| `tests/test_screenshots.py` | Takes the screenshots of every view and compares them with the references |
| `tests/test_server.py` | Python tests for the server |
| `tests/support.py`, `tests/conftest.py` and the other helpers | Test helpers, fixtures, the frozen clock, the JavaScript coverage measurement and the end-of-run summary |
| `tests/screenshots/` | The sixty reference screenshots, one folder per view |
| `requirements-dev.txt` | Test tools only: pytest, coverage, playwright |
| `TRANSCRIPT.md` | The full conversation record, with times |
| `journey/index.html` | The presentation of how the episode was built: one file with its pictures and the finished page inside it |
| `journey/images/` | The pictures used in the journey, as separate files |
