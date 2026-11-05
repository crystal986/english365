#!/usr/bin/env python3
"""Check Week 3 content, quiz, and all real slow MP3 files."""
import hashlib,json,re,subprocess
from pathlib import Path
m=json.loads(Path("audio/week3_manifest.json").read_text(encoding="utf-8"))
assert len(m)==28 and len({x["path"] for x in m})==28
paths={x["path"] for x in m}
for n in range(15,22):
    h=Path(f"day{n}.html").read_text(encoding="utf-8")
    refs=re.findall(r'data-audio="([^"]+)"',h)
    assert len(refs)==(11 if n==21 else 4),(n,len(refs))
    assert len(set(refs))==(10 if n==21 else 4)
    assert set(refs)<=paths
    assert "speechSynthesis" not in h
    assert "course.html" in h
    if n==21:
        assert h.index("第一部分")<h.index("第二部分")<h.index("第三部分")
        assert len(re.findall(r'<fieldset class="card">',h))==7
for x in m:
    p=Path(x["path"])
    assert p.is_file() and p.stat().st_size>2000
    assert x["bytes"]==p.stat().st_size
    assert x["sha256"]==hashlib.sha256(p.read_bytes()).hexdigest()
    assert x["speed"]==.75 and x["voice"]=="af_heart"
    subprocess.run(["ffmpeg","-v","error","-i",str(p),"-f","null","-"],check=True)
print("Week 3 validation passed")
