# Transcript

A 10½-minute recording made in October 2026: Pasha shows two ways of talking to ChatGPT, dictate and voice, by asking it the same question both ways. Times are minutes:seconds from the start of the recording.

The words come from the recording's sound, turned into text by Apple's speech recognition. Everything is given **as understood**: a clean, faithful restatement of what was said, not the exact spoken words. In the voice conversation, ChatGPT's spoken replies are given the same way and marked **ChatGPT**.

## 00:00 — Pasha

*Understood as:* Pasha here, from Semantic Works. Today we're talking about dictate versus voice as ways of talking to an LLM.

Here's our use case. This is my art: it's painted in acrylic, and what you see here is an animation that lets you fly through it at micro-resolution. Today we'll design this app with ChatGPT, using both dictate mode and voice mode, and I'll tell you which one to use and why.

## 00:27 — Pasha

*Understood as:* Let's switch to ChatGPT. There are two buttons we'll talk about: this one is dictate, and this one is voice.

The way I use dictate, I narrate the thoughts I have, in any order, for up to five minutes, and then I let it run. Let's see how I'd do that for this app, as if I hadn't built it yet.

## 00:51 — Pasha, dictating to ChatGPT

*Understood as:* I have this gigapixel image. I'm thinking of displaying it in the browser, or in a native app on macOS. I want to fly through it: move left and right, zoom in and out, smoothly. I want to build an application that does that, given the image.

I'm thinking of the browser, because that's easy and portable, but I don't know SVG versus WebGL, or how compatible they are across operating systems and browsers. I also don't know whether it will be smooth or jerky. If it isn't fast enough, maybe I'd go to native Swift, but I've never done anything in Swift.

That's the space of my worries, and I need guidance on how to get this built. I want it built quickly, up and running in a short time. I don't want any third-party dependencies; everything should be built from scratch. And I want it to be fast: buttery smooth, flying by. Let me know what you think.

## 02:00 — Pasha

*Understood as:* That was very typical. I said a lot, in no particular order; that was my exploration of how to approach the app. Even though I spoke out of order about many different things, it did an excellent job: it covered the source image, recommended tiling, discussed smoothness and canvas versus Swift, and chose WebGL 2.0. Great content.

But notice: I spoke a lot, and it responded with a lot, so it will take me a while to go through it. That's the nature of dictate mode. You put in many minutes, and you should expect to spend time going through the response.

## 03:03 — Pasha

*Understood as:* Now let's do the same thing in voice mode. Voice is a very different interaction: I say a couple of sentences, it says a couple of sentences, and we go back and forth. Because it has to answer by voice, there's no room to give me five pages. Whatever I ask, it has to go through everything it knows that's relevant and pick what matters most for the very next answer. That makes for a very different conversation.

I use voice to explore the options quickly, without going deep right away; I can go deeper later.

One small note: if I don't interrupt it, it keeps talking. I think they changed that around August; before, it was more back-and-forth, with pauses. Now I have to interrupt, or it will take up all the time. It's October 2026, and I expect this to keep changing; tomorrow it may behave differently.

Let's do the same exploration, by voice.

## 04:30 — Voice conversation with ChatGPT

**Pasha:** Hey, are you there?

**ChatGPT:** Yes, I'm here. What's on your mind?

**Pasha:** Love the accent, by the way.

**ChatGPT:** Thank you. Very happy to be talking to you.

**Pasha:** I have an idea. I have a big gigapixel image I created, and I want to show it on a computer screen with a fly-by animation: zooming in and out.

**ChatGPT:** Fun. You mean taking one huge image and flying over it, like a camera moving?

**Pasha:** Yes, that's right. I'm a software engineer, so I'm thinking of the browser, so I can open it on any operating system or browser and give it to friends. But I don't know WebGL versus SVG versus just divs, and maybe it won't be fast enough, so maybe I should write native Swift instead. Those are my thoughts.

**ChatGPT:** Good questions; give me a second. WebGL is a solid starting point, because it handles smooth zooming and large images better than rolling your own WebGL renderer. You could drive the camera path with a simple keyframe timeline in JavaScript, animate the viewport, and keep it all shareable as a web page. Swift would be fine, but…

**Pasha:** Hold on, before Swift. Do I push the whole gigapixel image into WebGL, or do we need tiling? How would that work?

**ChatGPT:** Tiling is the trick. You don't want the whole gigapixel image in memory at once. You split it into smaller tiles, usually as a multi-resolution pyramid of zoom levels, and load only the ones you need.

**Pasha:** But if I already have tiles, why do I need WebGL? Wouldn't SVG be fine?

**ChatGPT:** If you're just showing a raster gigapixel image with smooth zooming, you don't need WebGL. SVG is for vector graphics, not huge bitmap images. For this, a library that already solves tiled image viewing is best; then you just animate the camera path on top.

**Pasha:** So the library that does this best is WebGL-based? Just checking.

**ChatGPT:** Not quite. The benefit comes from a tiled image viewer library, not from WebGL. You'd start with something like OpenSeadragon…

**Pasha:** No, I can't do that. My company doesn't let me use third-party packages. It has to be plain JavaScript, from scratch.

**ChatGPT:** Thanks for the heads-up; that changes the architecture. Plain JavaScript is absolutely enough, and you don't need WebGL. I'd make a simple tiled image viewer with canvas 2D, plus a small offline step to generate the tiles.

**Pasha:** I hear you. Sorry, I have to rush to a meeting; one more thing, quickly. How many frames per second can I expect, and when should I switch to Swift?

**ChatGPT:** Aiming for 60 frames per second on a modern computer is reasonable if you optimise the rendering, but don't promise it until you've tested on your target hardware. If you're below 30 and can't fix it, that's when I'd consider a native Swift app, or if you truly need tight macOS integration.

**Pasha:** Thank you very much. Bye.

## 08:46 — Pasha

*Understood as:* So there it was. You saw how different that was: I didn't have to read a lot, and we stayed at the top level. That's often what matters when choices have to be made quickly, or when you're exploring something you don't know.

I use both. I start with voice and explore the space. Once I've chosen a direction, I switch to dictate and go through the use cases, more like a product requirements document or a system architecture that I narrate.

Dictate is also how I review. With a document, I turn on dictate, go through it and say: "Paragraph one is good; page two needs a new opening", for up to five minutes, and then ask it to summarise all the notes. With an app, I use it and narrate as I go: how things felt and where the rough corners were. It does an excellent job of summarising all of that.

## 10:01 — Pasha

*Understood as:* I first limited typing because I had a pinched nerve, and typing was painful. That's resolved now, but I learned to avoid typing, and now I don't type any more. It's between dictate and voice; that's how I get my work done. I hope you do the same. Pasha, Semantic Works. See you around.
