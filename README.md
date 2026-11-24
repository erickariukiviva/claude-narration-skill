# narration: a Claude Code skill

Spoken narration in one house voice (edge-tts `en-GB-RyanNeural`, rate `-4%`) with per-sentence
timings, for any project. `SKILL.md` is what Claude reads; `narrate.py` makes the clips.

## Install on a PC

```
git clone https://github.com/erickariukiviva/claude-narration-skill %USERPROFILE%\.claude\skills\narration
python -m pip install --user edge-tts
```

FFmpeg (for `ffprobe`) is optional: `winget install Gyan.FFmpeg`. Claude Code finds the skill in the
next session; ask for a voice-over, or type `/narration`.

## What `narrate.py` does

- One clip, a text file, or a whole script of clips (`--json`), each with sentence timings.
- Re-records only the clips whose words, voice or rate changed.
- Records several clips at once and retries when the online voice drops a connection.

`SKILL.md` also covers how to write text that the voice reads well, and how to build a narrated
course in Remotion: one clip per beat, one composition per lesson.
