"""Fetch the "what is running now" data for the page panel. Standard library only.

Two kinds of source:
  test fishery   daily catch per species of the test nets on the Fraser:
                 DFO Albion (Fort Langley; Chinook, Chum, Coho) from the DFO FOS report,
                 PSC Whonnock (Maple Ridge) and Qualark (near Yale; Sockeye, Pink) from PSC PDF tables
  shop reports   weekly fishing reports of tackle shops (Atom feed): title, date, link,
                 species and map waters named in the text

Writes reports.json next to this script. A source that fails is left out and logged as a
warning; the script never fails the build, because the map must deploy without this panel.
Only titles, dates, links and tags are kept: the report text stays on the shop site.

  python fetch_reports.py
"""
import html, json, re, sys, time, urllib.parse, urllib.request, zlib
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "reports.json"
UA = "bc-salmon-map-reports/1.0 (+https://github.com/volkotyk/bc-salmon-map)"

FOS = "https://www-ops2.pac.dfo-mpo.gc.ca/fos2_Internet/Testfish/rptCSbD.cfm?stat=CPTFM"
ALBION_PAGE = "https://www.pac.dfo-mpo.gc.ca/fm-gp/fraser/albion-eng.html"
ALBION = [
    # species, FOS fishery sub-id (net), FOS species code
    ("chinook", 242, 124),   # 8" chinook net
    ("chum",    227, 112),   # 6.75" chum net, from Sep 1
    ("coho",    227, 115),   # coho caught in the chum net
]
PSC_PAGE = "https://www.psc.org/publications/fraser-panel-in-season-information/test-fishing-results/"
PSC = [
    # site, PDF (links from PSC_PAGE); both PDFs have the same table layout
    ("Whonnock", "https://www.psc.org/download/112/daily-test-fishing/3179/whonnock-gillnet.pdf"),
    ("Qualark",  "https://www.psc.org/download/112/daily-test-fishing/11828/qualark-gillnet.pdf"),
]
KEEP_DAYS = 28            # test-fishery history kept in the page

FEEDS = [
    # source name, Atom feed, title filter (other blog posts are sales and news)
    ("Pacific Angler", "https://www.pacificangler.ca/blogs/learn.atom", re.compile(r"fishing report", re.I)),
]
KEEP_REPORTS = 3          # newest reports kept per feed

# Species names as anglers write them. "Pink" and "spring" alone are also a colour and a season.
SPECIES = {
    "chinook": r"chinook|springs|spring salmon",
    "coho":    r"coho",
    "chum":    r"chum|chums|dog salmon",
    "pink":    r"pinks|pink salmon|humpies",
    "sockeye": r"sockeye",
}
# Water names in report text -> map keys: a water id of build/rules.json, or a DFO tidal subarea
# ("28-8"), because the ids of tidal groups follow the DFO table order and can change.
# main() warns about keys that rules.json lacks. Town and lake names are excluded:
# "Squamish", "Coquitlam" or "Harrison Lake" alone are not the river.
WATERS = {
    "chilliwack":      r"vedder|chilliwack river",
    "capilano":        r"capilano",
    "squamish":        r"squamish river|the squamish",
    "cheakamus":       r"cheakamus",
    "mamquam":         r"mamquam",
    "ashlu":           r"ashlu",
    "chapman":         r"chapman creek",
    "lois":            r"lois lake",
    "khartoum":        r"khartoum lake",
    "coquitlam":       r"coquitlam river",
    "deboville":       r"de ?boville",
    "alouette":        r"alouette river|the alouette",
    "kanaka":          r"kanaka creek",
    "serpentine":      r"serpentine",
    "nicomekl":        r"nicomekl",
    "little-campbell": r"little campbell",
    "stave":           r"stave river|the stave",
    "norrish":         r"norrish|suicide creek",
    "nicomen":         r"nicomen|dewdney slough",
    "harrison":        r"harrison river|the harrison",
    "chehalis":        r"chehalis river|the chehalis",
    "a29-mouth":       r"fraser mouth|mouth of the fraser",
    "28-1":            r"howe sound",
    "28-10":           r"burrard inlet",
    "28-8":            r"false creek",
}
tags = lambda table: {k: re.compile(rf"\b(?:{v})\b", re.I) for k, v in table.items()}
SPECIES_RE, WATERS_RE = tags(SPECIES), tags(WATERS)


def fetch(url, data=None):
    last = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, data=data, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception as e:          # network hiccup: retry, then let the caller skip the source
            last = e
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"cannot fetch {url}: {last}")


def fetch_text(url, data=None):
    return fetch(url, data).decode("utf-8", "replace")


