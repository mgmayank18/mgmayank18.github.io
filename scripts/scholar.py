"""Fetch citation stats from Mayank's Google Scholar profile into data/scholar.json."""
import json, re, sys, urllib.request, datetime

URL = "https://scholar.google.com/citations?user=CZzmgTQAAAAJ&hl=en"
req = urllib.request.Request(URL, headers={
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
})
html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
cells = re.findall(r'<td class="gsc_rsb_std">(\d+)</td>', html)
if len(cells) < 4:
    print("Could not parse Scholar stats (blocked or layout changed); keeping previous data.")
    sys.exit(0)
papers = {}
for row in re.findall(r'<tr class="gsc_a_tr">(.*?)</tr>', html, re.S):
    t = re.search(r'class="gsc_a_at">(.*?)</a>', row)
    c = re.search(r'class="gsc_a_ac gs_ibl"[^>]*>(\d*)</a>', row)
    if t:
        papers[re.sub(r"<.*?>", "", t.group(1)).strip()] = int(c.group(1)) if c and c.group(1) else 0
out = {
    "citations": int(cells[0]),
    "citations_recent": int(cells[1]),
    "h_index": int(cells[2]),
    "i10_index": int(cells[4]) if len(cells) > 4 else None,
    "papers": papers,
    "updated": datetime.date.today().isoformat(),
}
json.dump(out, open("data/scholar.json", "w"), indent=2)
print(json.dumps(out, indent=2))
