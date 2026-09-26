"""Refresh data/scholar.json with citation stats.

Reads Mayank's Google Scholar profile. Scholar often blocks GitHub's servers;
on those days the previous data is kept and the page shows nothing new.
"""
import datetime, json, re, sys, urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
def get(url, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")


def from_google_scholar():
    html = get("https://scholar.google.com/citations?user=CZzmgTQAAAAJ&hl=en", {"Accept-Language": "en-US,en;q=0.9"})
    cells = re.findall(r'<td class="gsc_rsb_std">(\d+)</td>', html)
    if len(cells) < 4:
        raise RuntimeError("could not parse Scholar stats")
    papers = {}
    for row in re.findall(r'<tr class="gsc_a_tr">(.*?)</tr>', html, re.S):
        t = re.search(r'class="gsc_a_at">(.*?)</a>', row)
        c = re.search(r'class="gsc_a_ac gs_ibl"[^>]*>(\d*)</a>', row)
        if t:
            papers[re.sub(r"<.*?>", "", t.group(1)).strip()] = int(c.group(1)) if c and c.group(1) else 0
    return {"source": "Google Scholar", "citations": int(cells[0]), "h_index": int(cells[2]),
            "i10_index": int(cells[4]) if len(cells) > 4 else None, "papers": papers}


out = None
for fn in (from_google_scholar,):
    try:
        out = fn()
        break
    except Exception as e:
        print(f"{fn.__name__} failed: {e}")
if not out:
    print("No source worked; keeping previous data.")
    sys.exit(0)
out["updated"] = datetime.date.today().isoformat()
json.dump(out, open("data/scholar.json", "w"), indent=2)
print(json.dumps(out, indent=2))
