---
name: narration
description: Make spoken narration (voice-over) for videos, tutorials, courses, demos or any audio, in the house voice - a calm British male voice (edge-tts en-GB-RyanNeural at -4%) - with per-sentence timings for captions and animation cues. Use whenever a task needs text turned into speech, an mp3 voice-over, narration for a Remotion or other video, a narrated course or lesson series, or captions timed to a voice, in any project on this PC.
---

# Narration in the house voice

Every narration on this PC uses one voice, so all videos sound like the same presenter:

| Setting | Value |
|---|---|
| Engine | `edge-tts` (Python package; needs internet: it is Microsoft Edge's online voice) |
| Voice | `en-GB-RyanNeural` (house default) |
| Rate | `-4%` (a little slower than default) |
| Output | mp3, 24 kHz mono, 48 kbit/s |

Never change the voice or rate unless the user asks for it.

Make the audio on the PC you are working on. edge-tts is light and fast anywhere with internet, so there is
no reason to send narration work to another machine.

## Setup check

```
python -m edge_tts --help          # missing: python -m pip install --user edge-tts
```

Call it as `python -m edge_tts`, not `edge-tts`: on Windows the `edge-tts.exe` launcher is often not on PATH.
FFmpeg is optional (`winget install Gyan.FFmpeg`); `narrate.py` finds `ffprobe` in winget's folders even
before a new terminal picks up PATH, and without it works out the length from the mp3's size.

### Other voices (only when asked)

`narrate.py` takes `--voice` and `--rate`. `--voice` accepts a preset name or any edge-tts voice id:

| Preset | Voice id | |
|---|---|---|
| `ryan` | `en-GB-RyanNeural` | house voice: calm British male (default) |
| `sonia` | `en-GB-SoniaNeural` | British female |
| `aria` | `en-US-AriaNeural` | US female |

```
python <this skill's folder>/narrate.py --voice sonia "Text to say." out/intro.mp3
python <this skill's folder>/narrate.py --voice en-US-GuyNeural --rate=+0% "Text." out/x.mp3   # any edge-tts id works
```

For a script with **alternating speakers**, give each `--json` clip its own `"voice"` (and optionally `"rate"`): `[{"id": "s01", "text": "...", "voice": "sonia"}, {"id": "s02", "text": "...", "voice": "ryan"}]`. `python -m edge_tts --list-voices` shows the full catalogue (~400 voices).

## Quick: one clip

```
python -m edge_tts --voice en-GB-RyanNeural --rate=-4% --text "Hello. This is the house voice." --write-media out.mp3
```

## With timings: `narrate.py`

The script next to this file makes the mp3 **and** the start/end of every sentence (from edge-tts subtitles), for captions or for starting an animation on a given sentence:

```
python <this skill's folder>/narrate.py "Text to say." out/intro.mp3
python <this skill's folder>/narrate.py --file script.txt out/intro.mp3
python <this skill's folder>/narrate.py --json clips.json out/voice/        # many clips: [{"id": "s01", "text": "..."}, ...]
```

- Writes `<name>.mp3` and `<name>.json`: `{"dur": seconds, "cues": [{"start", "end", "text"}, ...], "key"}`; with `--json`, one pair per clip plus `timing.json` for all.
- Re-makes a clip only when its text, voice or rate changed (the `key`), so editing one line of a long script re-records just that line. `--force` re-makes all.
- `--json` records 4 clips at a time (`--jobs N` to change). A dropped connection is retried, and a half-written clip never replaces a good one.
- An `id` may contain a folder (`"lesson2/s01"`), which keeps a multi-video project's clips apart.

## Writing text that sounds right

- Short sentences; one idea each. Commas make the pauses: "Open Settings, then Countries and hub."
- Spell out what should be said: "star one four four hash", "plus three seven two, two zero zero one", "Settings, then Templates" (not `›`).
- Code names: say them the way a person would. `@Composable` is "at Composable", `KMP` is "K M P", `48dp` is "forty eight D P", `0x20` is "hex two zero", `StateFlow` is "State Flow", `jSerialComm` is "J Serial Comm". Then turn the spoken form back into the real name for the caption (a list of `[spoken, shown]` replacements), so the viewer reads `@Composable` while hearing it said properly.
- Numbers with units: "nine thousand microseconds", "thirty eight kilohertz". Avoid symbols such as `/`, `->`, `|`; the voice reads them oddly or skips them.
- Each sentence becomes one cue, so an animation tied to "sentence 3" stays in time only while the sentence count stays the same: when editing, keep it, or move the cues.

## In a Remotion video

Put the mp3 in `public/`, play it with `<Audio src={staticFile(...)} />` a few frames into the scene, and make the scene last the clip plus about a second: `Math.round(dur * fps) + 42` frames at 30 fps (12 frames before the voice, 30 after). Start each caption or animation at `cue.start * fps` plus that offset.

## A narrated course (several lessons or videos)

This shape has worked well for beginner courses built from a real codebase:

- **Data, not markup.** Keep each course in one data file: a list of scenes, each with a `kind` (which visual to draw: code, cards, diagram...) and a list of **beats**. A beat is one narration clip plus what the screen shows while it plays (`say`, highlighted `lines`, a short `note`). The visuals read the current beat, so picture and voice can never drift apart.
- **One clip per beat**, id `<course>/<scene>-<n>`. Generate them with `--json`, then read every `dur` into a durations file that the video imports to work out its timeline: scene lead 0.5 s, a 0.3 s gap between beats, a 0.7 s tail.
- **One composition per course**, sharing the components and theme, so a series looks like one series.
- **Real code only.** Quote the project's actual files (marked "simplified from <file>" when trimmed), and say where something does not exist yet, rather than inventing it.
- **Check before a long render:** listen to one or two clips, render single stills of the busiest scenes, then render everything.
