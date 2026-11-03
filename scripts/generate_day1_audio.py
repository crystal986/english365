#!/usr/bin/env python3
"""Generate and validate six Kokoro af_heart Day 1 MP3s."""
import pathlib, subprocess
import numpy as np
import soundfile as sf
from kokoro import KPipeline

out = pathlib.Path("audio")
out.mkdir(exist_ok=True)
pipeline = KPipeline(lang_code="a")
phrases = {
    "hello": "Hello!",
    "hello_mary": "Hello, Mary!",
    "hello_everyone": "Hello, everyone!",
}
for stem, text in phrases.items():
    for label, speed in (("normal", 1.0), ("slow", 0.75)):
        filename = out / f"{stem}_{label}.mp3"
        pieces = [np.asarray(audio, dtype=np.float32) for _, _, audio in pipeline(text, voice="af_heart", speed=speed)]
        if not pieces:
            raise RuntimeError(f"No generated audio: {text}")
        audio = np.concatenate(pieces)
        if len(audio) < 6000 or float(np.sqrt(np.mean(audio**2))) < 0.002:
            raise RuntimeError(f"Empty or silent output: {filename}")
        wav = filename.with_suffix(".wav")
        sf.write(wav, audio, 24000)
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(wav), "-codec:a", "libmp3lame", "-qscale:a", "3", str(filename)], check=True)
        wav.unlink()
        if filename.stat().st_size < 2500:
            raise RuntimeError(f"MP3 unexpectedly small: {filename}")
        probe = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(filename)], text=True)
        duration = float(probe.strip())
        if duration < 0.25:
            raise RuntimeError(f"MP3 duration invalid: {filename}")
        print(f"PASS {filename} {filename.stat().st_size} bytes {duration:.2f}s")
assert len(list(out.glob("*.mp3"))) == 6
print("SUCCESS: all six MP3 files generated and structurally verified.")
