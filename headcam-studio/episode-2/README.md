# Semantic Works: HeadCam Studio — Episode 2 (Dictate and Voice)

Two ways to talk to an AI, and when to use each. In a 10½-minute recording made in October 2026, Pasha asks ChatGPT the same question twice, once by dictation and once in a spoken conversation, and shows how different the two are and how he combines them to get work done without typing.

The recording, with Pasha's words and ChatGPT's replies as understood, is in [TRANSCRIPT.md](TRANSCRIPT.md). A short slide-by-slide summary can be [followed online](https://semantic-works.com/public/headcam-studio/episode-2/journey/); the file itself is [journey/index.html](journey/index.html). The video can be [watched on YouTube](https://youtu.be/f1RkOoOMNjc).

## How we started

Pasha paints in acrylic, and one of his paintings exists as a gigapixel image: an animation lets you fly through it at microscopic detail. The question for this episode was how he would have designed that fly-through app with ChatGPT if he were starting today, and what the two buttons in ChatGPT, dictate and voice, are each good for.

## What it shows

- **Dictate.** Pasha talks for about a minute, in no particular order: a gigapixel image, a smooth fly-through, browser or native Swift, SVG or WebGL, no third-party code, and it must be fast. ChatGPT answers thoroughly (tiling, smoothness, canvas versus Swift, and a choice of WebGL 2.0), but at length: a lot said in, a lot to read out.
- **Voice.** The same question as a spoken back-and-forth. Because it answers aloud, ChatGPT has to pick what matters most for the very next reply, so the conversation stays at the top level and moves fast:
  - tiling first, as a pyramid of zoom levels;
  - no WebGL needed, and SVG is for vector graphics, not huge bitmaps;
  - a suggestion of OpenSeadragon, ruled out because no third-party code is allowed, and a new answer within seconds: plain JavaScript with canvas 2D and the tiles made offline;
  - aim for 60 frames per second, and switch to Swift only below 30.
- **How to combine them.** Voice to explore the options and choose a direction; dictate to specify it, like narrating a product requirements document or a system architecture; and dictate to review, narrating notes while reading a document or using an app, then asking for a summary.
- **Why no typing.** Pasha stopped typing because of a pinched nerve. It has healed, but he never went back: he now gets his work done by dictate and voice.

## How we made it

- **A screen recording** of Pasha using ChatGPT on his Mac, narrated as he goes.
- **ChatGPT, not Claude:** the dictate and voice modes shown are ChatGPT's, as of October 2026. Pasha notes they change over time; around August the voice mode began to keep talking unless interrupted.
- **The transcript** was made from the recording's sound with Apple's on-device speech recognition, then given as understood.

## How we finished

The video and this summary are the whole episode: there is no app and no code, so there are no tests, no token count and no cost. Behaviour of the dictate and voice modes is as seen in October 2026 and may have changed since.

## Files

| Path | What it is |
|---|---|
| `TRANSCRIPT.md` | The recording, as understood: Pasha's words and ChatGPT's spoken replies |
| `journey/index.html` | The slide-by-slide summary: one file with its pictures inside it |
| `journey/images/` | The pictures in the summary, kept as files |
