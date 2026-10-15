---
name: journey
description: Write or revise a "journey" — the single-file HTML slide deck that tells how one Semantic Works episode (Cyber Kitchen, NYC Subway Live, …) was built in a conversation between Pasha and Claude. Use when asked to start, extend or check a journey, or to add its title, result, tokens, cost or closing slides. Releasing the episode it belongs to is the `episode` skill.
---

# Journey slides

A journey is the story of one episode: what was asked, what was tried, what was kept, what it cost, and where it goes next. It sits beside the episode's source as `journey/index.html` and is published at `https://semantic-works.com/public/<series>/<episode>/journey/`.

These rules come from the published journeys (NYC Subway Live Episode 1, Cyber Kitchen Episodes 1 and 2) and from the refinements Pasha asked for while building Cyber Kitchen Episode X. Read the newest published journey before starting a new one, and copy its CSS and scripts rather than writing new ones.

This skill covers writing the journey. Releasing it with its episode to GitHub (the README, the transcript, the token count and the checks before release) is the `episode` skill; the website is covered elsewhere.

## The file

- **One self-contained HTML file.** Every picture is a base64 data URL in an `IMAGES` map applied to `img[data-img]`; the finished product, when it runs as a single page, is embedded too (`APP`, base64). Nothing loads from elsewhere except the Semantic Works logo, which removes itself if it cannot load.
- **Source pictures are kept as files** under `journey/images/`, in subfolders by purpose (`story/`, `build/`, `episodes/`, early versions, …). The deck does not reference them; they are there to be re-embedded or replaced.
- `<title>`: `<Episode name> — Episode N`.
- **Light theme only**, with the shared tokens: `--bg #f6f7f9`, `--panel #fff`, `--edge #d5dae1`, `--text #1b2330`, `--muted #5d6877`, `--accent #0b62d6`, `--warm #b85c00`. Body `18px/1.5 system-ui`.
- **Colour has one meaning each.** Blue (`#0050d8`) is only for things to click: buttons and the navigation. Green (`#00803f`) is the episode name, the figures in stat boxes, and the one button that opens the live product. Warm orange is for kickers and for the experimental notice. Red and green text labels (`.bad`, `.good`) mark what was wrong and what was good.
- **Fixed furniture:** the logo top left, linking to `https://semantic-works.com/public/`; the series line top right (`Semantic Works: <Series>: <Episode N: Name>` with the episode in green), hidden on the title slide, which carries it in full; the navigation bar at the bottom with ◀◀ ◀ ▶ ▶▶, `N / total · slide name`, and one dot per slide whose tooltip is `N: slide name`.
- **The experimental notice** (`Experimental · …`, in orange, with the full disclaimer in its tooltip) says what is invented or unofficial. It appears **only on the first slide** of every journey and is hidden on all the others, for example with `body:not(:has(.slide[data-name="Start"].on)) #notice { display: none; }`.
- **Navigation:** plain left and right arrows move the slides (not with a modifier held); the address carries `#N`. A button that jumps to another slide uses `jump()`, which leaves a step in the browser's history so the back button returns.

## Slides

Every slide has a `data-name` (a short name for the counter), a kicker and a heading.

- **Kicker** (small, orange, upper case) says where in the story this is: `0:16 – 0:22 · Turns 4 – 5`, `Version 3 of 6 · …`, `The build · phase 2 of 5`, `The result`, `Open`.
- **Heading** says what happened, as a statement: "We built a recorder for everything the MTA publishes", "Phase 2: polish the first view toward usability". When several slides make one step, they share its prefix: "Phase 3: …", then "Phase 3, continued: …".
- **Layouts:** text on the left and one picture on the right (default); `wide` for tables, lists and quotes; `title` for the first, the closing and any interlude slide; `showcase` for the result.
- **Fit on one screen.** No slide scrolls at 1440×900. Check every slide after every change, with the body's `scrollHeight - clientHeight` equal to 0; check 1280×720 too and say which slides still do not fit there. To make room, shorten text before shrinking type.
- **One idea per slide,** told in plain words for a business reader. No jargon without its meaning beside it.
- **Pictures** are screenshots of what was on the screen at that moment, with a caption that says what it shows. A picture in a slide's figure opens full screen on click; another click doubles it about the mouse; Escape or a click beside it closes. The logo, the cover and the author's photo do not open.
- **Pasha's words** are quoted as understood, word for word from the transcript's *Understood as* text (his exact dictated words are never published), in a `blockquote` with a `cite` ("Pasha, to Claude", "Pasha, in Episode 2"), lightly trimmed with `…`, on a very light blue background (`#e9f2ff`). Quote only when the words themselves carry the point; a quote that only repeats the bullets is removed.
- **What was rejected** gets the same treatment as what was kept: its picture, what it was, and then, in one list, what was wrong (red labels) and the good ideas in it that came back later (green labels). The kicker carries a pill: "thrown away", "not kept" or "kept".
- **Name things the same way everywhere:** Pasha (Dr. Pavel (Pasha) Simakov in the author card), Claude, and the product's own names for its views and objects.
- **Placeholders** for Pasha to fill in are orange italic lines (`.todo`). None may remain when the journey is published.

