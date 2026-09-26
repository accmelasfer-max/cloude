# لوحة وظائف محمد الأصفر

لوحة تحكم للبحث عن وظيفة مالية/ضريبية في السعودية، مع سيرة ذاتية مخصصة ورسالة تقديم لكل إعلان.

- `dashboard/index.html` — صفحة اللوحة (تُنشر كـ Artifact مع قاعدة بيانات `jobs`).
- `data/jobs.json` — الوظائف المجمّعة (المسمى، الشركة، الرابط، المسار، درجة التطابق).
- `generator/` — مولّد السير المخصصة: `base.json` (المحتوى الأساسي لكل مسار)، `tailor.json` (التخصيص لكل وظيفة)، `gen.js` (يُنتج PDF لكل وظيفة عبر Playwright/Chromium ويكتب رسائل التقديم).

## التشغيل

```bash
# يحتاج playwright وخطوط Source Sans 3 / Source Serif 4 في مجلد fonts/ (fonts.css + ملفات woff2)
NODE_PATH=$(npm root -g) node generator/gen.js
```

يخرج ملف PDF من صفحتين لكل وظيفة في `dash/cv/jobs/` وملف تحديث لقاعدة البيانات في `generator/db_updates/`.
