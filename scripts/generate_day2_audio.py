#!/usr/bin/env python3
"""Synthesize and validate six Day 2 Kokoro af_heart MP3 files."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

import numpy as np
import soundfile as sf
from kokoro import KPipeline

ROOT = Path(__file__).resolve().parents[1]
PHRASES = {
    "day2_thank_you": "Thank you!",
    "day2_thank_you_mary": "Thank you, Mary!",
    "day2_thank_you_very_much": "Thank you very much!",
}
SPEEDS = {"normal": 1.0, "slow": 0.75}

def verify(path):
    probe = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)
    ]))
    stream = next(s for s in probe["streams"] if s["codec_type"] == "audio")
    raw = subprocess.check_output([
        "ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "1", "-ar", "24000", "-"
    ])
    samples = np.frombuffer(raw, dtype="<f4")
    duration = float(probe["format"]["duration"])
    rms = float(np.sqrt(np.mean(samples ** 2))) if len(samples) else 0.0
    if (stream["codec_name"] != "mp3" or int(stream["sample_rate"]) != 24000
            or path.stat().st_size < 2500 or not 0.3 < duration < 20
            or not np.isfinite(samples).all() or rms < 0.002):
        raise RuntimeError(f"Audio validation failed: {path}")
    return {"duration": duration, "rms": rms, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "decoded_sha256": hashlib.sha256(raw).hexdigest(), "bytes": path.stat().st_size}

def main():
    html = (ROOT / "day2.html").read_text(encoding="utf-8")
    if 'id="day2-player"' not in html:
        raise RuntimeError("Day 2 HTML player missing")
    pipeline = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M", device="cpu")
    results = {}
    with tempfile.TemporaryDirectory() as temp:
        stage = Path(temp)
        for stem, phrase in PHRASES.items():
            for label, speed in SPEEDS.items():
                name = f"{stem}_{label}.mp3"
                if f'audio/{name}' not in html:
                    raise RuntimeError(f"HTML is missing {name}")
                chunks = [audio.detach().cpu().numpy() for _, _, audio in
                          pipeline(phrase, voice="af_heart", speed=speed) if audio is not None]
                if not chunks:
                    raise RuntimeError(f"No audio for {phrase}")
                wav = stage / f"{stem}_{label}.wav"
                mp3 = stage / name
                sf.write(wav, np.concatenate(chunks), 24000)
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(wav),
                                "-codec:a", "libmp3lame", "-b:a", "128k", str(mp3)], check=True)
                results[name] = {"text": phrase, "speed": speed, **verify(mp3)}
                print("PASS", name, results[name]["duration"], flush=True)
        if len(results) != 6:
            raise RuntimeError("Expected exactly six MP3 files")
        for field in ("sha256", "decoded_sha256"):
            if len({item[field] for item in results.values()}) != 6:
                raise RuntimeError(f"Duplicate audio detected: {field}")
        for stem in PHRASES:
            if results[f"{stem}_slow.mp3"]["duration"] <= results[f"{stem}_normal.mp3"]["duration"]:
                raise RuntimeError(f"Slow audio not longer: {stem}")
        out = ROOT / "audio"
        out.mkdir(exist_ok=True)
        for name in results:
            if (out / name).exists():
                raise RuntimeError(f"Refusing to overwrite existing {name}")
        for name in results:
            (out / name).write_bytes((stage / name).read_bytes())
        (out / "day2_validation.json").write_text(json.dumps({
            "model": "hexgrad/Kokoro-82M", "voice": "af_heart",
            "listening_verified": False, "files": results
        }, indent=2), encoding="utf-8")
    print("SUCCESS: all six Day 2 MP3s validated", flush=True)

if __name__ == "__main__":
    main()
