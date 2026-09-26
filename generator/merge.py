"""Merge verifier chunk outputs into sweep.json for seed_v2.py."""
import json, glob, os, re

S = "/tmp/claude-0/-home-user-cloude/9dbea030-cfa2-50c3-9061-c570c6b3ff07/scratchpad"
files = sorted(glob.glob(os.path.join(S, "verified", "chunk*.json")))
res = []
for f in files:
    try:
        arr = json.load(open(f))
    except Exception as e:
        print("BAD", f, e); continue
    if isinstance(arr, dict) and "results" in arr:
        arr = arr["results"]
    for r in arr:
        r["_file"] = os.path.basename(f)
        res.append(r)

norm = lambda u: re.sub(r"[?#].*$", "", (u or "").strip().lower()).rstrip("/")
seen, uniq = set(), []
for r in res:
    u = norm(r.get("url"))
    if not u or u in seen:
        continue
    seen.add(u); uniq.append(r)

def ok(r):
    try:
        fs = float(r.get("fit_score") or 0)
    except Exception:
        fs = 0
    return r.get("live") != "no" and not r.get("saudi_only") and fs >= 45 and r.get("seniority") != "junior" and r.get("track") in {"accounting_manager","tax_zakat","controller","finance_manager","practice"}

kept = [r for r in uniq if ok(r)]
dropped = [{"title": r.get("title"), "company": r.get("company"), "url": r.get("url"), "live": r.get("live"), "saudi_only": r.get("saudi_only"),
            "fit_score": r.get("fit_score"), "seniority": r.get("seniority")} for r in uniq if not ok(r)]
found_all = json.load(open(os.path.join(S, "found_all.json"))) if os.path.exists(os.path.join(S, "found_all.json")) else []
sweep = {"today": "2026-09-26",
         "sources": ["LinkedIn", "Bayt", "GulfTalent", "Naukrigulf", "Indeed", "Glassdoor", "مواقع مكاتب المراجعة", "وكالات التوظيف وبوابات الجهات شبه الحكومية", "المجمّعات", "بحث بالمسميات العربية"],
         "total_found": max(144, len(found_all)), "unique": len(uniq), "verified": len(uniq), "jobs": kept, "dropped": dropped}
json.dump(sweep, open(os.path.join(S, "sweep.json"), "w"), ensure_ascii=False, indent=1)
from collections import Counter
print(f"files={len(files)} results={len(res)} unique={len(uniq)} kept={len(kept)} dropped={len(dropped)}")
print("live:", Counter(r.get("live") for r in uniq))
print("kept tracks:", Counter(r["track"] for r in kept))
print("kept fit>=75:", sum(1 for r in kept if float(r["fit_score"]) >= 75))
