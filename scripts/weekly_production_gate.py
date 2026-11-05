#!/usr/bin/env python3
"""Fail-closed weekly production queue. Never publishes or merges."""
import json,os,re,subprocess
from pathlib import Path
PLAN=Path("data/365_word_plan.json")
STATE=Path("data/weekly_queue.json")
if not PLAN.is_file():
    raise SystemExit("STOP: data/365_word_plan.json missing. Import approved V1.2 plan before enabling production.")
plan=json.loads(PLAN.read_text(encoding="utf-8"))
assert isinstance(plan,list) and len(plan)==365,"Expected exactly 365 ordered daily entries"
for i,x in enumerate(plan,1):
    assert isinstance(x,dict) and x.get("day")==i and isinstance(x.get("word"),str) and x["word"].strip(),f"Invalid Day {i}"
assert len({x["word"].strip().casefold() for x in plan})==365,"Duplicate core words: stop for manual review"
extras={121:"here",122:"there",274:"I",275:"you",276:"we",277:"he",278:"she",279:"my",280:"your",281:"name"}
assert {x["day"]:x["supplement"] for x in plan if "supplement" in x}==extras,"Supplement assignments differ from approved V1.2"
assert [x["word"] for x in plan[14:21]]==["hi","bye","yes","no","thanks","okay","good"],"Week 3 differs from V1.2"
assert plan[364]["word"]=="careful","Day 365 differs from V1.2"
week=int(os.environ.get("WEEK","0"))
assert 3<=week<=53,"WEEK must be 3..53"
first=(week-1)*7+1;last=min(week*7,365)
selected=plan[first-1:last]
assert len(selected)==last-first+1
print(json.dumps({"week":week,"start":first,"end":last,"words":selected},ensure_ascii=False,indent=2))
