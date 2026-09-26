// Generates one tailored CV PDF + cover letters per job.
const fs = require("fs"), path = require("path");
const { chromium } = require("playwright");

const ROOT = __dirname;
const SCRATCH = path.resolve(ROOT, "..");
const base = JSON.parse(fs.readFileSync(path.join(ROOT, "base.json"), "utf8"));
const tailor = JSON.parse(fs.readFileSync(path.join(ROOT, "tailor.json"), "utf8"));
const jobs = JSON.parse(fs.readFileSync(path.join(SCRATCH, "jobs_raw.json"), "utf8"));
const OUT_PDF = path.join(SCRATCH, "dash", "cv", "jobs");
const OUT_HTML = path.join(ROOT, "html");
const OUT_DB = path.join(ROOT, "db_updates");
for (const d of [OUT_PDF, OUT_HTML, OUT_DB]) fs.mkdirSync(d, { recursive: true });

const esc = s => String(s).replace(/[&<>]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
const li = arr => arr.map(b => `<li>${esc(b)}</li>`).join("");

const CSS = `
@page { size: A4; margin: 12mm 14mm 12mm 14mm; }
:root{ --ink:#17211D; --muted:#5C6B64; --accent:#17614A; --rule:#CBD6D0; --soft:#EEF4F1; }
*{ box-sizing:border-box }
html,body{ margin:0; padding:0 }
body{ font-family:"Source Sans 3", "Liberation Sans", Arial, sans-serif; color:var(--ink); font-size:9.4pt; line-height:1.27; }
h1,h2{ font-family:"Source Serif 4","Liberation Serif",Georgia,serif; margin:0; }
h1{ font-size:19pt; font-weight:700; letter-spacing:.06em; }
.headline{ font-size:11.2pt; font-weight:600; color:var(--accent); margin-top:2pt; }
.contact{ font-size:9.3pt; color:var(--muted); margin-top:3pt; }
.contact span+span::before{ content:"  •  "; color:var(--rule); }
.target{ margin-top:6pt; padding:4pt 8pt; background:var(--soft); border-left:3px solid var(--accent); font-size:9.4pt; display:flex; justify-content:space-between; gap:10pt; }
.target b{ font-weight:600 }
h2{ font-size:9.6pt; font-weight:700; letter-spacing:.14em; text-transform:uppercase; color:var(--accent); border-bottom:1px solid var(--rule); padding-bottom:2.5pt; margin:7.5pt 0 3pt; break-after:avoid; }
p{ margin:0 }
ul{ margin:0; padding-left:12pt }
li{ margin:0 0 1.8pt; padding-left:1pt }
li::marker{ color:var(--accent) }
.fit li{ margin-bottom:3pt }
.comp{ display:grid; grid-template-columns:auto 1fr; gap:1.8pt 8pt; }
.comp dt{ font-weight:600; white-space:nowrap; }
.comp dd{ margin:0 }
.role{ break-inside:avoid; margin-top:5pt }
.role:first-of-type{ margin-top:0 }
.rh{ display:flex; justify-content:space-between; align-items:baseline; gap:8pt }
.rh .t{ font-weight:700; font-size:10.6pt }
.rh .t span{ font-weight:400; color:var(--muted) }
.rh .d{ color:var(--muted); font-size:9.3pt; white-space:nowrap }
.blurb{ font-style:italic; color:var(--muted); font-size:9.3pt; margin:1pt 0 2pt }
.edu{ break-inside:avoid } .edu p{ margin-bottom:1.5pt }
.edu b{ font-weight:600 }
`;

function cvHTML(job, t) {
  const tr = base.tracks[t.track];
  const c = base.contact;
  const comps = tr.competencies.map(k => `<dt>${esc(base.competencies[k][0])}:</dt><dd>${esc(base.competencies[k][1])}</dd>`).join("");
  const exp = tr.experience.map(k => {
    const e = base.experience[k];
    return `<div class="role"><div class="rh"><div class="t">${esc(e.title)} <span>| ${esc(e.company)}</span></div><div class="d">${esc(e.place)} · ${esc(e.dates)}</div></div>${e.blurb ? `<p class="blurb">${esc(e.blurb)}</p>` : ""}<ul>${li(e.bullets)}</ul></div>`;
  }).join("");
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><title>${esc(base.name)} — ${esc(t.headline)}</title>
<link rel="stylesheet" href="../../fonts/fonts.css"><style>${CSS}</style></head><body>
<header>
  <h1>${esc(base.name)}</h1>
  <div class="headline">${esc(t.headline)} &nbsp;|&nbsp; ${esc(tr.tagline)}</div>
  <div class="contact"><span>${esc(c.city)}</span><span>${esc(c.phone)}</span><span>${esc(c.email)}</span><span>${esc(c.linkedin)}</span></div>
  <div class="target"><span>Application for <b>${esc(job.title)}</b> — ${esc(job.company)}</span><span>${esc(job.city_en)}</span></div>
</header>
<h2>Professional Summary</h2>
<p>${esc(t.open)} ${esc(tr.summary_rest)}</p>
<h2>Relevance to this Role</h2>
<ul class="fit">${li(t.fit)}</ul>
<h2>Key Achievements</h2>
<ul>${li(tr.achievements.map(k => base.achievements[k]))}</ul>
<h2>Core Competencies</h2>
<dl class="comp">${comps}</dl>
<h2>Professional Experience</h2>
${exp}
<h2>Certifications &amp; Education</h2>
<div class="edu">
<p><b>Certification:</b> ${esc(base.education.cert)}</p>
<p><b>Education:</b> ${esc(base.education.degree)}</p>
<p><b>Languages:</b> ${esc(base.education.languages)}</p>
<p><b>Work Authorisation:</b> ${esc(base.education.work)}</p>
</div>
</body></html>`;
}

const CITY_EN = { "الرياض": "Riyadh", "جدة": "Jeddah", "الدمام": "Dammam", "الظهران": "Dhahran", "الخبر": "Al Khobar" };
const generic = co => /confidential|via |for a client|leading company/i.test(co);
const shortCo = co => co.replace(/\s*\(.*?\)\s*/g, "").replace(/\s*–.*$/, "").trim();

function covers(job, t) {
  const tr = base.tracks[t.track];
  const g = generic(job.company), co = shortCo(job.company), city = job.city_en;
  const en = [
    g ? "Dear Hiring Manager," : `Dear Hiring Team at ${co},`,
    `I am writing to apply for the ${job.title} position in ${city}. ${t.angle}`,
    tr.evidence_en,
    `I hold a transferable Saudi Iqama and am available for immediate transfer. I have attached a CV prepared for this role and would welcome a conversation about how I can contribute to ${g ? "your organisation" : co}.`,
    `Kind regards,\nMohamed El Asfar\n+966 57 020 5701 · acc.m.elasfar@gmail.com · linkedin.com/in/mhamdi1992`
  ].join("\n\n");
  let ar = null;
  if (t.angle_ar) {
    ar = [
      g ? "السادة مسؤولي التوظيف المحترمين،" : `السادة فريق التوظيف في ${co} المحترمين،`,
      `أتقدم بطلبي لشغل وظيفة ${job.title} في ${job.city}. ${t.angle_ar}`,
      tr.evidence_ar,
      `أحمل إقامة سعودية قابلة للنقل ومتاح للانتقال فوراً. مرفق سيرتي الذاتية المُعدّة لهذه الوظيفة، ويسعدني التحدث عن كيفية إسهامي في ${g ? "منشأتكم" : co}.`,
      `مع خالص التقدير،\nمحمد حمدي الأصفر\n+966 57 020 5701 · acc.m.elasfar@gmail.com`
    ].join("\n\n");
  }
  return { en, ar };
}

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const byId = Object.fromEntries(jobs.map((j, i) => ["j" + String(i + 1).padStart(2, "0"), j]));
  for (const t of tailor) {
    const job = { ...byId[t.id], city_en: CITY_EN[byId[t.id].city] || byId[t.id].city };
    if (!job.title) throw new Error("no job for " + t.id);
    const html = cvHTML(job, t);
    const hp = path.join(OUT_HTML, t.id + ".html");
    fs.writeFileSync(hp, html);
    await page.goto("file://" + hp, { waitUntil: "load" });
    await page.evaluate(() => document.fonts.ready);
    const pdf = path.join(OUT_PDF, t.id + ".pdf");
    await page.pdf({ path: pdf, format: "A4", printBackground: true, preferCSSPageSize: true });
    const { en, ar } = covers(job, t);
    const upd = { cv: `cv/jobs/${t.id}.pdf`, cv_name: `Mohamed_ElAsfar_CV_${shortCo(job.company).replace(/[^A-Za-z0-9]+/g, "_").replace(/^_|_$/g, "")}.pdf`, headline: t.headline, cover_en: en };
    if (ar) upd.cover_ar = ar;
    fs.writeFileSync(path.join(OUT_DB, t.id + ".json"), JSON.stringify(upd, null, 1));
    process.stdout.write(t.id + " ");
  }
  await browser.close();
  console.log("\ndone");
})();
