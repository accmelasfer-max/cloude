"""Add one verifier chunk incrementally: python3 add_chunk.py <chunk.json>"""
import json, glob, os, re, sys, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "seed_v2")
spec = importlib.util.spec_from_file_location("s2", os.path.join(HERE, "seed_v2_lib.py")); s2 = importlib.util.module_from_spec(spec); spec.loader.exec_module(s2)
existing = {f[:-5].split("/")[-1]: json.load(open(f)) for f in glob.glob(os.path.join(OUT, "k*.json"))}
norm = lambda u: re.sub(r"[?#].*$", "", (u or "").strip().lower()).rstrip("/")
def key(d):
    t = re.sub(r"[^a-z0-9]+", " ", d["title"].lower()).strip(); t = re.sub(r"\b(riyadh|ksa|saudi arabia|jeddah|dammam)\b", "", t).strip()
    c = re.sub(r"[^a-z0-9]+", " ", d["company"].lower()).split()[:1]; return t + "|" + " ".join(c)
seenU = {norm(d["url"]) for d in existing.values()}; seenK = {key(d) for d in existing.values()}
nxt = max(int(k[1:]) for k in existing) + 1
arr = json.load(open(sys.argv[1])); arr = arr["results"] if isinstance(arr, dict) else arr
writes, dropped = [], []
for r in arr:
    if not s2.ok(r): dropped.append(r); continue
    d = s2.build(r)
    if norm(d["url"]) in seenU or key(d) in seenK: print("dup:", d["title"], d["company"]); continue
    seenU.add(norm(d["url"])); seenK.add(key(d))
    did = "k%03d" % nxt; nxt += 1
    p = os.path.join(OUT, did + ".json"); json.dump(d, open(p, "w"), ensure_ascii=False)
    writes.append({"op": "set", "collection": "jobs", "doc_id": did, "file_path": p}); print("add:", did, d["fit_score"], d["title"], "—", d["company"])
print("dropped:", [(r.get("title"), r.get("fit_score"), r.get("live")) for r in dropped])
print(json.dumps(writes))
