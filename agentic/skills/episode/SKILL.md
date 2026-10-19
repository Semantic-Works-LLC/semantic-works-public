---
name: episode
description: Plan, prepare and check one Semantic Works episode (Cyber Kitchen, NYC Subway Live, HeadCam Studio, Tea Time Planner, …): first the planning conversation before anything is recorded (who it is for, the everyday example, the principle underneath), then its release to GitHub in `Semantic-Works-LLC/semantic-works-public`: its folder, README, TRANSCRIPT.md, the main README entry, the journey or video link, the token and cost count, and the checks before release. Use when Pasha wants to make, record, add, release, check or publish an episode or video, with or without a journey.
---

# Making and releasing an episode

An episode is one product built in one recorded conversation between Pasha and Claude. It is released to GitHub, in the `semantic-works-public` repository, as a folder holding its source, its README and its `TRANSCRIPT.md`. An episode comes with either a **journey** (a slide deck; see the `journey` skill for how to write one) or a **video**.

This skill covers only what goes into the repository. The website is covered elsewhere. Nothing is committed, pushed or published without Pasha's go-ahead: prepare, check, report what was found, and wait.

## Before recording: plan the episode with Pasha

This comes first, before anything is recorded or built. When Pasha says he wants to make a new episode or video, start with a short planning conversation, and agree on the answers below before he presses record. Nothing else in this skill starts until this is done.

**Who it is for.** Two layers, every time:

- **The surface is for smart non-engineers:** college graduates, business majors, anyone using AI tools. They must be able to follow it without any programming.
- **The core is for professional engineers:** the reasoning underneath must be sound enough that a senior software engineer agrees with the method.

**Settle these, in this order:**

1. **The lesson:** the one thing a viewer should be able to do afterwards, in a sentence. For example, "Explore by voice, then specify by dictate".
2. **The everyday example** that carries the lesson: a problem a business major has had themselves, ideally with a business flavour. For example: planning a trip or a party, choosing between two vendors or job offers, a renovation, a training plan, a product launch, a busy-season staffing plan, reviewing a contract. Not a programming choice: an example like "SVG versus WebGL versus Swift" loses everyone who is not a developer in the first minute, even when the lesson is broad.
3. **The principle underneath:** one real idea an engineer recognises, such as exploring options before committing, requirements before design, constraints and dependencies, or checking the result. Pasha names it once, in plain words, during the episode.
4. **The check:** one moment where the AI's work is verified, not just accepted, for example a plan checked against a budget, or a result compared with a source. This is what separates rigour from hype.
5. **Where the depth goes:** the technical detail belongs in the README, the transcript and one "Under the hood" slide in the journey, not in the main story.

**Two tests before recording:**

- **The surface test:** could a business major explain the example back after the first 30 seconds?
- **The core test:** would a senior engineer agree with the method?

If either answer is no, change the example or the method before recording, not after. The series and episode name, and whether it will have a journey or a video, are agreed in the same conversation.

## The folder

- One folder per episode: `<series>/<episode>/`, both in kebab case (`cyber-kitchen/episode-x/`, `nyc-subway-live/episode-1/`, `headcam-studio/episode-1/`). A series name is two or three words.
- **What is in it:** the source, `README.md`, `TRANSCRIPT.md`, and either `journey/index.html` with its source pictures under `journey/images/`, or `video/index.html`. Screenshots for the READMEs are checked in; tests and their screenshots are checked in when there are tests.
- **What is not in it:** build output, downloaded or recorded data, caches, virtual environments, coverage output and personal settings. These are git-ignored by the episode's own `.gitignore`, and so are local secrets such as `*.local.env`. Check with `git status --ignored` that each one is really ignored.
- Nothing in the folder reveals more than it needs to: no home-folder paths, user names, personal bundle IDs, signing identities or session-log locations hard-coded in source, scripts or plists.

## The episode README

`<series>/<episode>/README.md`. Read the newest released README and follow it.

