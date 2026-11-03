#!/usr/bin/env python3
"""Generate real Kokoro af_heart MP3 for Days 3-7; validate before committing."""
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path
import numpy as np
import soundfile as sf
from kokoro import KPipeline

ROOT=Path(__file__).resolve().parents[1]
PHRASES={
3:["Please.","Coffee, please.","One bag, please."],
4:["Excuse me.","Excuse me, please.","Excuse me, where is the bus stop?"],
5:["Sorry.","I'm sorry.","Sorry, I'm late."],
6:["You're welcome.","You're very welcome.","Thank you. You're welcome."],
7:["Hello!","Thank you!","Please.","Excuse me.","Sorry.","You're welcome.","Goodbye!"]
}
SPEEDS={"normal":1.0,"slow":0.75}
def check(path):
    data=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_streams","-show_format","-of","json",str(path)]))
    stream=next(s for s in data["streams"] if s["codec_type"]=="audio")
    raw=subprocess.check_output(["ffmpeg","-v","error","-i",str(path),"-f","f32le","-ar","24000","-ac","1","-"])
    samples=np.frombuffer(raw,dtype="<f4")
    duration=float(data["format"]["duration"])
    rms=float(np.sqrt(np.mean(samples*samples))) if samples.size else 0
    if stream["codec_name"]!="mp3" or int(stream["sample_rate"])!=24000 or not 0.3<duration<25 or rms<0.002 or not np.isfinite(samples).all() or path.stat().st_size<2500:
        raise RuntimeError(f"MP3 validation failed: {path}")
    return {"duration":duration,"rms":rms,"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"bytes":path.stat().st_size}
def main():
    pipeline=KPipeline(lang_code="a",repo_id="hexgrad/Kokoro-82M",device="cpu")
    results={}
    with tempfile.TemporaryDirectory() as tmp:
        stage=Path(tmp)
        for day,phrases in PHRASES.items():
            html=(ROOT/f"day{day}.html").read_text(encoding="utf-8")
            for i,phrase in enumerate(phrases,1):
                for label,speed in SPEEDS.items():
                    name=f"day7_review_{i}_{label}.mp3" if day==7 else f"day{day}_{i}_{label}.mp3"
                    if f"audio/{name}" not in html: raise RuntimeError(f"Missing HTML reference: {name}")
                    parts=[audio.detach().cpu().numpy() for _,_,audio in pipeline(phrase,voice="af_heart",speed=speed) if audio is not None]
                    if not parts: raise RuntimeError(f"Empty Kokoro output: {name}")
                    wav=stage/(name+".wav")
                    sf.write(wav,np.concatenate(parts),24000)
                    mp3=stage/name
                    subprocess.run(["ffmpeg","-v","error","-y","-i",str(wav),"-codec:a","libmp3lame","-b:a","128k",str(mp3)],check=True)
                    results[name]={"day":day,"text":phrase,"speed":speed,**check(mp3)}
                    print("PASS",name,results[name]["duration"],flush=True)
        if len(results)!=38: raise RuntimeError("Expected exactly 38 MP3s")
        if len({x["sha256"] for x in results.values()})!=38: raise RuntimeError("Duplicate MP3 output")
        for day,phrases in PHRASES.items():
            for i,_ in enumerate(phrases,1):
                stem=f"day7_review_{i}" if day==7 else f"day{day}_{i}"
                if results[stem+"_slow.mp3"]["duration"]<=results[stem+"_normal.mp3"]["duration"]:
                    raise RuntimeError(f"Slow version is not longer: {stem}")
        dest=ROOT/"audio"
        dest.mkdir(exist_ok=True)
        for name in results:
            if (dest/name).exists(): raise RuntimeError(f"Refusing overwrite: {name}")
        for name in results:(dest/name).write_bytes((stage/name).read_bytes())
        (dest/"week1_days3_7_validation.json").write_text(json.dumps({"model":"hexgrad/Kokoro-82M","voice":"af_heart","files":results},ensure_ascii=False,indent=2),encoding="utf-8")
    print("SUCCESS: all 38 real Kokoro MP3s verified",flush=True)
if __name__=="__main__":main()
