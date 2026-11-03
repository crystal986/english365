#!/usr/bin/env python3
"""Generate and validate one Kokoro af_heart slow example for Day 7."""
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path
import numpy as np
import soundfile as sf
from kokoro import KPipeline

ROOT = Path(__file__).resolve().parents[1]
NAME = "day7_goodbye_example_slow.mp3"
TEXT = "Goodbye! See you tomorrow."
DEST = ROOT / "audio" / NAME

def main():
    if DEST.exists():
        raise RuntimeError("Refusing to overwrite existing MP3")
    html = (ROOT / "day7.html").read_text(encoding="utf-8")
    if "audio/" + NAME not in html:
        raise RuntimeError("Day 7 does not reference the generated example")
    pipeline = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M", device="cpu")
    parts = [audio.detach().cpu().numpy() for _, _, audio in pipeline(TEXT, voice="af_heart", speed=0.75) if audio is not None]
    if not parts:
        raise RuntimeError("Empty Kokoro output")
    with tempfile.TemporaryDirectory() as temp:
        wav = Path(temp) / "example.wav"
        mp3 = Path(temp) / NAME
        sf.write(wav, np.concatenate(parts), 24000)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(wav), "-codec:a", "libmp3lame", "-b:a", "128k", str(mp3)], check=True)
        meta = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(mp3)]))
        stream = next(x for x in meta["streams"] if x["codec_type"] == "audio")
        samples = np.frombuffer(subprocess.check_output(["ffmpeg", "-v", "error", "-i", str(mp3), "-f", "f32le", "-ar", "24000", "-ac", "1", "-"]), dtype="<f4")
        duration = float(meta["format"]["duration"])
        rms = float(np.sqrt(np.mean(samples * samples))) if samples.size else 0
        if stream["codec_name"] != "mp3" or int(stream["sample_rate"]) != 24000 or not 0.3 < duration < 25 or rms < 0.002 or not np.isfinite(samples).all() or mp3.stat().st_size < 2500:
            raise RuntimeError("Audio verification failed")
        DEST.parent.mkdir(exist_ok=True)
        DEST.write_bytes(mp3.read_bytes())
        validation = {"model":"hexgrad/Kokoro-82M","voice":"af_heart","text":TEXT,"speed":0.75,"file":NAME,"duration":duration,"rms":rms,"bytes":DEST.stat().st_size,"sha256":hashlib.sha256(DEST.read_bytes()).hexdigest()}
        (ROOT / "audio" / "day7_goodbye_example_validation.json").write_text(json.dumps(validation, indent=2) + "\n", encoding="utf-8")
        print("PASS: validated real Kokoro example", validation, flush=True)

if __name__ == "__main__":
    main()