- **Title:** `# Semantic Works: <Series> — Episode N (<Name>)`.
- **Opening paragraph:** what was built, in one or two sentences, and that it was built in one conversation between Pavel and Claude, with the month and year. Any disclaimer (unofficial, experimental, not for real use) follows in bold.
- **Links paragraph:** the conversation in `TRANSCRIPT.md`, "with Pavel's requests as understood"; then the journey ("can be followed online" with its published address, and the file `journey/index.html`) or the video ("watched online" on its video page, or "on YouTube"), and the file `video/index.html`.
- **Sections, in this order:** How we started · What we built · How we built it · Run it · What we improved · How we finished · Files, and a Data section when outside data is used. An episode with nothing to report under What we improved leaves it out.
  - **How we started:** the ask, from the transcript, and any choice made before building.
  - **What we built:** a screenshot when there is one, then the features as a nested list with bold lead-ins.
  - **How we built it:** the method in a few bold-led bullets, ending with whether there are tests ("Features first, no tests." when there are none).
  - **Run it:** what is needed, then one command per fenced `bash` block, then what to expect the first time.
  - **What we improved:** what changed and why, in order, from the transcript.
  - **How we finished:** whether it works, the tests, the tokens and cost, and what is open. An idea that was only discussed is potential, not promised.
  - **Files:** a table of every file and folder with what it is, saying which are generated or not included in the repository.
- **Names:** the README calls him Pavel, as the transcript does. Name the product's views, buttons and menu items exactly as the code does.
- Plain words for a business reader; no claim the transcript and the code do not support.

## The main README

The repository's `README.md` lists every series under "Our Projects".

- **A new series** gets its own `### <Series>` section at the top of "Our Projects", so the newest is seen first, unless Pasha says otherwise: one line saying what the series is, the episode list, a line linking the journeys or the video, a table of screenshots (one per episode, each linking to its folder, with alt text that says what it shows), and `[Explore the project](./<series>/)`.
- **A new episode** in an existing series is one bullet: `**[Episode N (<Name>)](./<series>/<episode>/)** —` and two or three sentences from its README. Add its screenshot to the series table, and its journey or video to the series' links line.
- **A journey** is linked at its published address, `https://semantic-works.com/public/<series>/<episode>/journey/`.
- **A video** gets two links: "watch the video", to the episode's video address `https://semantic-works.com/public/<series>/<episode>/video/`, and "watch it on YouTube", to the video itself. The video plays on the website's public projects page, over the page, opened by the address `https://semantic-works.com/public/#watch=<series>/<episode>` (the website is covered elsewhere). The episode's `video/index.html` (copy the newest one) only sends visitors there: a redirect, with links to the video on the site and on YouTube in case it does not happen. GitHub cannot embed a player in a README, which is why the links go to the site. Until Pasha has published the video, the README links use the placeholder `VIDEO_URL` with a `<!-- TODO -->` comment beside them, and it is listed as open in the report.

## The transcript

`TRANSCRIPT.md` is the record of the conversation: Pavel's requests as understood, and Claude's replies as written, with times relative to Pavel's first message (T+0). Tool calls are left out.

- **Pavel's words are not published verbatim.** He speaks by voice, and dictation is full of filler, false starts, slips and side talk. Each of his messages is given only **as understood**: a clean, faithful restatement of what he asked, labelled `*Understood as:*`. It keeps every request, decision, fact, number and name he gave, and adds nothing he did not say. A side conversation unrelated to the work becomes "[Side conversation, left out.]".
- **Say so in the transcript.** Its opening paragraph states plainly that Pavel's messages are given as understood, not as his exact words, and that Claude's replies are as written.
- **Pasted text keeps its own wording.** Text Pavel typed to another AI (for example a conversation with Gemini) and pasted into the session may be summarised or quoted as typed, and journeys may quote it, cited "Pasha, to Gemini". Only his dictation to Claude is given as understood.
- **The verbatim record stays private.** His exact words remain only in the session logs on Pasha's machine, which are never published.

