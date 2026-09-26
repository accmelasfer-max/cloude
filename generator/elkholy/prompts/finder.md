You are sourcing job postings. Today is {TODAY}. Only postings published within the last {DAYS} days (or with no visible date).

{PROFILE}

SOURCE TO SWEEP: {SOURCE}

Use WebSearch and WebFetch (load via ToolSearch "select:WebSearch,WebFetch"). Run a query for EVERY track title family (at least 8 distinct searches, English and Arabic titles: مدير مالي، رئيس حسابات، مدير حسابات، مدير ضرائب، مراقب مالي) and open result pages to harvest individual postings. Skip any posting whose URL is in this ALREADY-KNOWN list (normalise by ignoring query strings): {KNOWN_URLS}
Return up to 30 postings as a JSON array written to {OUT_FILE}. Each item: {"title","company","city" (Arabic name when known: الرياض جدة الدمام الخبر الظهران), "source","url" (ONE specific posting, never a search page; never invent URLs), "posted_text","track" (one of the five keys), "snippet"}. Reply with one line: how many written.
