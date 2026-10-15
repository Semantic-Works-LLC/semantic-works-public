# Semantic Works: Tea Time Planner — Episode 1 (The Afternoon Tea)

A planning app for a British afternoon tea for seven, built in one conversation between Pavel and Claude in October 2026, in about an hour and a half. Pavel and Olga planned a real tea party out loud, and every decision they made became part of the page: a 3D table that turns by itself, a plate of finger sandwiches with recipe cards, a drinks table with rising steam and bubbles, and a day-by-day plan with a shopping list by store.

The conversation that built the app, with Pavel's requests as understood, is in [TRANSCRIPT.md](TRANSCRIPT.md). A slide-by-slide account of the journey can be [followed online](https://semantic-works.com/public/tea-time-planner/episode-1/journey/); the file itself is [journey/index.html](journey/index.html). A selection of how the app looked as it grew, 14 of the 115 screenshots taken during the session, on the same clock as the transcript, is in [screenshots/timeline.md](screenshots/timeline.md).

## How we started

Pavel and Olga were hosting an afternoon tea for seven, and Olga would be doing the cooking. Pavel asked Claude to start a local server with a page saying "Hello, World!" and "Hello, Olga!", and to push every change to that page while he watched. Then he began describing the party, and asked Claude to draw the table with everything they discussed.

There was no specification and no mockup. The app grew one spoken request at a time, while the decisions about food, tableware and timing were still being made.

## What we built

![The 3D tea table at the end of the session: seven guests on curved chairs, two three-tier stands, two glass teapots, bouquets and floating candles, with the side panel open on how to set each place](screenshots/113-table.jpg)

One page with four views, switched with the gold button in the header. Each view has its own side panel of sections that open and close; the panel button hides it, and its divider resizes it.

- **Table.** A 3D British tea table that turns slowly by itself, never dipping below the table.
  - Seven guests on curved, table-height chairs, each place set British-style: tea plate with napkin, fork left, dessert knife right, cup and saucer above.
  - Down the middle: two tall three-tier stands (sandwiches, scones, sweets), two glass teapots, jam and clotted cream, two bouquets and floating candles with pearls.
  - Drag to turn, scroll to zoom; camera presets (Angle, Top, Seated), a switch to hide the guests, and a flat Plan drawing.
  - In the panel: seating, a flip card showing how to set each place, what goes on the table, and a little etiquette.
- **Food.** A 3D plate of 15 finger sandwiches of five kinds: smoked salmon, egg and salmon, shrimp and crab, roast beef with horseradish cream, and chicken Waldorf.
  - In the panel, a card for each sandwich that flips from its picture to a short recipe with its garnish.
  - Which bread to buy, timing against soggy bread, how to cut fingers, and where in Tampa to find scones and clotted cream.
- **Drinks.** A 3D side table with the two teapots giving off steam, red and white wine, a Coke, champagne in an ice bucket and flutes with rising bubbles.
- **Plan.** A day-before and party-day checklist for a 6:30 PM start, with ticks.
  - Every step is tagged *Olga · main cook*, *Pasha · helper* or *Both*, with filters for Everyone, Olga, Pasha and Together.
  - The shopping list by store (Amazon, Publix, Whole Foods, Sam's Club, Walmart), with tickboxes; music and small gift ideas.
- **Memory.** The page keeps its state across reloads in the browser: ticks, open sections, panel width, filter, flipped cards, and each 3D camera's angle and spin. A live update lands without the viewer noticing.
- **A record of its own making.** A few seconds after each change, the server photographs every view in a hidden browser and keeps the ones that changed, numbered and timed: 115 screenshots in all.

## How we built it

- **By voice, live.** Pavel spoke each request while watching the page, often thinking aloud with Olga. The page reloaded itself within a second of every change.
- **Planning and building at once.** Many requests were questions about the party itself (what spread goes with roast beef, where to buy clotted cream in Tampa, which bread to use), and each answer was added to the page as a decision, a recipe or a shopping item.
- **One page, plain files.** HTML, CSS and JavaScript in one page, with the three 3D scenes in one script using three.js, which is built into the page; a small Python server for live reload and the screenshots.
- **Features first, no tests.** Nothing here has automated tests.

## Run it

You need Python 3 and a web browser. The screenshots also need Google Chrome, installed in the usual place on a Mac.

```bash
python3 server.py
```

Then open http://localhost:8000. The page reloads by itself whenever `index.html` or `scenes3d.js` changes, and a few seconds later the server saves new screenshots of the views that changed. The page is fully self-contained: three.js is built into it, so it loads nothing from the internet and works offline.

## What we improved

- **The table, three times.** It started as an oval, became a rectangle with two seats at one head, and settled at three on each long side and one at the head.
- **The 3D table crashed on its first showing.** The code used a shape that this version of three.js doesn't have, so the drawing stopped halfway. It was fixed within minutes with simpler shapes.
- **The header buttons stopped responding** in Pavel's window, though they worked in Claude's own tests. The top strip of the page didn't take clicks there; moving the buttons a little lower fixed it, and the page now reloads only when its own files change, so reloads no longer interrupt a click.
- **Part of the page's script was deleted by mistake** while the shopping list was being split by store, and the view switcher broke for a few minutes. It was restored from Claude Code's saved file history.
- **Live updates used to reset the 3D views.** Each camera now saves its angle, zoom and spin, so an update lands without a jump.
- **The chicken sandwich changed three times:** coronation chicken, then a salad from roasted thighs, and finally chicken Waldorf from a rotisserie chicken.

## How we finished

The app works as described above and has no tests. The conversation took about 1 hour 27 minutes: 79 requests from Pavel, nearly all spoken, and 225 requests to the model, about 60 million tokens, nearly all of them re-reads of the conversation so far. At Anthropic's pay-as-you-go prices for Claude Opus 5.5 in October 2026 ($4 input, $8 cache write, $0.20 cache read and $20 output per million tokens), that is about $20; without caching it would have been about $244.

These were still open at the end of the session:

- Which wine is already in the fridge.
- Lobster meat for the shrimp salad, only if it can be found.
- Bread: a ready-sliced thin loaf or a bakery Pullman.
- The shopping trip for the teapots and dessert knives.
- The party date, allergies, exact quantities and which small gift.

## Files

| Path | What it is |
|---|---|
| `index.html` | The app: one page with its data (sandwiches, shopping list, plan), its 2D drawings, its styles, and a copy of three.js r128, the 3D library (MIT licence) |
| `scenes3d.js` | The three 3D scenes (table, sandwich plate, drinks), drawn with three.js |
| `server.py` | A small web server with live reload, which also triggers the screenshots |
| `snapshot.py` | Takes the numbered screenshots and writes the timeline and gallery |
| `screenshots/` | 14 of the 115 screenshots taken as the app was built, the ones the journey uses; `timeline.md` lists them with their times, `index.html` is a gallery |
| `journey/index.html` | The presentation of how the app was built: one file with its pictures and the live app inside it |
| `TRANSCRIPT.md` | The conversation record |