- **It is regenerated from the session log** while the episode is being built, with the episode's transcript tool, so it stays current.
- **It is closed when Pasha says so.** It then ends at that point (marked `# END`), and is never regenerated, extended or rewritten again, even when the conversation goes on. Later turns are not part of the episode. A transcript tool that would overwrite a closed transcript is reported, so it can be changed or left out.
- **Scrubbing** (see below) is the only change after it closes, and only what Pasha approves.

## Counting tokens and cost

The README's How we finished, and the journey's tokens and cost slides, give the same figures.

- Count from the session's own log (`~/.claude/projects/<project>/<session>.jsonl`): every `assistant` entry with `usage`, de-duplicated by message id, keeping the entry with the most output. Add up `cache_read_input_tokens`, `input_tokens + cache_creation_input_tokens` (new input) and `output_tokens`.
- Count only the stretch that the transcript covers: from the first message to the point where the transcript closes. Say what is left out.
- Price each kind separately. Opus 5.5 as used so far: $4 input, $8 cache write (one-hour rate), $0.20 cache read and $20 output per million; Sonnet 5.5: $2, $4, $0.20 and $10. Check the current prices before release and say their date.
- A phase's cost (for example, the test suite) is the same count over the stretch of the log between the turns that began and ended it; say what else happened in that stretch.
- When the transcript quotes a count made earlier in the conversation, the README may quote it as said then, and also give the fresh count, saying what the difference is.
- Recount as the last step before release, and update everything that quotes it.

## Before release

An episode is released as a whole: its source, its README, its `TRANSCRIPT.md`, the main README entry, and its journey when it has one. Before any of it is committed, all of these checks are done, and what was found and changed is reported to Pasha for his decision.

### Build and run it fresh

Build the product and run its tests from a clean state, with the commands in the README's Run it, exactly as written. Report every error and warning. If it cannot be run here (for example, it needs a camera or a person to try it), say what was and was not checked.

### Scrub the transcript

Read `TRANSCRIPT.md` from beginning to end, as a stranger would. Mark anything that should not be public:

- anything said in the heat of the moment that would be regrettable in print: frustration, swearing, remarks about people, companies or products;
- anything private: personal details, names of people who did not agree to be named, clients, credentials, keys, internal addresses, private projects, file paths that reveal more than they need to;
- dictation that went wrong into something embarrassing.

Propose each change to Pasha, with the line and the suggested replacement. Check the *Understood as* lines against the session log: each must say what Pavel meant, no more and no less. A passage taken out is shown in brackets, not silently dropped.

### Review the released files

Every file that will be released (source, scripts, plists, tests, screenshots, pictures, data, the journey) is read or looked at for objectionable or controversial material: offensive or careless wording in code, comments, test names, sample data or invented menus; pictures with watermarks, other people's branding or anything not ours to publish; leftover debugging, secrets, personal paths, user names and identifiers. List what was found and what should change.

### Cross-check the episode, the README, the transcript and the journey

They must agree. Check each against the others, and against the code as it is:

- **The episode against the README:** what the README says was built, how to run it, the commands, the file table and the test counts all match the code and a fresh run.
- **The README (and the journey) against the transcript:** every quote of Pavel is his *Understood as* text from the transcript, word for word; every "Pavel asked…", time, turn and order of events matches it; nothing claims Pavel said, confirmed or decided something he did not.
- **The main README against the episode README:** the name, the description and the links match.
- **The journey against the episode,** when there is one: as in the `journey` skill's checks.
- **The numbers everywhere:** tests, coverage, screenshots, modules, turns, tokens and cost are the same in the README, the journey and a fresh count.

Report each mismatch with where it is and what the source of truth says, then fix it.

### Check the links and placeholders

- Every relative link in both READMEs points to a file that exists, and every picture loads.
- Every placeholder (`VIDEO_URL`, `VIDEO_ID`, `.todo` lines in a journey) is listed in the report as what remains before release.

## The report

End with what is ready, what was changed, what needs Pasha's decision (each with a suggested fix), and what remains open, such as a video address still to come. Do not commit. When Pasha gives the go-ahead, commit the episode as one commit named `<Series>: Episode N: <Name>`.
