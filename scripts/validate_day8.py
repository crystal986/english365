#!/usr/bin/env python3
"""Fail closed if Day 8 page/audio/manifest disagree."""
import hashlib,json,re,subprocess,sys
from html.parser import HTMLParser
from pathlib import Path
class Parser(HTMLParser):
 def __init__(self): super().__init__();self.audios=[];self.buttons=0;self.tts=False
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=="button" and "data-audio" in a:self.buttons+=1;self.audios.append(a["data-audio"])
p=Path("day8.html");assert p.exists(),"Day 8 missing"
html=p.read_text(encoding="utf-8");parser=Parser();parser.feed(html)
assert "speechSynthesis" not in html and "normal.mp3" not in html and "0.5" not in html
assert parser.buttons==4 and len(set(parser.audios))==4
assert html.count('class="pron"')==4 and html.count('class="cn"')==4
manifest=json.loads(Path("audio/day8_manifest.json").read_text())
assert len(manifest)==4 and set(parser.audios)=={m["path"] for m in manifest}
for m in manifest:
 assert m["day"]==8 and m["voice"]=="af_heart" and m["speed"]==0.75 and m["model"]=="hexgrad/Kokoro-82M"
 f=Path(m["path"]);assert f.exists() and f.stat().st_size==m["bytes"] and m["bytes"]>1000
 assert hashlib.sha256(f.read_bytes()).hexdigest()==m["sha256"]
 subprocess.run(["ffmpeg","-v","error","-xerror","-i",str(f),"-f","null","-"],check=True)
assert '8:{title:' in Path("course.html").read_text(), "Course index must be updated before publication"
print("Day 8 file, audio, metadata, and index checks passed")
