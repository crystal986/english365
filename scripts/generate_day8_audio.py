#!/usr/bin/env python3
"""Generate verified Kokoro-82M lesson audio. No synthetic placeholders."""
import hashlib, json, math, os, subprocess, tempfile, wave, audioop
from pathlib import Path
import numpy as np
from kokoro import KPipeline
DAY=8
TEXTS={
 "audio/day8_main_slow.mp3":"How are you?",
 "audio/day8_example1_slow.mp3":"Hi, how are you?",
 "audio/day8_example2_slow.mp3":"Good morning! How are you today?",
 "audio/day8_example3_slow.mp3":"How are you, Mrs. Lee?",
}
pipeline=KPipeline(lang_code="a",repo_id="hexgrad/Kokoro-82M")
manifest=[]
for path,text in TEXTS.items():
    chunks=[audio for _,_,audio in pipeline(text,voice="af_heart",speed=0.75)]
    if not chunks: raise RuntimeError("No Kokoro inference output: "+text)
    pcm=np.concatenate([np.asarray(c,dtype=np.float32).reshape(-1) for c in chunks])
    if not np.isfinite(pcm).all() or np.sqrt(np.mean(pcm**2))<0.001: raise RuntimeError("Invalid/silent synthesis: "+text)
    output=Path(path);output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        import soundfile as sf
        sf.write(tmp.name,pcm,24000,subtype="PCM_16")
        subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",tmp.name,"-ac","1","-ar","24000","-b:a","128k",str(output)],check=True)
    probe=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_entries","stream=codec_name,sample_rate,channels:format=duration","-of","json",str(output)]))
    stream=probe["streams"][0]
    if stream["codec_name"]!="mp3" or int(stream["sample_rate"])!=24000 or int(stream["channels"])!=1: raise RuntimeError("MP3 format mismatch")
    duration=float(probe["format"]["duration"])
    if not 0.4<duration<30: raise RuntimeError("Implausible duration")
    decoded=subprocess.check_output(["ffmpeg","-v","error","-i",str(output),"-f","f32le","-ac","1","-ar","24000","pipe:1"])
    signal=np.frombuffer(decoded,dtype=np.float32)
    rms=float(np.sqrt(np.mean(signal**2)))
    if rms<0.001: raise RuntimeError("Silent decoded MP3")
    manifest.append(dict(day=DAY,text=text,voice="af_heart",model="hexgrad/Kokoro-82M",speed=0.75,path=path,duration=duration,rms=rms,bytes=output.stat().st_size,sha256=hashlib.sha256(output.read_bytes()).hexdigest()))
Path("audio/day8_manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("Generated and verified",len(manifest),"MP3s")
