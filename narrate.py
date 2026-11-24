"""Narration in the house voice (edge-tts en-GB-RyanNeural, rate -4%), with per-sentence timings.
    python narrate.py "Text to say." out/intro.mp3
    python narrate.py --file script.txt out/intro.mp3
    python narrate.py --json clips.json out/voice/       clips.json: [{"id": "s01", "text": "..."}, ...]
    python narrate.py --voice sonia "Text to say." out/intro.mp3    presets: ryan (default, house voice), sonia, aria; or any edge-tts voice id
Writes <name>.mp3 and <name>.json ({"dur", "cues": [{"start", "end", "text"}], "key"}); --json also timing.json.
A --json clip may carry its own "voice"/"rate" (e.g. alternating speakers). A clip is re-made only when its
text, voice or rate changed (or with --force). --json makes several clips at once (--jobs, default 4).
"""
import argparse, glob, hashlib, json, os, re, shutil, subprocess, sys, tempfile, time
from concurrent.futures import ThreadPoolExecutor

# The house voice is Ryan. Alternates can be chosen with --voice (a preset name below, or any edge-tts voice id).
VOICES = {
    "ryan": "en-GB-RyanNeural",    # house voice: calm British male
    "sonia": "en-GB-SoniaNeural",  # British female
    "aria": "en-US-AriaNeural",    # US female
}
DEFAULT_VOICE, RATE = "en-GB-RyanNeural", "-4%"
ATTEMPTS = 4  # edge-tts is an online service; a dropped connection is retried with a growing pause


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


def ffprobe():
    """ffprobe on PATH, or where winget puts FFmpeg on Windows (PATH only updates in a new terminal)."""
    found = shutil.which("ffprobe")
    if found:
        return found
    local = os.environ.get("LOCALAPPDATA")
    if local:
        for pattern in (r"Microsoft\WinGet\Links\ffprobe.exe", r"Microsoft\WinGet\Packages\Gyan.FFmpeg*\*\bin\ffprobe.exe"):
            hits = glob.glob(os.path.join(local, pattern))
            if hits:
                return hits[0]
    return None


def length(mp3, cues):
    probe = ffprobe()
    if probe:
        r = subprocess.run([probe, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp3], capture_output=True, text=True)
        if r.stdout.strip():
            return round(float(r.stdout.strip()), 3)
    # edge-tts writes 48 kbit/s constant-bitrate mp3, so the size gives the length, including the trailing pause.
    estimate = os.path.getsize(mp3) * 8 / 48000
    return round(max(estimate, cues[-1]["end"] if cues else 0.0), 3)


def key_of(text, voice, rate):
    return hashlib.sha256(f"{voice}|{rate}|{text}".encode("utf8")).hexdigest()[:16]


def narrate(text, mp3, force=False, voice=DEFAULT_VOICE, rate=RATE):
    """mp3 plus its sentence timings (kept beside it as .json); re-made only when the words, voice or rate changed"""
    meta = os.path.splitext(mp3)[0] + ".json"
    key = key_of(text, voice, rate)
    if not force and os.path.exists(mp3) and os.path.exists(meta):
        old = json.load(open(meta, encoding="utf-8-sig"))
        if old.get("key", key) == key:  # files from before keys existed are trusted
            return old
    os.makedirs(os.path.dirname(os.path.abspath(mp3)), exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        srt, part = os.path.join(tmp, "s.srt"), os.path.join(tmp, "a.mp3")
        for attempt in range(1, ATTEMPTS + 1):
            r = subprocess.run([sys.executable, "-m", "edge_tts", "--voice", voice, f"--rate={rate}", "--text", text,
                                "--write-media", part, "--write-subtitles", srt], capture_output=True, text=True)
            if r.returncode == 0 and os.path.exists(part) and os.path.getsize(part) > 0:
                break
            if attempt == ATTEMPTS:
                raise RuntimeError(f"edge-tts failed for {mp3}: {r.stderr.strip()[-400:]}")
            time.sleep(3 * attempt)
        cues = cues_of(srt)
        shutil.move(part, mp3)  # only a finished clip replaces the old one
    timing = {"dur": length(mp3, cues), "cues": cues, "key": key}
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
    p.add_argument("--jobs", type=int, default=4, help="clips made at the same time with --json (default 4)")
    p.add_argument("--force", action="store_true", help="re-make clips even when nothing changed")
    a = p.parse_args()
    voice = resolve_voice(a.voice)
    if a.json:
        clips = json.load(open(a.json, encoding="utf-8-sig"))  # utf-8-sig: Windows tools often add a BOM

        def make(c):
            cv = resolve_voice(c["voice"]) if c.get("voice") else voice
            return c["id"], narrate(c["text"], os.path.join(a.out, f"{c['id']}.mp3"), a.force, cv, c.get("rate", a.rate))

        with ThreadPoolExecutor(max(1, a.jobs)) as pool:
            done = dict(pool.map(make, clips))
        for c in clips:
            t = done[c["id"]]
            print(c["id"], t["dur"], "s,", len(t["cues"]), "sentences")
        json.dump({c["id"]: done[c["id"]] for c in clips}, open(os.path.join(a.out, "timing.json"), "w", encoding="utf8"), indent=1, ensure_ascii=False)
        print(f"{len(clips)} clips, {sum(t['dur'] for t in done.values()) / 60:.1f} minutes of speech")
    else:
        text = open(a.file, encoding="utf-8-sig").read().strip() if a.file else a.text
        if not text:
            p.error("give the text, --file or --json")
        t = narrate(text, a.out, a.force, voice, a.rate)
        print(a.out, t["dur"], "s")
        for c in t["cues"]:
            print(f"  {c['start']:7.3f}  {c['text']}")
