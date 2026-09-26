"""Merge Elkholy verifier chunks, dedupe, build db seed docs and batch files."""
import json, glob, os, re, importlib.util, datetime
from collections import Counter

E = os.path.dirname(os.path.abspath(__file__))
G = "/home/user/cloude/generator"
spec = importlib.util.spec_from_file_location("s2", os.path.join(G, "seed_v2_lib.py"))
s2 = importlib.util.module_from_spec(spec); s2.BASE_PATH = os.path.join(E, "base.json"); spec.loader.exec_module(s2)

AR = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي", "ة": "ه", "ـ": ""})
_n = lambda s: re.sub(r"[^\w]+", " ", str(s or "").lower().translate(AR)).strip()
norm = lambda u: re.sub(r"[?#].*$", "", (u or "").strip().lower()).rstrip("/")
def key(d):
    t = re.sub(r"\b(riyadh|ksa|saudi arabia|jeddah|dammam|khobar|dhahran|الرياض|جده|الدمام|الخبر)\b", "", _n(d.get("title"))).strip()
    return t + "|" + " ".join(_n(d.get("company")).split()[:2])

res = []
for f in sorted(glob.glob(os.path.join(E, "verified", "chunk*.json"))):
    try:
        a = json.load(open(f)); a = a["results"] if isinstance(a, dict) else a; res += a
    except Exception as e:
        print("BAD", f, e)
seenU, seenK, uniq = set(), set(), []
for r in res:
    u, k = norm(r.get("url")), key(r)
    if not u or u in seenU or k in seenK: continue
    seenU.add(u); seenK.add(k); uniq.append(r)
kept = [r for r in uniq if s2.ok(r)]
dropped = [{"title": r.get("title"), "company": r.get("company"), "url": r.get("url"), "live": r.get("live"), "saudi_only": r.get("saudi_only"),
            "fit_score": r.get("fit_score"), "seniority": r.get("seniority")} for r in uniq if not s2.ok(r)]

OUT = os.path.join(E, "seed"); os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT): os.remove(os.path.join(OUT, f))
docs = sorted((s2.build(r) for r in kept), key=lambda d: (-d["fit_score"], d["posted_date"] or ""))
writes = []
for i, d in enumerate(docs):
    did = "k%03d" % (i + 1); p = os.path.join(OUT, did + ".json")
    json.dump(d, open(p, "w"), ensure_ascii=False)
    writes.append({"op": "set", "collection": "jobs", "doc_id": did, "file_path": p})
found = json.load(open(os.path.join(E, "found_all.json")))
meta = {"today": "2026-09-26", "sources": ["LinkedIn", "Bayt", "GulfTalent", "Naukrigulf", "Indeed", "Glassdoor", "مواقع الشركات (مقاولات وتجارة إلكترونية)", "وكالات التوظيف", "لوحات عربية (Sabbar، Mourjan، Jobs-Arab)"],
        "total_found": 231, "unique": len(uniq), "verified": len(uniq), "kept": len(docs), "dropped": dropped[:150]}
mp = os.path.join(OUT, "meta.json"); json.dump(meta, open(mp, "w"), ensure_ascii=False)
writes.append({"op": "set", "collection": "meta", "doc_id": "sweep", "file_path": mp})
for n, i in enumerate(range(0, len(writes), 50)):
    json.dump(writes[i:i + 50], open(os.path.join(OUT, "batch%d.json" % (n + 1)), "w"))
T = datetime.date(2026, 9, 26)
def prio(d):
    try: n = (T - datetime.date.fromisoformat(d["posted_date"])).days
    except Exception: n = None
    rec = 40 if n is None else max(0, 1 - n / 30) * 100
    return round(d["fit_score"] * 0.75 + rec * 0.25)
print(f"results={len(res)} unique={len(uniq)} kept={len(docs)} dropped={len(dropped)} batches={(len(writes)+49)//50}")
print("live:", Counter(r.get("live") for r in uniq)); print("tracks:", Counter(d["track"] for d in docs)); print("sources:", Counter(d["source"] for d in docs).most_common(8))
print("high priority:", sum(1 for d in docs if prio(d) >= 75))
for d in sorted(docs, key=prio, reverse=True)[:10]: print(prio(d), d["fit_score"], d["posted_date"], d["title"], "—", d["company"], d["city"])
