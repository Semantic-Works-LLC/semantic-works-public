# Semantic Works: HeadCam Studio — Episode 1 (The Bubble Head)

BubbleHead is a native macOS app that shows your webcam as a round bubble floating above every other app. You can drag it, resize it, blur the room behind you or put a picture there, and see a live transcript of what you say. It was built in one conversation between Pavel and Claude in October 2026, starting from a spoken idea, in about 17 minutes.

The conversation that built the app, with Pavel's requests as understood, is in [TRANSCRIPT.md](TRANSCRIPT.md). A video of how it was built can be [watched online](https://semantic-works.com/public/headcam-studio/episode-1/video/), or [on YouTube](https://youtu.be/ER1GQ6WiXwA); the page itself is [video/index.html](video/index.html).

## How we started

Pavel narrates and records presentations on a Mac and wanted to see his own head on screen while doing it: a bubble from the built-in or external webcam that he could move around and that would show up in recordings.

He suggested a native macOS app rather than Python, because it has to sit on top of all other apps, and left the final choice to Claude. Claude chose Swift with Apple's own frameworks and no third-party libraries.

## What we built

One menu-bar app, written in Swift with AppKit, AVFoundation, Vision, Core Image and Speech.

![The bubble floating over a Claude window, with the room behind the presenter blurred](screenshot.jpg)

- **The bubble.** The webcam in a circle or rounded square, floating above every app, including full-screen apps and slideshows, on every desktop. It appears in screen recordings.
  - **Drag** to move it. **Scroll or pinch** to resize it.
  - **Right-click** it, or use the menu-bar icon, to pick a camera (built-in, external or iPhone), the shape, the mirror image, the ring and the size.
  - **⌃⌥B** hides or shows it from any app. While hidden, the camera is off.
  - It remembers its camera, position, size and look between launches. It has no Dock icon.
- **Background blur.** Apple's on-device person detection finds you in each frame, and the room behind you is blurred: **No Blur**, **Soft** or **Strong**. The blur scales with the bubble. **Apple Video Effects…** opens macOS's own Portrait and Studio Light controls for comparison.
- **Picture behind you.** A picture can replace the room. It stays crisp and is never mirrored, so text in it reads the right way. The layers, bottom to top, are the blurred room, the picture, then you.
  - **Choose Picture…** picks any image; the default is a map from [NYC Subway Live](../../nyc-subway-live/episode-1/), bundled with the app.
  - **Click the bubble** and its ring turns yellow: **arrows** move the picture (**⇧** for bigger steps), **+ / −** zoom, **0** resets, and **Esc**, **Return** or a click elsewhere finishes.
- **Live transcript.** What you say appears in a box under the bubble as you speak, using Apple's on-device speech recognition, with no cloud service.
  - About 4 lines are shown, and sentences older than about 30 seconds disappear. Clicks pass through the box.
  - Each finished sentence is saved with its time to `~/Documents/BubbleHead Transcripts/`, one file per session, so the narration does not have to be extracted from the recording later.
  - **⌃⌥T** turns it on and off, and the microphone with it.

## How we built it

- **Small steps, run each time.** Pavel spoke each request; Claude changed the code, rebuilt the app and relaunched it, checking that it ran without crashing and how much CPU it used.
- **Claude could not see the screen.** Claude described what each change should look like, and Pavel tried it and reported back: the blur worked, the picture was blurred when it should be crisp, the arrow keys did nothing at first.
- **Options before code.** For the blur, Claude laid out four approaches with their trade-offs and Pavel picked the recommended one.
- **Apple's frameworks only.** No third-party libraries and no Xcode project: one build script that calls the Swift compiler and signs the app.
- **Features first, no tests.** Nothing here has automated tests.

## Run it

You need a Mac with the Xcode command-line tools (`xcode-select --install`). The live transcript needs macOS 26 or later.

```bash
./build.sh
```

```bash
open build/BubbleHead.app
```

macOS asks for camera permission on the first launch, and for microphone and speech recognition permission when the live transcript is first turned on.

`build.sh` signs the app with the first Apple developer identity in your keychain, so macOS remembers the permissions across rebuilds. To choose one, set `BUBBLEHEAD_IDENTITY` in a file named `signing.local.env` next to the script. With no identity, the app is signed ad hoc and macOS asks again after every build.

## What we improved

- **Picture sized to the bubble.** Pavel suspected the picture was scaled to the full 1080p camera frame. It was already scaled to the bubble; Claude explained how the frame and the picture are cropped.
- **Crisp picture.** At first the picture was blurred along with the room. Pavel wanted it crisp, so the layers were reordered: only the real room is blurred, and the picture sits on top of it.
- **Keys that reach the bubble.** The bubble never takes keyboard focus, so it does not steal it from the app being presented. That also kept the arrow keys from reaching it. It now takes the keys only after a click, shown by the yellow ring, and gives them back on Esc, Return or a click elsewhere.
- **Moving the picture freely.** The picture first stopped at the bubble's edge. Pavel asked to move it anywhere, so it can now go past the rim and be zoomed out below the bubble's size, with the blurred room showing where it does not cover.

## How we finished

The app works as described above and has no tests. At the end, Pavel asked what it cost. Claude counted about 4.6 million tokens across 47 requests, mostly cached re-reads, or roughly $2.90 at Anthropic's pay-as-you-go API prices, and compared this with estimates for other providers. Counted again to include that last answer, the conversation used about 5.7 million tokens across 53 requests, roughly $3.50 (Claude Opus 5.5 at $4 input, $8 cache write, $0.20 cache read and $20 output per million tokens).

These are open:

- **The edge around you is feathered.** A thin soft edge hides jagged, flickering cut-outs; it can be tightened if it looks haloed.
- **The transparent cut-out,** where only your head and shoulders float over the screen with no bubble, was proposed but not built.
- **The transcript's speed and accuracy** were not reported back during the session.

## Files

| Path | What it is |
|---|---|
| `main.swift` | The app: the bubble window, camera, menus, hot keys, settings and picture controls |
| `blur.swift` | Person detection, the background blur and the picture behind you |
| `transcript.swift` | The live transcript: microphone, on-device speech recognition, caption box and saved files |
| `build.sh` | Builds and signs `build/BubbleHead.app` with the Swift compiler; no Xcode project |
| `Info.plist` | The app's name, menu-bar-only setting and permission messages |
| `entitlements.plist` | The camera and microphone entitlements |
| `assets/background.png` | The default picture behind you, bundled into the app |
| `screenshot.jpg` | The picture of the app used in this README |
| `video/index.html` | The video's address on the website: it sends visitors to the public projects page, which plays the video over the page |
| `build/` | The built app. Created by `build.sh`; not included in the repository |
| `TRANSCRIPT.md` | The conversation record |
