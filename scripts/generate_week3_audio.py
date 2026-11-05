#!/usr/bin/env python3
"""Generate real Kokoro-82M slow-only Week 3 MP3s, with audio integrity manifest."""
import hashlib,json,subprocess,tempfile
from pathlib import Path
import numpy as np
import soundfile as sf
from kokoro import KPipeline
TEXTS={
    "audio/day15_main_slow.mp3": "Where is the bus stop?",
    "audio/day15_example1_slow.mp3": "Where is the bus stop?",
    "audio/day15_example2_slow.mp3": "Is this the right bus stop?",
    "audio/day15_example3_slow.mp3": "Where can I catch the bus?",
    "audio/day16_main_slow.mp3": "Please help me.",
    "audio/day16_example1_slow.mp3": "Please help me with this bag.",
    "audio/day16_example2_slow.mp3": "Can you help me, please?",
    "audio/day16_example3_slow.mp3": "Please help me find the clinic.",
    "audio/day17_main_slow.mp3": "I don't understand.",
    "audio/day17_example1_slow.mp3": "Sorry, I don't understand.",
    "audio/day17_example2_slow.mp3": "I don't understand this form.",
    "audio/day17_example3_slow.mp3": "I don't understand English very well.",
    "audio/day18_main_slow.mp3": "Please speak slowly.",
    "audio/day18_example1_slow.mp3": "Please speak slowly.",
    "audio/day18_example2_slow.mp3": "Could you speak more slowly, please?",
    "audio/day18_example3_slow.mp3": "Please speak slowly. I'm learning English.",
    "audio/day19_main_slow.mp3": "Could you repeat that?",
    "audio/day19_example1_slow.mp3": "Could you repeat that, please?",
    "audio/day19_example2_slow.mp3": "Sorry, could you repeat that?",
    "audio/day19_example3_slow.mp3": "Could you repeat the address?",
    "audio/day20_main_slow.mp3": "Thank you for your help.",
    "audio/day20_example1_slow.mp3": "Thank you for your help.",
    "audio/day20_example2_slow.mp3": "Thank you for helping me.",
    "audio/day20_example3_slow.mp3": "Thank you for your time.",
    "audio/day21_main_slow.mp3": "You're welcome.",
    "audio/day21_example1_slow.mp3": "You're welcome.",
    "audio/day21_example2_slow.mp3": "You're very welcome.",
    "audio/day21_example3_slow.mp3": "No problem. You're welcome.",
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
