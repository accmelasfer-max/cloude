"""Turn the sweep workflow result into artifact-db seed files.

usage: python3 seed_v2.py sweep.json old_status.json
  sweep.json      -> the Workflow tool's returned object
  old_status.json -> {url: status} carried over from the previous job list (may be {})
"""
import json, re, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
sweep = json.load(open(sys.argv[1]))
old = json.load(open(sys.argv[2])) if len(sys.argv) > 2 and os.path.exists(sys.argv[2]) else {}
base = json.load(open(os.path.join(HERE, "base.json")))

OUT = os.path.join(HERE, "seed_v2")
os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT):
    os.remove(os.path.join(OUT, f))

CITY = {"riyadh": "الرياض", "jeddah": "جدة", "dammam": "الدمام", "khobar": "الخبر", "al khobar": "الخبر", "al-khobar": "الخبر",
        "dhahran": "الظهران", "jubail": "الجبيل", "makkah": "مكة", "mecca": "مكة", "madinah": "المدينة", "medina": "المدينة",
        "tabuk": "تبوك", "neom": "نيوم", "abha": "أبها", "yanbu": "ينبع", "saudi arabia": "السعودية", "ksa": "السعودية",
        "eastern province": "المنطقة الشرقية"}
SOURCE = [("linkedin", "LinkedIn"), ("bayt", "Bayt"), ("gulftalent", "GulfTalent"), ("naukrigulf", "Naukrigulf"), ("indeed", "Indeed"),
          ("glassdoor", "Glassdoor"), ("google", "Google Jobs"), ("jadarat", "Jadarat"), ("tanqeeb", "Tanqeeb"), ("monster", "Monster Gulf"),
          ("akhtaboot", "Akhtaboot"), ("foundit", "Foundit"), ("wuzzuf", "Wuzzuf"), ("workday", "موقع الشركة"), ("successfactors", "موقع الشركة"),
          ("taleo", "موقع الشركة"), ("smartrecruiters", "موقع الشركة"), ("greenhouse", "موقع الشركة"), ("lever", "موقع الشركة"),
          ("career", "موقع الشركة"), ("hays", "Hays"), ("michael page", "Michael Page"), ("robert walters", "Robert Walters"),
          ("cooper fitch", "Cooper Fitch"), ("nadia", "Nadia Global"), ("kinetic", "Kinetic")]

def norm_city(c):
    s = (c or "").strip()
    low = s.lower()
    for k, v in CITY.items():
        if k in low:
            return v
    return s or "السعودية"

def norm_source(s, url):
    low = (s or "").lower() + " " + (url or "").lower()
    for k, v in SOURCE:
        if k in low:
            return v
    return (s or "موقع الشركة").strip()[:24]

def norm_url(u):
    return re.sub(r"[?#].*$", "", (u or "").strip().lower()).rstrip("/")

def generic(co):
    return bool(re.search(r"confidential|via |for a client|leading company|recruit|hr\b|talent", co, re.I))

def short_co(co):
    co = re.sub(r"\s*\(.*?\)\s*", " ", co)
    co = re.split(r"\s+[–—-]\s+", co)[0]
    return co.strip()

def covers(j, ev):
    g, co, city = generic(j["company"]), short_co(j["company"]), j["city_en"]
    en = "\n\n".join([
        "Dear Hiring Manager," if g else f"Dear Hiring Team at {co},",
        f"I am writing to apply for the {j['title']} position in {city}. {j['angle_en'].strip()}",
        ev["evidence_en"],
        "I hold a transferable Saudi Iqama and am available for immediate transfer. My CV is attached and I would welcome a conversation about how I can contribute to "
        + ("your organisation." if g else co + "."),
        "Kind regards,\nMohamed El Asfar\n+966 57 020 5701 · acc.m.elasfar@gmail.com · linkedin.com/in/mhamdi1992",
    ])
    ar = None
    if j.get("angle_ar"):
        ar = "\n\n".join([
            "السادة مسؤولي التوظيف المحترمين،" if g else f"السادة فريق التوظيف في {co} المحترمين،",
            f"أتقدم بطلبي لشغل وظيفة {j['title']} في {j['city']}. {j['angle_ar'].strip()}",
            ev["evidence_ar"],
            "أحمل إقامة سعودية قابلة للنقل ومتاح للانتقال فوراً. مرفق سيرتي الذاتية، ويسعدني التحدث عن كيفية إسهامي في " + ("منشأتكم." if g else co + "."),
            "مع خالص التقدير،\nمحمد حمدي الأصفر\n+966 57 020 5701 · acc.m.elasfar@gmail.com",
        ])
    return en, ar

CITY_EN = {"الرياض": "Riyadh", "جدة": "Jeddah", "الدمام": "Dammam", "الخبر": "Al Khobar", "الظهران": "Dhahran", "الجبيل": "Jubail",
           "السعودية": "Saudi Arabia", "المنطقة الشرقية": "the Eastern Province", "نيوم": "NEOM", "تبوك": "Tabuk", "مكة": "Makkah", "المدينة": "Madinah", "أبها": "Abha", "ينبع": "Yanbu"}

seen, docs = set(), []
for r in sweep["jobs"]:
    u = norm_url(r["url"])
    if not u or u in seen:
        continue
    seen.add(u)
    j = dict(r)
    j["city"] = norm_city(r.get("city"))
    j["city_en"] = CITY_EN.get(j["city"], j["city"])
    j["source"] = norm_source(r.get("source"), r.get("url"))
    j["fit_score"] = int(max(0, min(100, round(float(r.get("fit_score") or 0)))))
    ev = base["tracks"][j["track"]]
    en, ar = covers(j, ev)
    doc = {k: j.get(k, "") for k in ["title", "company", "city", "source", "url", "posted_date", "deadline", "language", "live", "seniority",
                                     "years_required", "cert_required", "cert_note", "industry_mandatory", "track", "fit_score", "fit_reason_ar", "requirements_en"]}
    doc["cover_en"] = en
    if ar:
        doc["cover_ar"] = ar
    doc["status"] = old.get(u, "new")
    docs.append(doc)

docs.sort(key=lambda d: (-d["fit_score"], d["posted_date"] or ""), reverse=False)
writes = []
for i, d in enumerate(docs):
    did = "k%03d" % (i + 1)
    p = os.path.join(OUT, did + ".json")
    json.dump(d, open(p, "w"), ensure_ascii=False)
    writes.append({"op": "set", "collection": "jobs", "doc_id": did, "file_path": p})

meta = {"today": sweep["today"], "sources": sweep["sources"], "total_found": sweep["total_found"], "unique": sweep["unique"],
        "verified": sweep["verified"], "kept": len(docs), "dropped": sweep.get("dropped", [])[:150]}
mp = os.path.join(OUT, "meta.json")
json.dump(meta, open(mp, "w"), ensure_ascii=False)
writes.append({"op": "set", "collection": "meta", "doc_id": "sweep", "file_path": mp})

chunks = [writes[i:i + 50] for i in range(0, len(writes), 50)]
for n, c in enumerate(chunks):
    json.dump(c, open(os.path.join(OUT, "batch%d.json" % (n + 1)), "w"))
print(f"{len(docs)} jobs -> {len(chunks)} batch files in {OUT}")
from collections import Counter
print("sources:", Counter(d["source"] for d in docs).most_common())
print("tracks:", Counter(d["track"] for d in docs).most_common())
print("cities:", Counter(d["city"] for d in docs).most_common())
