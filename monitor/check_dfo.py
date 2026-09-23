"""Daily check of the three DFO salmon pages the map is built from.

Fetches each page, keeps only the salmon part as plain text, and compares it with
monitor/snapshots/<name>.txt. On a change it rewrites the snapshot, writes
monitor/out/issue.md (title on the first line, then the body) and prints
changed=true to $GITHUB_OUTPUT. Standard library only.

  python monitor/check_dfo.py            check and update snapshots
  python monitor/check_dfo.py --init     write snapshots without reporting a change
"""
import difflib, html, os, re, sys, time, urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "snapshots"
OUT = ROOT / "out"
UA = "bc-salmon-map-monitor/1.0 (+https://github.com/volkotyk/bc-salmon-map)"

PAGES = [
    # name, title, url, start marker, end markers (first one found wins)
    ("region2", "Region 2 – Lower Mainland (fresh water)",
     "https://www.pac.dfo-mpo.gc.ca/fm-gp/rec/fresh-douce/region2-eng.html",
     "<main", ["</main>"]),
    ("area28", "Area 28 (tidal)",
     "https://www.pac.dfo-mpo.gc.ca/fm-gp/rec/tidal-maree/a-s28-eng.html",
     '<h2 id="salmon"', ["<summary>Other finfish", '<h2 id="finfish"']),
    ("area29", "Area 29 (tidal)",
     "https://www.pac.dfo-mpo.gc.ca/fm-gp/rec/tidal-maree/a-s29-eng.html",
     '<h2 id="salmon"', ["<summary>Other finfish", '<h2 id="finfish"']),
]
MAX_DIFF = 18000          # characters of diff per page in the issue body (GitHub limit is 65536 in total)


def fetch(url):
    last = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:          # network hiccup: retry, then fail the run loudly
            last = e
            time.sleep(10 * (attempt + 1))
    raise RuntimeError(f"cannot fetch {url}: {last}")


def section(page, start, ends):
    i = page.find(start)
    if i < 0:
        raise RuntimeError(f"marker {start!r} not found: the DFO page layout changed, update monitor/check_dfo.py")
    for end in ends:
        j = page.find(end, i)
        if j > 0:
            return page[i:j + len(end)]
    raise RuntimeError(f"end marker not found after {start!r}: the DFO page layout changed")


def to_text(fragment):
    s = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", fragment, flags=re.S | re.I)
    # Keep link targets: fishery-notice links carry the rule changes.
    s = re.sub(r'<a\b[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r"\2 [\1]", s, flags=re.S | re.I)
    s = re.sub(r"</t[dh]>", " | ", s, flags=re.I)
    s = re.sub(r"<br\s*/?>|</(p|h\d|li|tr|div|table|ul|ol|dt|dd|summary|caption)>", "\n", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s).replace("\xa0", " ")
    lines = (re.sub(r"\s+", " ", ln).strip() for ln in s.splitlines())
    return "\n".join(ln for ln in lines if ln and ln != "|") + "\n"


def main():
    init = "--init" in sys.argv
    SNAP.mkdir(exist_ok=True)
    changed = []
    for name, title, url, start, ends in PAGES:
        text = to_text(section(fetch(url), start, ends))
        path = SNAP / f"{name}.txt"
        old = path.read_text(encoding="utf-8") if path.exists() else None
        if old == text:
            print(f"{name}: no change")
            continue
        path.write_text(text, encoding="utf-8", newline="\n")
        if old is None or init:
            print(f"{name}: snapshot written")
            continue
        diff = "".join(difflib.unified_diff(old.splitlines(True), text.splitlines(True),
                                            f"{name} (previous)", f"{name} ({date.today()})", n=2))
        if len(diff) > MAX_DIFF:
            diff = diff[:MAX_DIFF] + "\n… (diff truncated; see the commit that updated the snapshot)\n"
        changed.append((name, title, url, diff))
        print(f"{name}: CHANGED")

    if changed:
        OUT.mkdir(exist_ok=True)
        head = f"DFO salmon rules changed: {', '.join(c[1] for c in changed)} ({date.today()})"
        body = ["The daily check found changes on these DFO pages. Review the diff and update "
                "`WATERS` in `build/template.html` if the fishing rules changed.\n"]
        for name, title, url, diff in changed:
            body.append(f"### {title}\n{url}\n\n```diff\n{diff}```\n")
        body.append("- [ ] Rules in `build/template.html` checked and updated (or no map change needed)\n"
                    "- [ ] Page redeployed and checked at https://volkotyk.github.io/bc-salmon-map/\n")
        (OUT / "issue.md").write_text(head + "\n" + "\n".join(body), encoding="utf-8", newline="\n")

    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a", encoding="utf-8") as f:
            f.write(f"changed={'true' if changed else 'false'}\n")
            f.write(f"pages={','.join(c[0] for c in changed)}\n")


if __name__ == "__main__":
    main()
