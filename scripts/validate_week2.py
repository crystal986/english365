#!/usr/bin/env python3
"""Check Day 9–14 HTML and 24 generated audio files before publication."""
import hashlib, json, re, subprocess
from pathlib import Path
manifest=json.loads(Path("audio/week2_manifest.json").read_text(encoding="utf-8"))
assert len(manifest)==24
items={x["path"]:x for x in manifest}
assert len(items)==24
for n in range(9,15):
    html=Path(f"day{n}.html").read_text(encoding="utf-8")
    refs=re.findall(r'data-audio="([^"]+)"',html)
    assert len(refs)==(11 if n==14 else 4),(n,len(refs))
    assert len(set(refs))==len(refs) if n!=14 else len(set(refs))==11
    assert all("slow.mp3" in p for p in refs)
    assert "speechSynthesis" not in html
    assert "course.html" in html
    for p in refs:
        assert p in items or p=="audio/day8_main_slow.mp3",(n,p)
    if n==14:
        assert html.index("第一部分")<html.index("第二部分")<html.index("第三部分")
        assert len(re.findall(r'<fieldset class="card">',html))==7
for item in manifest:
    p=Path(item["path"])
    assert p.is_file() and p.stat().st_size>2000,item["path"]
    assert p.stat().st_size==item["bytes"]
    assert hashlib.sha256(p.read_bytes()).hexdigest()==item["sha256"]
    assert item["voice"]=="af_heart" and item["speed"]==0.75
    subprocess.run(["ffmpeg","-v","error","-i",str(p),"-f","null","-"],check=True)
index=Path("course.html").read_text(encoding="utf-8")
for n in range(9,15):assert f"href:'day{n}.html'" in index
print("Week 2 validation passed: 6 lessons, 24 MP3, 7 reviews, 7 quiz questions")
