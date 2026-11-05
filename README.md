# narration: a Claude Code skill

Spoken narration in one house voice (edge-tts `en-GB-RyanNeural`, rate `-4%`) with per-sentence
timings, for any project. `SKILL.md` is what Claude reads; `narrate.py` makes the clips.

## Install on a PC

```
git clone https://github.com/erickariukiviva/claude-narration-skill %USERPROFILE%\.claude\skills\narration
pip install edge-tts
```

FFmpeg (for `ffprobe`) is optional: `winget install Gyan.FFmpeg`. Claude Code finds the skill in the
next session; ask for a voice-over, or type `/narration`.