def text_of(fragment):
    s = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", fragment, flags=re.S | re.I)
    s = html.unescape(re.sub(r"<[^>]+>", " ", s)).replace("\xa0", " ")
    return re.sub(r"\s+", " ", s).strip()


def day(date_iso, catch, effort, per=1):
    # CPUE: catch per unit of net effort. The unit differs per source, so compare a series only with itself.
    return [date_iso, catch, round(catch * per / effort, 2)]


# ---------- DFO Albion: FOS "Catch Summary by Date" HTML table ----------
FOS_DAY = re.compile(r"\d{2} [A-Z][a-z]{2} \d{4}$")
num = lambda s: float(s.replace(",", "") or 0)


def albion(year, fsub, species_code):
    body = urllib.parse.urlencode({"lboYears": year, "lboFsub": fsub, "lboSpecies": species_code,
                                   "cmdRunReport": "Run Report"}).encode()
    page = fetch_text(FOS, body)
    if "Catch Summary Table" not in page:
        raise RuntimeError("FOS report layout changed: no 'Catch Summary Table'")
    days = []
    # A day row has 10 cells: date, net length (can be empty), then catch, sets, effort, CPUE
    # for vessel 1 and the same four for vessel 2. Statweek subtotal rows do not start with a date.
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", page, flags=re.S | re.I):
        cells = [text_of(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", row, flags=re.S | re.I)]
        if len(cells) != 10 or not FOS_DAY.match(cells[0]):
            continue
        catch, effort = int(num(cells[2]) + num(cells[6])), num(cells[4]) + num(cells[8])
        if effort:                      # effort 0: no net in the water that day
            # Fish per 1000 fathom-minutes, as in the DFO table.
            days.append(day(datetime.strptime(cells[0], "%d %b %Y").date().isoformat(), catch, effort, 1000))
    if not days and "Statweek" in page:
        raise RuntimeError("FOS report has week totals but no day rows: the table layout changed")
    return sorted(days)


# ---------- PSC Whonnock / Qualark: PDF table (Microsoft Access report) ----------
# The PDF has one Flate stream per page; each cell is a BT..ET block with a Tm position and
# WinAnsi literal strings in a TJ array. That is enough to rebuild the table rows by y and x.
PDF_ESC = re.compile(rb"\\([nrtbf()\\]|[0-7]{1,3})")
PDF_ESC_MAP = {b"n": b"\n", b"r": b"\r", b"t": b"\t", b"b": b"\b", b"f": b"\f", b"(": b"(", b")": b")", b"\\": b"\\"}
ROW_TOL = 3               # PDF units: a cell can sit 1-2 units off the rest of its row


def pdf_rows(data):
    """Rows of text cells, top to bottom on each page: [[page, y, [(x, text), ...]], ...]."""
    rows, page = [], 0
    for m in re.finditer(rb"<<([^<>]*?/FlateDecode[^<>]*?)>>\s*stream\r?\n", data):
        start = m.end()
        try:
            stream = zlib.decompress(data[start:data.find(b"endstream", start)])
        except zlib.error:
            continue
        if b"BT" not in stream:
            continue                    # fonts, metadata
        page += 1
        items = []
        for bt in re.findall(rb"BT(.*?)ET", stream, re.S):
            tm = re.search(rb"([-\d.]+) ([-\d.]+) Tm", bt)
            if tm:
                s = b"".join(PDF_ESC.sub(lambda e: PDF_ESC_MAP.get(e.group(1)) or bytes([int(e.group(1), 8) & 255]), x)
                             for x in re.findall(rb"\(((?:\\.|[^\\)])*)\)", bt))
                items.append((float(tm.group(2)), float(tm.group(1)), s.decode("cp1252").strip()))
        for y, x, t in sorted(items, key=lambda i: (-i[0], i[1])):
            if rows and rows[-1][0] == page and rows[-1][1] - y <= ROW_TOL:
                rows[-1][2].append((x, t))
            else:
                rows.append([page, y, [(x, t)]])
    for r in rows:
        r[2].sort()
    return rows


PSC_GROUPS = ["Assessment", "Sockeye", "Pink", "Chinook", "Chinook (Rel.)", "Coho", "Sthd", "Chum", "Other"]
PSC_HEAD = ["Date", "Vessels", "Sets", "Effort", "Adult", "Jack", "All", "Adult", "Jack", "Adult", "Jack",
            "All", "Rel.", "All", "All", "All"]
PSC_EFFORT = 3
PSC_COLS = {"sockeye": (4, 5), "pink": (6,)}      # PSC_HEAD columns: sockeye adult + jack, pink all
PSC_DAY = re.compile(r"\d{2}-[A-Z][a-z]{2}-\d{2}$")


def psc(url):
    rows = pdf_rows(fetch(url))
    if not any([t for _, t in cells] == PSC_GROUPS for _, _, cells in rows):
        raise RuntimeError("PSC table layout changed: species header row not found")
    starts, out = None, {sp: [] for sp in PSC_COLS}
    for _, _, cells in rows:
        texts = [t for _, t in cells]
        if texts == PSC_HEAD:
            starts = [x for x, _ in cells]      # left edge of each column on this page
            continue
        if starts is None or not PSC_DAY.match(texts[0]):
            continue
        vals = {}
        for x, t in cells[1:]:
            # Numbers are right-aligned, so a value starts at or right of its column's left edge.
            vals[max((i for i, s in enumerate(starts) if s <= x + 2), default=0)] = num(t)
        effort = vals.get(PSC_EFFORT, 0)
        if not effort:                  # no set that day
            continue
        iso = datetime.strptime(texts[0], "%d-%b-%y").date().isoformat()
        for sp, cols in PSC_COLS.items():
            out[sp].append(day(iso, int(sum(vals.get(c, 0) for c in cols)), effort))
    if starts is None or not any(out.values()):
        raise RuntimeError("PSC table layout changed: no column header or no day rows")
    return {sp: sorted(d) for sp, d in out.items()}


def test_fishery(today):
    since = (today - timedelta(days=KEEP_DAYS)).isoformat()
    week = (today - timedelta(days=7)).isoformat()
    got = []                            # (site, species, source, url, days), downstream to upstream
    for sp, fsub, code in ALBION:
        try:
            got.append(("Albion", sp, "DFO", ALBION_PAGE, albion(today.year, fsub, code)))
        except Exception as e:
            warn(f"Albion {sp}: {e}")
    for site, url in PSC:
        try:
            got += [(site, sp, "PSC", PSC_PAGE, d) for sp, d in psc(url).items()]
        except Exception as e:
            warn(f"{site}: {e}")
    out = []
    for site, sp, src, url, days in got:
        days = [d for d in days if d[0] >= since]
        print(f"{site} {sp}: {len(days)} days since {since}, {sum(d[1] for d in days)} fish")
        # No fish in the last 7 days: the species is not running there now (a stray fish weeks ago is not a run).
        if any(d[1] for d in days if d[0] > week):
            out.append({"id": f"{site.lower()}-{sp}", "sp": sp, "site": site, "src": src, "url": url, "days": days})
    return out


# ---------- tackle shop reports: Atom feeds ----------
ATOM = "{http://www.w3.org/2005/Atom}"


def shop_reports(name, url, title_re):
    root = ET.fromstring(fetch(url))
    out = []
    for e in root.iter(ATOM + "entry"):
        title = re.sub(r"\s+", " ", e.findtext(ATOM + "title", "")).strip()
        if not title_re.search(title):
            continue
        link = next((l.get("href") for l in e.iter(ATOM + "link") if l.get("rel", "alternate") == "alternate"), None)
        stamp = e.findtext(ATOM + "published") or e.findtext(ATOM + "updated") or ""
        body = text_of(e.findtext(ATOM + "content", ""))
        if not (link and link.startswith("https://") and re.match(r"\d{4}-\d{2}-\d{2}", stamp)):
            continue
        out.append({"src": name, "title": title, "url": link, "date": stamp[:10],   # local date of the post
                    "sp": [k for k, rx in SPECIES_RE.items() if rx.search(body)],
                    "w": [k for k, rx in WATERS_RE.items() if rx.search(body)]})
    out.sort(key=lambda r: r["date"], reverse=True)
    return out[:KEEP_REPORTS]


def reports():
    out = []
    for name, url, title_re in FEEDS:
        try:
            got = shop_reports(name, url, title_re)
        except Exception as e:
            warn(f"{name}: {e}")
            continue
        print(f"{name}: {len(got)} reports")
        out += got
    return sorted(out, key=lambda r: r["date"], reverse=True)


def warn(msg):
    # GitHub Actions shows ::warning:: lines on the run summary.
    print(f"::warning::fetch_reports: {msg}", file=sys.stderr)


def main():
    waters = json.loads((HERE / "rules.json").read_text(encoding="utf-8"))["waters"]
    known = {w["id"] for w in waters} | {s for w in waters for s in w.get("subs") or []}
    if WATERS.keys() - known:
        warn(f"WATERS keys missing from rules.json: {sorted(WATERS.keys() - known)}")
    today = datetime.now(timezone(timedelta(hours=-8))).date()     # Pacific standard time is close enough for a date
    data = {"generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
            "testfish": test_fishery(today), "reports": reports()}
    OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8", newline="\n")
    print(f"{OUT.name}: {len(data['testfish'])} test-fishery series, {len(data['reports'])} reports")


if __name__ == "__main__":
    main()
