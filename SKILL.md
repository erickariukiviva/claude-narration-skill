---
name: narration
description: Make spoken narration (voice-over) for videos, tutorials, demos or any audio, in the house voice - a calm British male voice (edge-tts en-GB-RyanNeural at -4%) - with per-sentence timings for captions and animation cues. Use whenever a task needs text turned into speech, an mp3 voice-over, narration for a Remotion or other video, or captions timed to a voice, in any project on this PC.
---

# Narration in the house voice

Every narration on this PC uses one voice, so all videos sound like the same presenter:

| Setting | Value |
|---|---|
| Engine | `edge-tts` (Python package, installed globally; needs internet: it is Microsoft Edge's online voice) |
| Voice | `en-GB-RyanNeural` (house default) |
| Rate | `-4%` (a little slower than default) |
| Output | mp3, 24 kHz mono |

Never change the voice or rate unless the user asks for it.

### Other voices (only when asked)

`narrate.py` takes `--voice` and `--rate`. `--voice` accepts a preset name or any edge-tts voice id:

| Preset | Voice id | |
|---|---|---|
| `ryan` | `en-GB-RyanNeural` | house voice — calm British male (default) |
| `sonia` | `en-GB-SoniaNeural` | British female |
| `aria` | `en-US-AriaNeural` | US female |

```
python <this skill's folder>/narrate.py --voice sonia "Text to say." out/intro.mp3
python <this skill's folder>/narrate.py --voice en-US-GuyNeural --rate=+0% "Text." out/x.mp3   # any edge-tts id works
```

For a script with **alternating speakers**, give each `--json` clip its own `"voice"` (and optionally `"rate"`): `[{"id": "s01", "text": "...", "voice": "sonia"}, {"id": "s02", "text": "...", "voice": "ryan"}]`. `edge-tts --list-voices` shows the full catalogue (~400 voices).

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

- Writes `<name>.mp3` and `<name>.json`: `{"dur": seconds, "cues": [{"start", "end", "text"}, ...]}`; with `--json`, one pair per clip plus `timing.json` for all.
- Skips a clip whose mp3 already exists (so changing one clip's text re-makes only that one after deleting its mp3); `--force` re-makes all.
- Length comes from `ffprobe` (installed with FFmpeg); without it, the last cue's end is used.

## Writing text that sounds right

- Short sentences; one idea each. Commas make the pauses: "Open Settings, then Countries and hub."
- Spell out what should be said: "star one four four hash", "plus three seven two, two zero zero one", "Settings, then Templates" (not `›`).
- Each sentence becomes one cue, so an animation tied to "sentence 3" stays in time only while the sentence count stays the same: when editing, keep it, or move the cues.

## In a Remotion video

Put the mp3 in `public/`, play it with `<Audio src={staticFile(...)} />` a few frames into the scene, and make the scene last the clip plus about a second: `Math.round(dur * fps) + 42` frames at 30 fps (12 frames before the voice, 30 after). Start each caption or animation at `cue.start * fps` plus that offset.
