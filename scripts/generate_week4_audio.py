#!/usr/bin/env python3
"""Generate real Kokoro-82M slow-only Week 4 MP3s, with audio integrity manifest."""
import hashlib,json,subprocess,tempfile
from pathlib import Path
import numpy as np
import soundfile as sf
from kokoro import KPipeline
TEXTS={
    "audio/day22_main_slow.mp3": "morning",
    "audio/day22_example1_slow.mp3": "Good morning!",
    "audio/day22_example2_slow.mp3": "I walk every morning.",
    "audio/day22_example3_slow.mp3": "My appointment is in the morning.",
    "audio/day23_main_slow.mp3": "afternoon",
    "audio/day23_example1_slow.mp3": "Good afternoon!",
    "audio/day23_example2_slow.mp3": "See you this afternoon.",
    "audio/day23_example3_slow.mp3": "The class is in the afternoon.",
    "audio/day24_main_slow.mp3": "evening",
    "audio/day24_example1_slow.mp3": "Good evening!",
    "audio/day24_example2_slow.mp3": "I cook in the evening.",
    "audio/day24_example3_slow.mp3": "The meeting is this evening.",
    "audio/day25_main_slow.mp3": "night",
    "audio/day25_example1_slow.mp3": "Good night!",
    "audio/day25_example2_slow.mp3": "I sleep well at night.",
    "audio/day25_example3_slow.mp3": "It is cold at night.",
    "audio/day26_main_slow.mp3": "today",
    "audio/day26_example1_slow.mp3": "I feel good today.",
    "audio/day26_example2_slow.mp3": "Is the clinic open today?",
    "audio/day26_example3_slow.mp3": "Today is a sunny day.",
    "audio/day27_main_slow.mp3": "tomorrow",
    "audio/day27_example1_slow.mp3": "See you tomorrow!",
    "audio/day27_example2_slow.mp3": "I have a class tomorrow.",
    "audio/day27_example3_slow.mp3": "Will it rain tomorrow?",
    "audio/day28_main_slow.mp3": "yesterday",
    "audio/day28_example1_slow.mp3": "I went shopping yesterday.",
    "audio/day28_example2_slow.mp3": "It rained yesterday.",
    "audio/day28_example3_slow.mp3": "I called the clinic yesterday."
}
pipeline=KPipeline(lang_code="a",repo_id="hexgrad/Kokoro-82M")
manifest=[]
for path,text in TEXTS.items():
    chunks=[np.asarray(a,dtype=np.float32).reshape(-1) for _,_,a in pipeline(text,voice="af_heart",speed=0.75)]
    if not chunks:raise RuntimeError("Empty synthesis "+path)
    pcm=np.concatenate(chunks)
    if not np.isfinite(pcm).all() or float(np.sqrt(np.mean(pcm**2)))<0.001:raise RuntimeError("Invalid PCM "+path)
    out=Path(path);out.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        sf.write(tmp.name,pcm,24000,subtype="PCM_16")
        subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",tmp.name,"-ac","1","-ar","24000","-b:a","128k",str(out)],check=True)
    probe=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_entries","stream=codec_name,sample_rate,channels:format=duration","-of","json",str(out)]))
    stream=probe["streams"][0]
    if stream["codec_name"]!="mp3" or int(stream["sample_rate"])!=24000 or int(stream["channels"])!=1:raise RuntimeError("Invalid codec "+path)
    duration=float(probe["format"]["duration"])
    if not .4<duration<30:raise RuntimeError("Invalid duration "+path)
    decoded=subprocess.check_output(["ffmpeg","-v","error","-i",str(out),"-f","f32le","-ac","1","-ar","24000","pipe:1"])
    rms=float(np.sqrt(np.mean(np.frombuffer(decoded,dtype=np.float32)**2)))
    if rms<.001:raise RuntimeError("Silent MP3 "+path)
    manifest.append(dict(day=int(path.split("day")[1].split("_")[0]),text=text,voice="af_heart",model="hexgrad/Kokoro-82M",speed=.75,path=path,duration=duration,rms=rms,bytes=out.stat().st_size,sha256=hashlib.sha256(out.read_bytes()).hexdigest()))
Path("audio/week4_manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("Verified",len(manifest),"MP3 files")