## The first slides

1. **Start** (`title`): the date kicker top right (`October 2026`); the heading `<Series>:<br><span class="episode">Episode N: Name</span>` beside a 288-pixel square cover picture; one lede paragraph saying what was built, from what, by whom and in how long, and that it was built 100% by voice, no code or commands entered by keyboard; the author card (photo, "Dr. Pavel (Pasha) Simakov", "Managing Partner, Semantic Works LLC", LinkedIn); and the source line: "The source for this episode is on GitHub:" linking to the episode's folder in `Semantic-Works-LLC/semantic-works-public`.
2. **Slide 2 introduces the demo; slide 3 is the demo.** If a live demo is available, slide 2 ("Play right away", `title` layout, kicker "Before the story") says that the finished product runs live on the next slide, with nothing to install and nothing to configure; it has a green "Play with it live" button that goes to the demo and a "View the source code on GitHub" button; it says the source of everything presented can be seen too; and it ends: press ▶ to play with it, after which ▶ continues with the story.
3. **Slide 3 is the live demo** ("Try it", marked `data-live`): the product itself in a frame, loaded fresh on each visit, under an introduction that says it is live (or a recording, replayed live), how to use it, and how to continue. If the product needs a server, build a self-contained copy with recorded data served from inside the page. If even that is not possible, slide 2 says so and how to run it in a minute, with "Run it yourself" and "View the source code on GitHub", and there is no slide 3 demo.

The story follows: how it started (the ask, in Pasha's words), each version or phase in order, what was kept, and the tests.

## The last slides, in this order

1. **The result** (`showcase`, kicker "The result"): one heading that names what it is; the features as two columns of small boxes (heading and one line each); a picture of the finished product; and the buttons: green "Play with it live" when there is a live slide, "Run it yourself", "View the source". Say how it is deployed and that it was built by voice.
2. **Tokens** (kicker `0:00 – H:MM · The whole conversation`): the count, in millions, and the number of requests and the model, then a table of the four kinds (re-read from cache, new input, output, total) with what each is, a paragraph on why a long conversation counts the same text again and again, and "Other statistics" as stat boxes (turns, views, modules, tests, coverage, screenshots…).
3. **Cost** (kicker "If bought as API calls, with no subscription"): the dollar figure on the model that ran the session, a table with the other models priced on the same counts, what it would have cost with no caching, and the assumptions: a pricing comparison, not a prediction; cache writes at the one-hour rate; prices as of the month, with their source.
4. **What is not done** (kicker "Open"): what is invented, what is missing, what is known to be weak, and where the full conversation is (`TRANSCRIPT.md`).
5. **Related episodes** (the second-to-last slide, see below).
6. **Public projects** (the very last slide, see below).

### The second-to-last slide: related episodes

Points the reader to the rest of the series, so each journey leads to the others.

- Kicker "The series so far", heading "All the episodes" (or, for a first episode, "What comes next").
- One column per episode: a screenshot of that episode's finished product, its number and name, two or three sentences taken from its README, and a blue button "Follow the Episode N journey" to its **published** journey (`https://semantic-works.com/public/<series>/<episode>/journey/`). The episode being presented says "You are here." instead of a button.
- The next episode, if one is planned, in one line under the columns ("Next, Episode 3: …"). An episode that is only talked about is called potential, not promised.

### The very last slide: public projects

Points the reader to everything else Semantic Works has published. It is the same on every journey.

- `title` layout. Kicker "Thank you for your interest"; heading "Want to see more?"; lede "There is more from Semantic Works to explore.".
- One blue button, "See our public projects", to `https://semantic-works.com/public/`.
- The author card: photo, "Dr. Pavel (Pasha) Simakov", "Managing Partner, Semantic Works LLC", the LinkedIn link.
- The sign-off "Happy vibe coding with LLM AI!" in green.
- Nothing comes after it.

## Tokens and cost

The figures on the tokens and cost slides are counted as the `episode` skill says, and are the same as in the episode's README.

## Checking a journey

Before saying a journey is done:

- every slide fits at 1440×900;
- no `.todo` placeholder remains (or, if the journey is not yet published, say which remain);
- every picture loads, and every button and link goes where it says;
- the live slide loads the product with no errors, and the browser's back button returns from it;
- the figures on the slides (tests, coverage, tokens, cost) match a fresh count;
- the title slide, the result, the tokens and cost slides, the related-episodes slide and the public-projects slide follow the rules above;
- the episode's checks before release, in the `episode` skill, have been done.
