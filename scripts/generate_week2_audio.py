#!/usr/bin/env python3
"""Generate real Kokoro-82M MP3 audio for Day 9–14; verify codec and decoded RMS."""
import hashlib, json, subprocess, tempfile
from pathlib import Path
import numpy as np
import soundfile as sf
from kokoro import KPipeline

TEXTS = {
    "audio/day9_main_slow.mp3": "I'm good, thank you.",
    "audio/day9_example1_slow.mp3": "I'm good, thank you.",
    "audio/day9_example2_slow.mp3": "I'm good. How about you?",
    "audio/day9_example3_slow.mp3": "I'm good, thanks for asking.",
    "audio/day10_main_slow.mp3": "Nice to meet you.",
    "audio/day10_example1_slow.mp3": "Hi, nice to meet you.",
    "audio/day10_example2_slow.mp3": "Nice to meet you, Anna.",
    "audio/day10_example3_slow.mp3": "It's nice to meet you.",
    "audio/day11_main_slow.mp3": "My name is...",
    "audio/day11_example1_slow.mp3": "My name is Li.",
    "audio/day11_example2_slow.mp3": "Hello, my name is Mei.",
    "audio/day11_example3_slow.mp3": "My name is Chen. Nice to meet you.",
    "audio/day12_main_slow.mp3": "What's your name?",
    "audio/day12_example1_slow.mp3": "Hi, what's your name?",
    "audio/day12_example2_slow.mp3": "Sorry, what's your name again?",
    "audio/day12_example3_slow.mp3": "May I have your name, please?",
    "audio/day13_main_slow.mp3": "Where are you from?",
    "audio/day13_example1_slow.mp3": "Where are you from?",
    "audio/day13_example2_slow.mp3": "I'm from China.",
    "audio/day13_example3_slow.mp3": "I'm from Vancouver.",
    "audio/day14_main_slow.mp3": "I live in Canada.",
    "audio/day14_example1_slow.mp3": "I live in Canada.",
    "audio/day14_example2_slow.mp3": "I live in Nanaimo.",
    "audio/day14_example3_slow.mp3": "My family lives in Canada.",
}
pipeline = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M")
manifest = []
for path, text in TEXTS.items():
    chunks = [np.asarray(audio, dtype=np.float32).reshape(-1) for _, _, audio in pipeline(text, voice="af_heart", speed=0.75)]
    if not chunks: raise RuntimeError("No generated audio: " + text)
    pcm = np.concatenate(chunks)
    if not np.isfinite(pcm).all() or float(np.sqrt(np.mean(pcm**2))) < 0.001:
        raise RuntimeError("Silent or invalid inference: " + text)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".wav") as wav:
        sf.write(wav.name, pcm, 24000, subtype="PCM_16")
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", wav.name, "-ac", "1", "-ar", "24000", "-b:a", "128k", str(target)], check=True)
    probe = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "stream=codec_name,sample_rate,channels:format=duration", "-of", "json",str(target)]))
    stream = probe["streams"][0]
    if stream["codec_name"] != "mp3" or int(stream["sample_rate"]) != 24000 or int(stream["channels"]) != 1:
        raise RuntimeError("MP3 format mismatch: " + path)
    duration = float(probe["format"]["duration"])
    if not 0.4 < duration < 30: raise RuntimeError("Invalid duration: " + path)
    decoded = subprocess.check_output(["ffmpeg", "-v", "error", "-i", str(target), "-f", "f32le", "-ac", "1", "-ar", "24000", "pipe:1"])
    rms = float(np.sqrt(np.mean(np.frombuffer(decoded, dtype=np.float32)**2)))
    if rms < 0.001: raise RuntimeError("Decoded silence: " + path)
    manifest.append(dict(day=int(path.split("day")[1].split("_")[0]), text=text, voice="af_heart", model="hexgrad/Kokoro-82M", speed=0.75, path=path, duration=duration, rms=rms, bytes=target.stat().st_size, sha256=hashlib.sha256(target.read_bytes()).hexdigest()))
Path("audio/week2_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
print("Generated and verified",len(manifest),"MP3 files")
