from pathlib import Path
import subprocess, json, tempfile, hashlib
import numpy as np
import soundfile as sf
from kokoro import KPipeline
root=Path(__file__).resolve().parents[1]
out=root/"audio"
out.mkdir(exist_ok=True)
phrase="Thank you very much!"
pipeline=KPipeline(lang_code="a",repo_id="hexgrad/Kokoro-82M",device="cpu")
result={}
with tempfile.TemporaryDirectory() as td:
 for label,speed in [("05",0.5),("075",0.75)]:
  chunks=[audio.detach().cpu().numpy() for _,_,audio in pipeline(phrase,voice="af_heart",speed=speed) if audio is not None]
  if not chunks: raise RuntimeError("Empty synthesis")
  wav=Path(td)/(label+".wav")
  sf.write(wav,np.concatenate(chunks),24000)
  mp3=out/("compare_thank_you_very_much_"+label+".mp3")
  subprocess.run(["ffmpeg","-v","error","-y","-i",str(wav),"-codec:a","libmp3lame","-b:a","128k",str(mp3)],check=True)
  meta=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_streams","-show_format","-of","json",str(mp3)]))
  stream=next(s for s in meta["streams"] if s["codec_type"]=="audio")
  decoded=np.frombuffer(subprocess.check_output(["ffmpeg","-v","error","-i",str(mp3),"-f","f32le","-ar","24000","-ac","1","-"]),dtype="<f4")
  rms=float(np.sqrt(np.mean(decoded*decoded)))
  duration=float(meta["format"]["duration"])
  if stream["codec_name"]!="mp3" or int(stream["sample_rate"])!=24000 or not 0.4<duration<25 or rms<0.002 or mp3.stat().st_size<2500: raise RuntimeError("Invalid MP3")
  result[label]={"speed":speed,"duration_seconds":duration,"rms":rms,"bytes":mp3.stat().st_size,"sha256":hashlib.sha256(mp3.read_bytes()).hexdigest()}
if result["05"]["duration_seconds"]<=result["075"]["duration_seconds"]: raise RuntimeError("0.5 must be longer than 0.75")
(out/"compare_speed_validation.json").write_text(json.dumps({"model":"hexgrad/Kokoro-82M","voice":"af_heart","text":phrase,"results":result},indent=2))
print("PASS",result)
