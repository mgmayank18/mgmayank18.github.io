"""Refresh data/scholar.json with citation stats.

Tries Mayank's Google Scholar profile first. Scholar often blocks GitHub's
servers, so it falls back to Semantic Scholar's public API for the papers
listed on the site.
"""
import datetime, json, re, sys, time, urllib.parse, urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
PAPERS = [
    ("Gemma 4 Technical Report", "arXiv:2607.02770"),
    ("Zero Shot License Plate Re-Identification", None),
    ("VPDS: An AI-Based Automated Vehicle Occupancy and Violation Detection System", None),
    ("Parametric Synthesis of Text on Stylized Backgrounds using ProGANs", "arXiv:1809.08488"),
]


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


def from_semantic_scholar():
    base = "https://api.semanticscholar.org/graph/v1/paper/"
    papers = {}
    for title, pid in PAPERS:
        for attempt in range(3):
            try:
                if pid:
                    d = json.loads(get(base + pid + "?fields=title,citationCount"))
                else:
                    q = urllib.parse.quote(title)
                    d = json.loads(get(base + "search/match?query=" + q + "&fields=title,citationCount"))["data"][0]
                papers[title] = d.get("citationCount") or 0
                break
            except Exception as e:
                print(f"  {title}: {e}")
                time.sleep(5 * (attempt + 1))
        time.sleep(1.5)
    if not papers:
        raise RuntimeError("no papers resolved")
    counts = sorted(papers.values(), reverse=True)
    h = sum(1 for i, c in enumerate(counts, 1) if c >= i)
    return {"source": "Semantic Scholar", "citations": sum(counts), "h_index": h, "i10_index": None, "papers": papers}


out = None
for fn in (from_google_scholar, from_semantic_scholar):
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
