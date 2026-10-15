# Cyber Kitchen — Episode 1 (The Restaurant): Conversation Record

Started 2026-10-11. Each turn gives Pavel's message followed by what Claude answered. Pavel's messages are given as understood: a clean, faithful restatement of what he asked, not his exact dictated words; Claude's replies are as written.

---

## Turn 1

### 🧑 Pavel said

> *Understood as:* Clear the conversation.

### 🤖 Claude answered

Nothing to clear yet — the session was fresh, with no prior conversation. Asked what to work on.

---

## Turn 2

### 🧑 Pavel said

> *Understood as:* I'm working on a new project called Cyber Kitchen: I've been invited to advise a restaurant owner on how his restaurant operates. Before we get to the restaurant, record this conversation in a Markdown file, clearly separating what I said from what you answered, so I have a record at the end. Next, start a local Python web server and build a Hello World HTML page, which I'll open in the browser. As I give you instructions for building the restaurant, push your changes to that page so it refreshes and I can see what you're doing; add a WebSocket or some kind of listener so you can push updates. Do you need anything from me?

### 🤖 Claude answered

Everything is set up and running; nothing is needed from you to get started.

- **Web page:** open http://localhost:8000 — it shows "Hello, World!" with a "Cyber Kitchen — Episode 1" subtitle.
- **Live updates:** the page keeps an open listener to the server (Server-Sent Events rather than a WebSocket, because Python's standard library has no WebSocket support and this needs no installs). Whenever I change a file under `site/`, the browser refreshes itself within about a second. I tested it by editing the heading and the open page updated on its own.
- **Record:** this file, `transcript.md`. I add your words verbatim and my answer after every turn.

Files created:

- `server.py` — the Python web server with the live-reload listener
- `site/index.html` — the page
- `.claude/launch.json` — lets the app start the server
- `transcript.md` — this record

One thing to know: the server only runs while this app session keeps it alive. If the page ever stops responding, tell me and I will restart it.

Ready for the restaurant details.

---

## Turn 3

### 🧑 Pavel said

> *Understood as:* To test that live updates work, I'll watch the page while you replace its content. Put up a pie chart with a table next to it. When I click a sector in the pie chart, select the matching row in the table; when I click a row in the table, select the matching sector. Go ahead.

### 🤖 Claude answered

Pushed. The page at http://localhost:8000 replaced the Hello World content on its own with a pie chart and a table side by side.

- **Sector → row:** clicking a sector highlights the matching table row.
- **Row → sector:** clicking a row pops the matching sector out and dims the others; the centre of the chart shows that category's share.
- Clicking the selected item again clears the selection. Hovering a sector shows its numbers.

I tested both directions in the browser and they work. The data is made up for the test: weekly sales across five menu categories (Mains, Drinks, Appetizers, Desserts, Sides) totalling $42,000.

---

## Turn 4

### 🧑 Pavel said

> *Understood as:* My company doesn't allow me to use JavaScript libraries from the internet on the corporate laptop where I want this page to run. Are you using any JavaScript libraries?

### 🤖 Claude answered

No. The page uses no JavaScript libraries and loads nothing from the internet.

- The pie chart, the table and the click-linking are all hand-written JavaScript, SVG and CSS inside `site/index.html`.
- There are no external scripts, stylesheets, fonts or images; the font is whatever the laptop already has.
- The server (`server.py`) uses only Python's built-in modules, so there is nothing to install with pip either.

I checked both files for outside references: the only web address in the page is the SVG namespace identifier, which is a label the browser never fetches. The page works with the network unplugged. The corporate laptop only needs Python 3 and a browser.

I will keep it that way: no internet-hosted libraries for the rest of the project.

---

## Turn 5

### 🧑 Pavel said

> *Understood as:* Good, you've shown that everything works. Now remove all that content, and let me tell you about the restaurant. The owner invited me to give feedback on it. When I come in, there are a dozen tables: some round ones for four people, a couple for two, and the rest for six. There's a kitchen somewhere, and I see a couple of waiters. A waiter takes an order and puts up a piece of paper, which I guess a cook picks up; I don't know whether there is one cook or several. Plates come out of the kitchen onto a small table, and a waiter brings them over. On the page, set up an SVG live view and draw the restaurant. Then let's try an animation: waiters moving, people coming in, the kitchen cooking. Title the page "Semantic Works: Cyber Kitchen". Let's see what happens.
>
> How is it going?

### 🤖 Claude answered

It's live at http://localhost:8000. The pie chart and table are gone; the page is now titled "Semantic Works: Cyber Kitchen" and shows an animated SVG floor plan of the restaurant.

What you will see:

- **Dining room** with twelve numbered tables, a front door on the left, and guests arriving in parties, walking the aisles to a table that fits them, and leaving after they eat.
- **Two waiters** who take the order at the table, carry a paper ticket to the order rail in the kitchen wall, then later collect plates from the small pass table and bring them to the guests.
- **Kitchen** with two cooks who take a ticket off the rail, cook at a stove (flame and progress bar), and put the finished plates on the pass.
- **Table colours** show each table's state: free, reading the menu, wants to order, waiting for food, eating. A legend is under the picture.
- **Counters** under the picture (guests inside, tickets on the rail, orders on the pass, parties served, parties turned away) and Pause / 1× / 2× / 4× buttons.

I ran the simulation through several hundred simulated seconds: the whole cycle from arrival to departure completes repeatedly, with no errors.

Things I assumed, because you did not say:

- **Table mix:** four round tables for four, two tables for two, six tables for six.
- **Cooks:** two, each with their own stove.
- **Layout:** where the door, kitchen, order rail and pass table sit is my guess.
- **All timings are invented:** how often guests arrive, how long they read the menu, cook times, eating times. A new party arrives every 5 to 10 seconds of simulated time.

With these invented numbers the room fills up and parties start queueing at the door and being turned away, because two waiters and two cooks cannot keep up. That is a product of my made-up timings, not a finding about the real restaurant. Real numbers from the owner would make it meaningful.

Still no libraries: it is all hand-written SVG and JavaScript in `site/index.html`.

---

## Turn 6

### 🧑 Pavel said

> *Understood as:* I don't like "reading the menu" being brown. Make reading the menu yellow, wants to order orange, and waiting for food red, since waiting for food is probably the most annoying time. Eating is green. [A side remark about the dictation followed and was cut off; left out.]

### 🤖 Claude answered

Done, and the page has refreshed. Table outlines now run from calm to annoying:

- **Reading menu:** yellow
- **Wants to order:** orange (the "!" bubble is orange too)
- **Waiting for food:** red
- **Eating:** green (unchanged)

Free tables stay grey, and a table whose guests are still walking to it has a light grey outline. The legend under the picture matches.

Your message cut off at "which is what I" — if there was an instruction after that, I did not get it.

---

## Turn 7

### 🧑 Pavel said

> *Understood as:* You got the colors wrong again. Go yellow, then orange, then red, with a distinct difference between them so I can tell them apart.

### 🤖 Claude answered

You were right: my orange and red were too close to each other, and the colour was only a thin outline, so the states were hard to tell apart. I changed two things:

- **Stronger, more separated colours:** a pure yellow for reading the menu, a clear orange for wants to order, and a bright red for waiting for food. Eating stays green.
- **The whole table top is now filled with the state colour**, not just its outline, so the state is visible at a glance. Free tables stay brown wood; table numbers turn dark on coloured tables so they stay readable.

The legend under the picture uses the same filled colours.

---

## Turn 8

### 🧑 Pavel said

> *Understood as:* I want to add a coffee machine and a pizza maker to the kitchen.

### 🤖 Claude answered

Both are in the kitchen now, and the page has refreshed.

- **Pizza oven:** a brick oven in the bottom-right corner, below the stoves. Its mouth glows and a progress bar fills while a pizza is baking.
- **Coffee machine:** a small unit by the pass table, with a cup under the spout that fills while coffee is brewing.

I also made the cooks use them, so they are not just decoration:

- About a third of orders are pizza: the cook takes the ticket to the oven instead of a stove. Only one cook can use the oven at a time.
- About half of orders include coffee: the cook stops at the machine for a couple of seconds on the way to the pass.

Those shares, and the idea that a cook rather than a waiter makes the coffee, are my assumptions. I ran the simulation for several hundred simulated seconds and both machines were used repeatedly with no errors.

---

## Turn 9

### 🧑 Pavel said

> *Understood as:* I need to be able to select the objects in the restaurant that perform functions. Build a right-hand side panel that can slide out or be hidden with a button at the top. Whenever I select an object, put a card in that panel: a basic about card saying what kind of object it is, what its purpose is, and why it's here. For now, only one object can be selected at a time: if I click another object, show me the card for that object instead. Go ahead.

While Claude was working, Pavel added:

> *Understood as:* I see an orange exclamation mark next to an orange table. What is it for?

> *Understood as:* Why did you pick a dark theme for the kitchen?

### 🤖 Claude answered

**On the orange "!":** it marks a table that is ready to order but has not got a waiter yet. Once a waiter arrives and starts taking the order, the table stays orange but the "!" disappears, so it separates "still waiting for a waiter" from "being served". It also pulses to draw the eye. I can remove it if you find it redundant.

**On the dark theme:** there was no strong reason. The first Hello World page I made was dark and I carried that look forward without asking. The kitchen floor is a cooler blue-grey and the dining room a warmer brown-grey only so the two rooms read as different spaces. I can switch to a light theme if you prefer.

**Selection and side panel:** done, and the page has refreshed.

- **Selecting:** click any working object in the live view and it gets a white glow. Only one object is selected at a time; clicking another one replaces it, and clicking empty floor clears the selection.
- **Panel:** a right-hand panel slides out when you select something. The "Show details / Hide details" button at the top right opens and closes it, and there is a × on the panel itself.
- **Card:** the panel shows one "about" card with the kind of object, its name, what it is, its purpose, and why it is here. I added a fifth line, "Right now", that updates live (for example "Taking the order at table 4").

What you can select: the twelve tables, both waiters, both cooks, each party of guests, the front door, the order rail, the pass table, the two stoves, the pizza oven, the coffee machine, and the prep counter, sink and fridge. The last three are only drawn for context and their cards say so.

I clicked every selectable object in the browser: each one showed exactly one card with the right text, with no errors. The purpose and "why it is here" wording is mine, written from general restaurant knowledge, so correct anything that does not match this restaurant.

---

## Turn 10

### 🧑 Pavel said

> *Understood as:* We loved what you did, but a few small notes. First: when the right-hand panel pops out, you also change the height available for rendering. Keep the height fixed instead. The side panel should take the whole height, the same as the drawing, and the drawing should give up horizontal space but keep its vertical size. Second: we couldn't click a ticket. It would be nice to click a ticket and see how long it has been waiting and what's on it, what people ordered. We also couldn't click the cooks or the parties, because everything is moving. So in the slide-out panel, add one card that always stays there and lists all the actors. We can then pick an actor either on the live map on the left or from the list. Once an actor is picked from the list, show its about card above the list of actors. So let's… [The message cut off here.]

### 🤖 Claude answered

All three notes are done, and the page has refreshed.

**1. Fixed height.** The live view and the panel now share one fixed height. Opening the panel only takes width from the drawing; the counters and legend below no longer jump. The panel is exactly as tall as the drawing and scrolls inside itself if its content is longer. One consequence: because the floor plan keeps its proportions, a narrower space means the plan is drawn smaller, with empty margin above and below it inside the same box. If you would rather the plan stay full size, the panel could slide over the top of the drawing instead of pushing it.

**2. Clickable tickets.** Tickets are now real objects. Click a ticket on the order rail, or a plate on the pass, and its card shows:

- which table it is for, which waiter wrote it and when
- what is on it, for example "1 × Steak frites, 1 × Coffee"
- time since the order was taken, counting live
- where it is right now and for how long: carried to the rail, hanging on the rail, with a cook, on the pass, being carried to the table, or delivered

A selected ticket stays selected as it moves through the kitchen, so you can follow one order from start to finish.

To put real items on tickets I had to invent a menu: six stove dishes, three pizzas and coffee. Each guest orders one dish (about 30% pizza) and about 40% add a coffee. The cooks now follow the ticket: stove dishes at their stove, then pizzas at the oven, then coffee at the machine, and they wait if the shared oven or coffee machine is taken. The menu, the shares and the cooking times are all my invention.

**3. Actors list.** The panel now has a card that is always there, listing every moving actor with a live one-line status:

- Staff: both waiters and both cooks
- Guest parties: each party with its table
- Open orders: each ticket that has not been delivered

Clicking a row selects that actor exactly as clicking it on the floor does: it glows on the floor, its row is highlighted, and its about card appears above the list. I also made the waiters and cooks easier to hit on the floor with a larger click area.

I tested in the browser: the height is identical with the panel open and closed, clicking a ticket shows its card with its items, picking Cook 2 from the list selects and highlights that cook on the floor, and several hundred simulated seconds ran with no errors. I found and fixed one bug on the way (the status text for a party still waiting at the door).

Your message cut off at "So let's" — anything after that did not reach me.

---

## Turn 11

### 🧑 Pavel said

(Pavel attached a screenshot of the page with the details panel open, showing a blank strip to the right of the panel.)

> *Understood as:* I expected all objects to be listed as selectable: the oven, all the tickets, everything, all the actors and objects. Also, when the side panel comes out there is a lot of empty space: as the screenshot shows, next to your panel there's an empty strip, below the "Hide details" button and above "Parties turned away". Please remove that.

### 🤖 Claude answered

Both fixed, and the page has refreshed.

**Everything is in the list now.** The card in the panel is renamed "Actors and objects" and lists every selectable thing, in five groups:

- Staff: both waiters and both cooks
- Guest parties: every party currently present
- Order tickets: every open order
- Tables: all twelve, with a colour dot that follows the table's state
- Kitchen and hand-off points: front door, order rail, pass table, both stoves, pizza oven, coffee machine, prep counter, sink and fridge

Clicking any row selects that object, highlights it on the floor and shows its about card above the list.

**The blank strip is gone.** That was my bug: the way I fixed the height in the last change also made the whole row narrower than the page, which left the gap to the right of the panel. The panel now sits flush with the right edge, under the "Hide details" button and above "Parties turned away", and the drawing gets that width back.

I checked it at a wide window size: the panel lines up with the right edge, the list shows all five groups, and picking "Pizza oven" from the list selects the oven on the floor.

Your message cut off after "So why don't you remove that um," — I took "that" to mean the empty strip.

---

## Turn 12

### 🧑 Pavel said

> *Understood as:* A few comments. There's far too much margin on the right and left; take 100% of the screen. Second, again: in the object picker I expect to see all the tickets and the orders, what people ordered. Please add those.

### 🤖 Claude answered

Both done, and the page has refreshed.

**Full width.** The page now uses the whole browser window, with only a small gap at the edges. The floor plan and the counters grow to fill it.

**Tickets and orders in the picker.** The tickets were in the list before, but buried under the staff and guests and showing only the table, which is probably why you did not see them. Now:

- **Tickets come first.** The list starts with "Open order tickets", then "Delivered orders, last 10", then staff, guest parties, tables and kitchen objects.
- **Each ticket row shows the order itself**: the table, number of guests, when it was taken, the items (for example "2 × Pepperoni pizza, 1 × Margherita pizza, 1 × Chicken parmesan, 3 × Coffee"), and where the ticket is right now.
- **Delivered tickets are kept**, the ten most recent, so you can look back at how long each took. That group starts folded.
- **Every group has a count and can be folded** by clicking its heading, so the list stays manageable.
- **Tables and guest parties show their order too**: selecting a table or a party now includes "Order at this table" / "What they ordered" on its card.

I checked it at a wide window size: the page spans the full width, ticket rows show their items, and selecting a delivered ticket from the list shows its card with the total time from order to food.

---

## Turn 13

### 🧑 Pavel said

> *Understood as:* When you list the objects, under a name such as a waiter you currently print what he is doing, and everything jumps around. I don't want to know what he's doing right now (later we will), so just show the names of the objects. If the names are short, put several on one line, like multiple waiters; you don't need a separate panel for each waiter. Maybe also reduce the font. Also, the white-filled circle next to a waiter confuses me, because it looks like a radio button. Just make buttons with the name of each thing; I click a button and you select that thing. No indicators and no colors, but do group them by category: waiters under "Waiters", parties under "Parties", and so on. Otherwise just buttons: I click a button and you select the object.

### 🤖 Claude answered

Done, and the page has refreshed. The list is now plain name buttons:

- **Names only.** No live status, no order items, no circles, no colours. Nothing in the list moves except when a party or ticket appears or goes.
- **Small buttons that share a line.** "Waiter 1" and "Waiter 2" sit side by side; the twelve tables take three lines. The font is smaller.
- **Grouped by category:** order tickets (open), order tickets (delivered, last 10), waiters, cooks, guest parties, tables, hand-off points, kitchen equipment. Each heading shows a count and folds when clicked.
- **Click a button to select that object.** It glows on the floor, the button gets a white border, and its about card appears above the list.

To keep names short and steady I numbered the things that come and go: tickets are "Ticket 9", parties are "Party 7". The card still gives the full picture, for example "Ticket 9 for table 7" with its items, or "Party 7: 4 guests" with what they ordered.

What each one is doing right now is still on the about card after you select it; I only took it out of the list.

I checked it in the browser: clicking "Waiter 2" in the list selects and highlights that waiter on the floor, and clicking a ticket button shows that ticket's card.

---

## Turn 14

### 🧑 Pavel said

> *Understood as:* Right now we render all the pickable items in the panel, and when we pick one, the panel on top shifts everything. Instead, next to "Hide details", add a button with a magnifying-glass emoji, like a filter or search. When it is clicked, pop up the picker, where I can pick the one item I want selected. After I pick it, the picker goes away and you show me the about box for that item.

### 🤖 Claude answered

Done, and the page has refreshed.

- **Magnifying-glass button.** There is a 🔍 button at the top right, just left of "Show details / Hide details".
- **Pop-up picker.** Clicking it drops down a picker with the same grouped name buttons as before: tickets, waiters, cooks, guest parties, tables, hand-off points and kitchen equipment.
- **Pick and it goes away.** Click a name and the picker closes, the object is selected on the floor, and the details panel shows its about card.
- **The details panel now holds only the about card**, so nothing shifts when you select something.

Two small additions of mine: a filter box at the top of the picker (type "cook" or "ticket 9" to narrow the list), and the picker also closes if you press Escape or click anywhere outside it.

I tested it in the browser: the list is no longer in the side panel, the 🔍 button opens the picker, typing "cook" leaves only Cook 1 and Cook 2, and picking "Pizza oven" closes the picker, highlights the oven and shows its card.

---

## Turn 15

### 🧑 Pavel said

> *Understood as:* I noticed there are no tests. Write a Python test suite and aim for 100% test coverage. I use a Makefile at the root of the project, so I can run the commands from it. Also add full coverage of the JavaScript in the HTML page; if you have to install Chromium, do so. Get as much coverage as you can. Let me know if you need anything.

While Claude was working, Pavel added:

> *Understood as:* As part of the UI testing, please capture a few screenshots: with the sidebar closed, with the sidebar (the right-hand panel) open, and of some known state of the kitchen. Put the PNG files in the test output so I can check them in and see that the UI hasn't changed as we go forward.

> *Understood as:* Thanks, make runs and everything is great. But I'm having difficulty reading the test summary. Tell me how many tests there are in total across Python and JavaScript, and what the coverage is in each.

(Pavel pasted his terminal output of `make test`: 66 passed, JavaScript 751/751 lines = 100.0%, server.py 100%.)

> *Understood as:* What's the status?

> *Understood as:* Why are you rerunning the full suite? Was there a flaky test?

> *Understood as:* Stop.

> *Understood as:* Did you capture the transcript of everything we said?

### 🤖 Claude answered

Stopped. The repeated background test runs are killed and nothing is running.

**What exists and was verified before the stop**

- **68 tests in total, all passing** on every run I did.
  - Python server tests: 20 tests, `server.py` covered 100% (86 of 86 statements, 20 of 20 branches).
  - Browser tests of the page's JavaScript and UI, in headless Chromium: 48 tests, the script in `index.html` covered 100% (751 of 751 lines).
- **Makefile** at the project root: `make test`, `make test-py`, `make test-js`, `make coverage`, `make serve`, `make setup`, `make clean`, and `make help`.
- **Seven UI screenshots** written to `tests/screenshots/` on each run: the empty restaurant with the panel closed, with the panel open, with the picker open, and a fixed moment 2:30 into service with the panel closed, a table selected, a cook selected, and the picker open.
- **One real bug found and fixed by the tests:** asking the server for a page that does not exist crashed the request instead of returning "not found".
- Test tools (pytest, coverage, Playwright) are installed in `.venv` in the project. Chromium was already on this machine, so nothing was downloaded for it. The page and the server themselves still need nothing installed.

**Not finished**

- **Screenshot flakiness.** Screenshots 06 (cook selected) and 07 (busy, picker open) came out with slightly different pixels in roughly one run in eight; the other five were identical every time. No test fails because of it, but those two files may show as changed when nothing changed. I had not found the cause when you stopped me.
- **Readable summary for `make test`.** I wrote it (a new `tests/summary.py`, plus edits to `tests/conftest.py` and the `test` target in the Makefile) but had not run it even once. The `make test` you ran earlier used the previous Makefile; the new one is untested and may need a fix.
- **Screenshots from a different browser differ.** Running with installed Google Chrome instead of Playwright's Chromium produces different pixels, so screenshots should always be made with the same browser.

**Answers to the questions asked along the way**

- Why repeat the full suite: not a failing test. I was rerunning to catch the two screenshots in their differing state and see which pixels differ.

**On the transcript**

Yes, with one limit. `transcript.md` has all 15 turns: everything you said is there word for word, including the messages you sent while I was working and the ones that cut off mid-sentence, and each is followed by my answer. What it does not have is my short in-between progress lines (such as "still building" or "now testing"); for each turn I recorded the answer I gave at the end, not every interim remark. The screenshot and terminal output you pasted are described in a line rather than copied in.

---

## Turn 16

### 🧑 Pavel said

> *Understood as:* Append this last bit to the transcript.

(Pavel interrupted, then continued:)

> *Understood as:* Now create a file called agents.md and summarize... no, I take that back. Make a file called readme.md and summarize in it how we started, what we built, how we built it, what we improved, and how we finished this episode.

### 🤖 Claude answered

Both done.

**Transcript.** The last exchange is appended. For the record, the closing reply to Turn 15, as it was shown to Pavel, was:

> Stopped. The background test runs are killed and nothing is running.
>
> **Transcript.** Yes, with one limit. transcript.md has all 15 turns: everything you said is there word for word, including the messages you sent while I was working and the ones that cut off mid-sentence, each followed by my answer. It does not have my short in-between progress lines ("still building", "now testing"); for each turn I recorded the answer I gave at the end. The screenshot and terminal output you pasted are described in a line rather than copied in.
>
> **Tests: verified before the stop.** Python server (`server.py`): 20 tests, 100% coverage (86/86 statements, 20/20 branches). Browser tests of the page's JavaScript and UI: 48 tests, 100% coverage (751/751 lines). Total: 68, all passing.
>
> - Screenshots: seven PNGs are written to `tests/screenshots/` on each run — the empty restaurant (panel closed, panel open, picker open) and a fixed moment 2:30 into service (panel closed, table selected, cook selected, picker open).
> - Bug found by the tests: asking the server for a page that doesn't exist crashed the request instead of returning "not found". That is fixed in server.py, but the web server on port 8000 is still running the old code because I didn't restart it.
> - Installs: pytest, coverage and Playwright went into `.venv` inside the project. Chromium was already on this machine, so nothing was downloaded for it.
>
> **Not finished.**
>
> - Two screenshots are unreliable. `06-busy-cook-selected.png` and `07-busy-picker-open.png` came out with slightly different pixels in roughly one run in eight; the other five were identical every time. No test fails because of it, but those two may show as changed when nothing changed. I hadn't found the cause when you stopped me.
> - The readable summary for `make test` is untested. I wrote tests/summary.py and changed tests/conftest.py and the `test` target in the Makefile, but never ran them. Your earlier `make test` used the previous Makefile, so the next run may need a fix.
> - Screenshots depend on the browser. Running with installed Google Chrome instead of Playwright's Chromium gives different pixels, so always generate them with the same one.
>
> Tell me when you want me to pick either of the unfinished items back up.

**README.** I created `README.md` (not `agents.md`, as you took that back) with the five parts you asked for: how we started, what we built, how we built it, what we improved, and how we finished. It also has a short "Run it" section and a list of the files.

The "how we finished" part says plainly what is still open: the two unreliable screenshots, the untested summary for `make test`, screenshots depending on which browser makes them, the running server needing a restart, and the project not being in version control yet.

I named the file `README.md` in capitals, which is the usual convention. I did not run any tests or change any code in this turn.

---

## Turn 17

### 🧑 Pavel said

> *Understood as:* Add a proper .gitignore at the root, as I'll be adding this to a git repo.

### 🤖 Claude answered

Added `.gitignore` at the project root. It keeps out of git:

- `.venv/`, the virtual environment with the test tools (recreated by `make setup`)
- Python caches (`__pycache__/`, compiled files)
- test and coverage output (`.pytest_cache/`, `.coverage`, the `coverage/` folder), all recreated by `make test`
- personal Claude Code settings (`.claude/settings.local.json`)
- macOS and editor clutter (`.DS_Store`, `.idea/`, `.vscode/`, swap files)

Two things are deliberately still tracked: the screenshots in `tests/screenshots/`, since checking them in is their purpose, and `.claude/launch.json`, which only tells the app how to start the web server.

I did not create the git repository or commit anything.

---
