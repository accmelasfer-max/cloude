"""Add one verifier chunk to the page database without duplicates.

usage: python3 add_chunk.py <verified_chunk.json> <existing_dir> <out_dir> [base.json]

  verified_chunk.json  a verifier's output (JSON array, or {"results": [...]})
  existing_dir         directory holding the CURRENT `jobs` docs, one JSON file per doc named <doc_id>.json
                       (as written by ArtifactData `out_dir`, i.e. <out_dir>/jobs/<doc_id>.json; a file may be the raw
                       document or an envelope {"id":..., "data": {...}})
  out_dir              where new seed files <doc_id>.json are written
  base.json            path to generator/base.json (default: next to this script)

Prints "add:" / "dup:" lines, then one JSON line: the ArtifactData batch `writes` array for the new docs.
"""
import json, glob, os, re, sys, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
chunk_path, existing_dir, out_dir = sys.argv[1], sys.argv[2], sys.argv[3]
base_path = sys.argv[4] if len(sys.argv) > 4 else os.path.join(HERE, "base.json")
os.makedirs(out_dir, exist_ok=True)

spec = importlib.util.spec_from_file_location("s2", os.path.join(HERE, "seed_v2_lib.py"))
s2 = importlib.util.module_from_spec(spec)
s2.BASE_PATH = base_path
spec.loader.exec_module(s2)


def load_doc(p):
    d = json.load(open(p))
    if isinstance(d, dict) and isinstance(d.get("data"), dict) and "title" in d["data"]:
        return d["data"]
    return d


existing = {}
for p in glob.glob(os.path.join(existing_dir, "*.json")) + glob.glob(os.path.join(existing_dir, "jobs", "*.json")):
    d = load_doc(p)
    if isinstance(d, dict) and d.get("url"):
        existing[os.path.basename(p)[:-5]] = d

norm = lambda u: re.sub(r"[?#].*$", "", (u or "").strip().lower()).rstrip("/")


AR_MAP = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي", "ة": "ه", "ـ": ""})


def _n(s):
    s = str(s or "").lower().translate(AR_MAP)
    return re.sub(r"[^\w]+", " ", s, flags=re.UNICODE).strip()


def key(d):
    t = _n(d.get("title"))
    t = re.sub(r"\b(riyadh|ksa|saudi arabia|jeddah|dammam|khobar|dhahran|الرياض|جده|الدمام|الخبر)\b", "", t).strip()
    c = _n(d.get("company")).split()[:2]
    return t + "|" + " ".join(c)


seenU = {norm(d["url"]) for d in existing.values()}
seenK = {key(d) for d in existing.values()}
ids = [int(k[1:]) for k in existing if re.fullmatch(r"k\d+", k)]
nxt = (max(ids) + 1) if ids else 1

arr = json.load(open(chunk_path))
arr = arr["results"] if isinstance(arr, dict) else arr
writes, dropped = [], []
for r in arr:
    if not s2.ok(r):
        dropped.append(r)
        continue
    d = s2.build(r)
    if norm(d["url"]) in seenU or key(d) in seenK:
        print("dup:", d["title"], "—", d["company"])
        continue
    seenU.add(norm(d["url"]))
    seenK.add(key(d))
    did = "k%03d" % nxt
    nxt += 1
    p = os.path.join(out_dir, did + ".json")
    json.dump(d, open(p, "w"), ensure_ascii=False)
    writes.append({"op": "set", "collection": "jobs", "doc_id": did, "file_path": os.path.abspath(p)})
    print("add:", did, d["fit_score"], d["title"], "—", d["company"])
print("dropped:", [(r.get("title"), r.get("fit_score"), r.get("live")) for r in dropped])
print(json.dumps(writes))
