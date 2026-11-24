"""Narration in the house voice (edge-tts en-GB-RyanNeural, rate -4%), with per-sentence timings.
    python narrate.py "Text to say." out/intro.mp3
    python narrate.py --file script.txt out/intro.mp3
    python narrate.py --json clips.json out/voice/       clips.json: [{"id": "s01", "text": "..."}, ...]
    python narrate.py --voice sonia "Text to say." out/intro.mp3    presets: ryan (default, house voice), sonia, aria; or any edge-tts voice id
Writes <name>.mp3 and <name>.json ({"dur", "cues": [{"start", "end", "text"}]}); --json also timing.json.
A --json clip may carry its own "voice"/"rate" (e.g. alternating speakers). An existing mp3 is kept unless --force.
"""
import argparse, json, os, re, shutil, subprocess, sys, tempfile

# The house voice is Ryan. Alternates can be chosen with --voice (a preset name below, or any edge-tts voice id).
VOICES = {
    "ryan": "en-GB-RyanNeural",    # house voice — calm British male
    "sonia": "en-GB-SoniaNeural",  # British female
    "aria": "en-US-AriaNeural",    # US female
}
DEFAULT_VOICE, RATE = "en-GB-RyanNeural", "-4%"


def resolve_voice(name):
    """Map a preset name (ryan/sonia/aria, case-insensitive) to its edge-tts id; any other value is passed straight through as a voice id."""
    if not name:
        return DEFAULT_VOICE
    return VOICES.get(name.lower(), name)


def cues_of(srt):
    out = []
    for block in open(srt, encoding="utf8").read().strip().split("\n\n"):
        lines = block.strip().split("\n")
        if len(lines) < 3:
            continue
        g = re.match(r"(\d+):(\d+):(\d+)[,.](\d+) --> (\d+):(\d+):(\d+)[,.](\d+)", lines[1]).groups()
        t = lambda h, m, s, ms: int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000
        out.append({"start": round(t(*g[:4]), 3), "end": round(t(*g[4:]), 3), "text": " ".join(lines[2:])})
    return out


def length(mp3, cues):
    if shutil.which("ffprobe"):
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp3], capture_output=True, text=True)
        if r.stdout.strip():
            return round(float(r.stdout.strip()), 3)
    return cues[-1]["end"] if cues else 0.0


def narrate(text, mp3, force=False, voice=DEFAULT_VOICE, rate=RATE):
    """mp3 plus its sentence timings (kept beside it as .json); re-made only when missing or forced"""
    meta = os.path.splitext(mp3)[0] + ".json"
    if not force and os.path.exists(mp3) and os.path.exists(meta):
        return json.load(open(meta, encoding="utf8"))
    os.makedirs(os.path.dirname(os.path.abspath(mp3)), exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        srt = os.path.join(tmp, "s.srt")
        subprocess.run([sys.executable, "-m", "edge_tts", "--voice", voice, f"--rate={rate}", "--text", text,
                        "--write-media", mp3, "--write-subtitles", srt], check=True)
        cues = cues_of(srt)
    timing = {"dur": length(mp3, cues), "cues": cues}
    json.dump(timing, open(meta, "w", encoding="utf8"), indent=1, ensure_ascii=False)
    return timing


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("text", nargs="?", help="the text to say (or --file / --json)")
    p.add_argument("out", help="the mp3 to write, or a folder with --json")
    p.add_argument("--file", help="read the text from this file")
    p.add_argument("--json", help="many clips: a JSON list of {id, text} (each may also set its own \"voice\"/\"rate\")")
    p.add_argument("--voice", default=DEFAULT_VOICE, help="preset (ryan/sonia/aria) or any edge-tts voice id (default: the house Ryan voice)")
    p.add_argument("--rate", default=RATE, help='speaking rate, e.g. "-4%%" (default) or "+0%%"')
    p.add_argument("--force", action="store_true", help="re-make clips that already exist")
    a = p.parse_args()
    voice = resolve_voice(a.voice)
    if a.json:
        all_ = {}
        for c in json.load(open(a.json, encoding="utf8")):
            cv = resolve_voice(c["voice"]) if c.get("voice") else voice
            all_[c["id"]] = t = narrate(c["text"], os.path.join(a.out, f"{c['id']}.mp3"), a.force, cv, c.get("rate", a.rate))
            print(c["id"], t["dur"], "s,", len(t["cues"]), "sentences")
        json.dump(all_, open(os.path.join(a.out, "timing.json"), "w", encoding="utf8"), indent=1, ensure_ascii=False)
    else:
        text = open(a.file, encoding="utf8").read().strip() if a.file else a.text
        if not text:
            p.error("give the text, --file or --json")
        t = narrate(text, a.out, a.force, voice, a.rate)
        print(a.out, t["dur"], "s")
        for c in t["cues"]:
            print(f"  {c['start']:7.3f}  {c['text']}")
