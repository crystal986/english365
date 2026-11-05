#!/usr/bin/env python3
"""Generate real Kokoro-82M slow-only Week 3 MP3s, with audio integrity manifest."""
import hashlib,json,subprocess,tempfile
from pathlib import Path
import numpy as np
import soundfile as sf
from kokoro import KPipeline
TEXTS={
    "audio/day15_main_slow.mp3": "hi",
    "audio/day15_example1_slow.mp3": "Hi, Mary!",
    "audio/day15_example2_slow.mp3": "Hi, how are you?",
    "audio/day15_example3_slow.mp3": "Hi, nice to see you.",
    "audio/day16_main_slow.mp3": "bye",
    "audio/day16_example1_slow.mp3": "Bye, see you tomorrow.",
    "audio/day16_example2_slow.mp3": "Bye, have a nice day.",
    "audio/day16_example3_slow.mp3": "Bye, take care.",
    "audio/day17_main_slow.mp3": "yes",
    "audio/day17_example1_slow.mp3": "Yes, please.",
    "audio/day17_example2_slow.mp3": "Yes, this is my card.",
    "audio/day17_example3_slow.mp3": "Yes, I have an appointment.",
    "audio/day18_main_slow.mp3": "no",
    "audio/day18_example1_slow.mp3": "No, thank you.",
    "audio/day18_example2_slow.mp3": "No, I don't need a receipt.",
    "audio/day18_example3_slow.mp3": "No, this is not my bag.",
    "audio/day19_main_slow.mp3": "thanks",
    "audio/day19_example1_slow.mp3": "Thanks for your help.",
    "audio/day19_example2_slow.mp3": "Thanks, that's very kind.",
    "audio/day19_example3_slow.mp3": "Thanks, see you next week.",
    "audio/day20_main_slow.mp3": "okay",
    "audio/day20_example1_slow.mp3": "Okay, I understand.",
    "audio/day20_example2_slow.mp3": "Okay, I'll wait here.",
    "audio/day20_example3_slow.mp3": "Is ten o'clock okay?",
    "audio/day21_main_slow.mp3": "good",
    "audio/day21_example1_slow.mp3": "This coffee is good.",
    "audio/day21_example2_slow.mp3": "That's a good idea.",
    "audio/day21_example3_slow.mp3": "I feel good today."
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
Path("audio/week3_manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("Verified",len(manifest),"MP3 files")
