"""Turn the three DFO salmon pages into build/rules.json.

  python dfo/update.py             fetch DFO, parse, validate, update rules/status/snapshots
  python dfo/update.py --cache     same, but reuse the pages saved in dfo/cache/ (no network)

Safeguard: if a page contains anything the parser or dfo/catalog.py does not understand
(a new water, an odd date, a new table layout ...), rules.json is NOT changed. status.json then
records `pending` with the reasons, the page shows a warning, and the workflow opens an issue.

Writes $GITHUB_OUTPUT: changed=true|false (files to commit), new_block=true|false (open an issue).
Standard library only.
"""
import difflib, json, os, re, sys, time, urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import catalog as C
from htmltable import tables

ROOT = Path(__file__).resolve().parent.parent
DFO = ROOT / "dfo"
RULES = ROOT / "build" / "rules.json"
STATUS = ROOT / "build" / "status.json"
UA = "bc-salmon-map/1.0 (+https://github.com/volkotyk/bc-salmon-map)"
PAGES = {
    "region2": ("Region 2 – Lower Mainland", "https://www.pac.dfo-mpo.gc.ca/fm-gp/rec/fresh-douce/region2-eng.html"),
    "area28": ("Area 28", "https://www.pac.dfo-mpo.gc.ca/fm-gp/rec/tidal-maree/a-s28-eng.html"),
    "area29": ("Area 29", "https://www.pac.dfo-mpo.gc.ca/fm-gp/rec/tidal-maree/a-s29-eng.html"),
}
MONTHS = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
MON_UK = ["січ", "лют", "бер", "кві", "тра", "чер", "лип", "сер", "вер", "жов", "лис", "гру"]
MON_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
SPECIES = {"chinook": "chinook", "coho": "coho", "chum": "chum", "pink": "pink", "sockeye": "sockeye", "all": "all"}
YEAR = ("04-01", "03-31")
B = C.B


class Problems(list):
    def add(self, msg):
        if msg not in self:
            self.append(msg)


# ---------------------------------------------------------------- fetch
def fetch(url):
    last = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:      # retry, then fail the run: better no deploy than a guess
            last = e
            time.sleep(10 * (attempt + 1))
    raise RuntimeError(f"cannot fetch {url}: {last}")


def cut(page, start, ends, name, bad):
    i = page.find(start)
    j = next((page.find(e, i) for e in ends if i >= 0 and page.find(e, i) > 0), -1)
    if i < 0 or j < 0:
        bad.add(f"{name}: page layout changed (marker {start!r} not found)")
        return ""
    return page[i:j]


# ---------------------------------------------------------------- small parsers
def md(mon, day):
    return f"{MONTHS[mon[:3].lower()]:02d}-{int(day):02d}"


def parse_dates(text):
    """'Sep 1 to Nov 30' | 'June 1 to Aug 31' | 'Apr 1 until further notice' | 'year round' -> (from, to)."""
    t = text.strip().strip("()").strip()
    if re.fullmatch(r"year round", t, re.I):
        return YEAR
    m = re.fullmatch(r"([A-Za-z]{3,9})\.? (\d{1,2}) to ([A-Za-z]{3,9})\.? (\d{1,2})", t)
    if m and m[1][:3].lower() in MONTHS and m[3][:3].lower() in MONTHS:
        return md(m[1], m[2]), md(m[3], m[4])
    m = re.fullmatch(r"([A-Za-z]{3,9})\.? (\d{1,2}) until further notice", t, re.I)
    if m and m[1][:3].lower() in MONTHS:
        start = datetime(2001, MONTHS[m[1][:3].lower()], int(m[2]))
        end = start.replace(year=2002) if (start.month, start.day) == (1, 1) else start
        prev = datetime.fromordinal(end.toordinal() - 1)
        return md(m[1], m[2]), f"{prev.month:02d}-{prev.day:02d}"
    return None


def fmt_range(fr, to):
    if (fr, to) == YEAR:
        return B("цілий рік", "year round")
    (m1, d1), (m2, d2) = [map(int, x.split("-")) for x in (fr, to)]
    return B(f"{d1} {MON_UK[m1-1]} – {d2} {MON_UK[m2-1]}", f"{MON_EN[m1-1]} {d1} – {MON_EN[m2-1]} {d2}")


def species_of(text):
    w = text.split()[0].lower() if text.strip() else ""
    return SPECIES.get(w)


def plural_hatchery(n):
    n = int(n)
    return "заводська" if n % 10 == 1 and n % 100 != 11 else "заводські" if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14 else "заводських"


def fresh_limit(en):
    """DFO freshwater limit text -> (type, {uk, en}) or (None, None) when unknown."""
    s = en.strip()
    fixed = {"Non-retention": ("release", "Лише відпустити"), "Bait ban": ("gear", "Заборона наживки"),
             "Single barbless hook": ("gear", "Лише одинарний гачок без зазубрини"),
             "No fishing for salmon": ("closed", "Риболовлю на лосося закрито")}
    if s in fixed:
        typ, uk = fixed[s]
        return typ, B(uk, s)
    m = re.fullmatch(r"(\d+) (hatchery marked )?per day(, hatchery marked only)?(?:, only (\d+) over (\d+) cm)?", s)
    if not m:
        return None, None
    n, hm, hm_only, k, cm = m.groups()
    uk = f"{n} {plural_hatchery(n)} на день" if hm else f"{n} на день"
    if hm_only:
        uk += ", лише заводська" if n == "1" else ", лише заводські"
    if k:
        uk += f", з них ≤{k} понад {cm} см"
    return "retain", B(uk, s)


def sub_list(text, area, bad, where):
    """'29-1 to 29-5 and 29-8' | '29-6,29-7 and 29-9 to 29-17' | '28' | '28-1 to 28-4' -> [subareas]."""
    t = text.strip()
    if t == area:
        return list(C.AREA_SUBS[area])
    out = []
    for part in re.split(r",| and ", t):
        part = part.strip()
        m = re.fullmatch(rf"{area}-(\d+)(?: to {area}-(\d+))?", part)
        if not m:
            bad.add(f"{where}: cannot read subareas {text!r}")
            return []
        a, b = int(m[1]), int(m[2] or m[1])
        out += [f"{area}-{i}" for i in range(a, b + 1)]
    unknown = [s for s in out if s not in C.AREA_SUBS[area]]
    if unknown:
        bad.add(f"{where}: unknown subareas {unknown}")
    return out


def tr(text, table):
    """Ukrainian from `table` (English fallback); English with a capital first letter for display."""
    en = text[:1].upper() + text[1:]
    return B(table.get(text, en), en)


def last_updated(fragment):
    ds = re.findall(r"Last updated:\s*(\d{4}-\d{2}-\d{2})", fragment)
    return max(ds) if ds else None


# ---------------------------------------------------------------- Region 2 (fresh water)
def parse_region2(page, bad):
    frag = cut(page, "<main", ["</main>"], "region2", bad)
    modified = re.search(r"Date modified:.*?(\d{4}-\d{2}-\d{2})", page, re.S)
    tabs = [t for t in tables(frag) if t[0][:5] == ["Waters", "Specific area", "Species", "Dates", "Limits/Gear"]]
    if len(tabs) != 1:
        bad.add("region2: salmon table not found or its columns changed")
        return [], None
    waters = {}
    for row in tabs[0][1]:
        cells = [c.text for c in row[:5]]
        if len(cells) < 5 or " - See " in cells[0]:
            continue                                  # cross-reference rows ("Sumas River - See Chilliwack River")
        wname, area, sp_t, dates_t, lim_c = cells[0], cells[1], cells[2], cells[3], row[4]
        where = f"region2 / {wname}"
        meta = C.SECTION_WATERS.get(area)
        if meta:
            area = ""
        else:
            meta = C.FRESH.get(wname)
        if not meta:
            bad.add(f"{where}: water is not on the map yet (add it to dfo/catalog.py and build/geo.json)")
            continue
        sp = species_of(sp_t)
        dates = parse_dates(dates_t)
        links = [{"id": t, "url": u} for t, u in lim_c.links if re.fullmatch(r"FN\d+", t)]
        lim_text = lim_c.text
        for l in links:
            lim_text = lim_text.replace(l["id"], "").strip()
        typ, lim = fresh_limit(lim_text)
        if not sp:
            bad.add(f"{where}: unknown species {sp_t!r}")
        if not dates:
            bad.add(f"{where}: cannot read dates {dates_t!r}")
        if not typ:
            bad.add(f"{where}: unknown limit wording {lim_text!r}")
        if not (sp and dates and typ):
            continue
        w = waters.setdefault(meta["id"], {"meta": meta, "areas": []})
        if area not in w["areas"]:
            w["areas"].append(area)
        rule = {"sp": sp, "from": dates[0], "to": dates[1], "lim": lim, "type": typ, "_area": area}
        if links:
            rule["fn"] = links
        w.setdefault("rules", []).append(rule)
    if len(waters) < 15:
        bad.add(f"region2: only {len(waters)} waters parsed, expected about 23")

    out = []
    for wid, w in waters.items():
        m = w["meta"]
        e = {"id": wid, "d": m["d"], "name": m["name"], "notes": m.get("notes", [])}
        if m.get("lake"):
            e["lake"] = True
        areas = [a for a in w["areas"]]
        if len(areas) == 1:
            if areas[0]:
                e["sec"] = tr(areas[0], C.AREA_UK)
            elif m.get("sec"):
                e["sec"] = m["sec"]
            for r in w["rules"]:
                r.pop("_area")
        else:
            keys = "abcdefgh"
            e["secs"] = {keys[i]: tr(a, C.AREA_UK) for i, a in enumerate(areas)}
            if m.get("sec"):
                e["sec"] = m["sec"]
            for r in w["rules"]:
                r["sec"] = keys[areas.index(r.pop("_area"))]
        e["rules"] = w["rules"]
        out.append(e)
    return out, (modified[1] if modified else None)


# ---------------------------------------------------------------- Areas 28 / 29 (tidal)
def gear_text(details):
    """'You are not allowed ...: X (dates)' -> (X, dates) list."""
    body = re.sub(r"^You are not allowed to harvest using the following gears and methods:\s*", "", details)
    return [(m[1].strip(), m[2]) for m in re.finditer(r"(.+?)\s*\(([^()]*?)\s*\)", body)]


def note(place, typ, details, species):
    """One DFO restriction row as a bilingual popup note."""
    prefix_en = f"{place}: " if place else ""
    prefix_uk = f"{C.PLACE_UK.get(place, place)}: " if place else ""
    sp_en = f"{species.split(' (')[0]} · " if species not in ("", "Finfish", "Salmon") else ""
    sp_uk = sp_en and f"{sp_en}"
    typ_uk = C.TYPE_UK.get(typ, typ)
    items = gear_text(details) if re.search(r"\([^()]*(to|round)[^()]*\)\s*$", details) else []
    if items:
        en_parts, uk_parts = [], []
        for what, dates in items:
            rng = parse_dates(dates)
            r = fmt_range(*rng) if rng else B(dates, dates)
            en_parts.append(f"{what} ({r['en']})")
            uk_parts.append(f"{C.DETAIL_UK.get(what, what)} ({r['uk']})")
        en, uk = "; ".join(en_parts), "; ".join(uk_parts)
    else:
        en, uk = details, C.DETAIL_UK.get(details, details)
    return B(f"{prefix_uk}{sp_uk}{typ_uk}: {uk}", f"{prefix_en}{sp_en}{typ}: {en}")


def parse_tidal(area, page, bad):
    name = f"area{area}"
    frag = cut(page, '<h2 id="salmon"', ["<summary>Other finfish", '<h2 id="finfish"'], name, bad)
    ts = tables(frag)
    sp_tab = next((t for t in ts if t[0][:6] == ["Species", "Areas", "Min size", "Gear", "Daily Limits", "Status"]), None)
    rs_tab = next((t for t in ts if t[0][:4] == ["Species", "Areas", "Restriction type", "Restriction details"]), None)
    ds_tab = next((t for t in ts if t[0][:3] == ["Area", "Map", "Area description"]), None)
    if not sp_tab or not rs_tab:
        bad.add(f"{name}: salmon tables not found or their columns changed")
        return [], None
    subs = C.AREA_SUBS[area]
    per = {s: [] for s in subs}            # subarea -> rules
    seen = set()
    species = ""
    for row in sp_tab[1]:
        c = [x.text for x in row[:6]]
        species = c[0] or species
        sp = species_of(species)
        where = f"{name} / {species or '?'}"
        if not sp or sp == "all":
            bad.add(f"{where}: unknown species {species!r}")
            continue
        targets = sub_list(c[1], area, bad, where)
        seen.update(targets)
        status, limit_t, size_t = c[5].strip().lower(), c[4], c[2]
        if status == "closed":
            continue
        if status == "non retention":
            rule = {"sp": sp, "from": YEAR[0], "to": YEAR[1], "type": "release", "lim": B("Лише відпустити", "Non-retention (release only)")}
        elif status == "open":
            n = re.match(r"\s*(\d+)", limit_t)
            cm = re.fullmatch(r"\s*(\d+)\s*cm\s*", size_t)
            if not n or not cm:
                bad.add(f"{where}: cannot read limit {limit_t!r} / size {size_t!r}")
                continue
            n, cm = n[1], cm[1]
            wild = re.search(r"(\d+) - Wild", limit_t)
            if n == "0":
                continue
            if wild and wild[1] == "0":
                lim = B(f"{n} на день, лише заводські (диких — 0), мін. {cm} см", f"{n} per day, hatchery marked only (wild: 0), min. {cm} cm")
            elif wild or "Combined" in limit_t:
                bad.add(f"{where}: unknown combined limit {limit_t!r}")
                continue
            else:
                lim = B(f"{n} на день, мін. {cm} см", f"{n} per day, min. {cm} cm")
            rule = {"sp": sp, "from": YEAR[0], "to": YEAR[1], "type": "retain", "lim": lim}
        else:
            bad.add(f"{where}: unknown status {c[5]!r}")
            continue
        for s in targets:
            per[s].append(rule)
    missing = [s for s in subs if s not in seen]
    if missing:
        bad.add(f"{name}: subareas missing from the species table: {missing}")

    notes_sub = {s: [] for s in subs}
    area_notes, area_gear, closed_subs, mouth = [], [], set(), {}
    species = ""
    for row in rs_tab[1]:
        c = [x.text for x in row[:4]]
        species = c[0] or species
        place, typ, details = c[1], c[2], c[3]
        if place == "Coastwide":
            continue                                    # coastwide rules are in the page's general rules text
        target = C.PLACES.get(place)
        if target is None and re.fullmatch(rf"{area}(-\d+)?((,| to | and ){area}-\d+)*", place):
            target = sub_list(place, area, bad, f"{name} / restriction {place!r}")
        if target == "mouth":
            if typ == "Closed":
                rng = re.search(r"\(([^()]*)\)\s*$", details)
                mouth[species_of(species)] = parse_dates(rng[1]) if rng else None
            continue
        whole_area = isinstance(target, list) and set(target) == set(subs)
        if typ == "Gear Restriction" and whole_area and species in ("Salmon", "Finfish", ""):
            for what, dates in gear_text(details):
                rng = parse_dates(dates)
                if not rng:
                    bad.add(f"{name}: cannot read gear dates {dates!r}")
                    continue
                area_gear.append({"sp": "all", "from": rng[0], "to": rng[1], "type": "gear",
                                  "lim": B(f"Заборонено: {C.DETAIL_UK.get(what, what)}", f"Not allowed: {what}")})
            continue
        if typ == "Reminder" and details.startswith("Closed to harvesting"):
            for sub, paren in re.findall(rf"({area}-\d+) \(([^)]*)\)", details):
                if "partial" not in paren:
                    closed_subs.add(sub)
        named = place in C.PLACES or target is None      # a place name, not a subarea list like "28-8,28-10"
        n = note(place if named else "", typ, details, species)
        if isinstance(target, list) and not whole_area:
            for s in target:
                if s in notes_sub and n not in notes_sub[s]:
                    notes_sub[s].append(n)
        elif n not in area_notes:
            area_notes.append(n)                        # whole area, or a place name that is not in the catalog

    for s in subs:
        per[s] = per[s] + area_gear
        if s in closed_subs:
            per[s] = [{"sp": "all", "from": YEAR[0], "to": YEAR[1], "type": "closed",
                       "lim": B("Закрито для вилову (навігаційне закриття)", "Closed to harvesting (navigational closure)")}] + area_gear
        elif not any(r["type"] in ("retain", "release") for r in per[s]):
            per[s] = [{"sp": "all", "from": YEAR[0], "to": YEAR[1], "type": "closed",
                       "lim": B("Закрито для лосося (ліміт 0)", "Closed to salmon (limit 0)")}] + area_gear

    # group subareas with identical rules
    groups = {}
    for s in subs:
        groups.setdefault(json.dumps(per[s], sort_keys=True, ensure_ascii=False), []).append(s)
    as_of = last_updated(frag)
    out = []
    for i, members in enumerate(groups.values()):
        label = compact(members)
        e = {"id": f"a{area}-{i + 1}", "d": f"a{area}", "tidal": True, "subs": members, "subsLabel": label,
             "name": C.GROUP_NAMES.get(frozenset(members), B(f"Area {area}: {label}", f"Area {area}: {label}")),
             "rules": per[members[0]], "notes": area_notes, "asOf": as_of,
             "subNotes": {s: notes_sub[s] for s in members if notes_sub[s]}}
        out.append(e)

    if mouth:
        dates = set(mouth.values())
        if set(mouth) != {"chinook", "coho", "chum", "pink", "sockeye"} or len(dates) != 1 or None in dates:
            bad.add(f"{name}: Fraser mouth closure is not the same for all five species: {mouth}")
        else:
            desc = next((r[2].text for r in (ds_tab[1] if ds_tab else []) if r[0].text == "Mouth of the Fraser River Salmon Closure"), "")
            desc = desc.replace("&#176;", "°").replace("&#39;", "'")
            if not all(k in desc for k in C.MOUTH_COORDS):
                bad.add(f"{name}: Fraser mouth closure boundary changed; update the polygon in build/build_tidal.py")
            fr, to = dates.pop()
            out.append({"id": f"a{area}-mouth", "d": f"a{area}", "tidal": True, "closure": True, "geom": "mouth",
                        "name": C.MOUTH_NAME, "sec": C.MOUTH_SEC, "subsLabel": B("частина 29-3", "part of 29-3"),
                        "asOf": as_of, "notes": [],
                        "rules": [{"sp": "all", "from": fr, "to": to, "type": "closed", "lim": B("Закрито для всіх видів лосося", "Closed to all salmon")}]})
    return out, as_of


def compact(subs):
    """['29-1','29-2','29-3','29-8'] -> '29-1…29-3, 29-8'."""
    nums = [(s.split("-")[0], int(s.split("-")[1])) for s in subs]
    parts, i = [], 0
    while i < len(nums):
        j = i
        while j + 1 < len(nums) and nums[j + 1][1] == nums[j][1] + 1:
            j += 1
        a, b = nums[i], nums[j]
        parts.append(f"{a[0]}-{a[1]}" if i == j else f"{a[0]}-{a[1]}…{b[0]}-{b[1]}" if j > i + 1 else f"{a[0]}-{a[1]}, {b[0]}-{b[1]}")
        i = j + 1
    return ", ".join(parts)


# ---------------------------------------------------------------- snapshots (human-readable diff for issues and git history)
def to_text(fragment):
    s = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", fragment, flags=re.S | re.I)
    s = re.sub(r'<a\b[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r"\2 [\1]", s, flags=re.S | re.I)
    s = re.sub(r"</t[dh]>", " | ", s, flags=re.I)
    s = re.sub(r"<br\s*/?>|</(p|h\d|li|tr|div|table|ul|ol|dt|dd|summary|caption)>", "\n", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    import html
    s = html.unescape(s).replace("\xa0", " ")
    lines = (re.sub(r"\s+", " ", ln).strip() for ln in s.splitlines())
    return "\n".join(ln for ln in lines if ln and ln != "|") + "\n"


SNAP_CUT = {"region2": ("<main", ["</main>"]), "area28": ('<h2 id="salmon"', ["<summary>Other finfish"]),
            "area29": ('<h2 id="salmon"', ["<summary>Other finfish"])}


def main():
    use_cache = "--cache" in sys.argv
    cache = DFO / "cache"
    cache.mkdir(exist_ok=True)
    pages = {}
    for k, (_, url) in PAGES.items():
        f = cache / f"{k}.html"
        pages[k] = f.read_text(encoding="utf-8") if use_cache else fetch(url)
        f.write_text(pages[k], encoding="utf-8")

    bad = Problems()
    fresh, r2_date = parse_region2(pages["region2"], bad)
    t28, a28_date = parse_tidal("28", pages["area28"], bad)
    t29, a29_date = parse_tidal("29", pages["area29"], bad)
    today = date.today().isoformat()
    new_rules = {
        "sources": {k: {"title": PAGES[k][0], "url": PAGES[k][1], "dfoDate": d}
                    for k, d in (("region2", r2_date), ("area28", a28_date), ("area29", a29_date))},
        "waters": fresh + t28 + t29,
    }

    old_rules = json.loads(RULES.read_text(encoding="utf-8")) if RULES.exists() else None
    status = json.loads(STATUS.read_text(encoding="utf-8")) if STATUS.exists() else {}
    old_status = json.dumps(status, sort_keys=True)
    new_block = False

    # snapshots: plain text of each page, committed so that git history shows what DFO changed
    snap_dir = DFO / "snapshots"
    snap_dir.mkdir(exist_ok=True)
    diffs = []
    for k in PAGES:
        start, ends = SNAP_CUT[k]
        text = to_text(cut(pages[k], start, ends, k, Problems()))
        p = snap_dir / f"{k}.txt"
        old = p.read_text(encoding="utf-8") if p.exists() else None
        if old != text:
            if old is not None:
                d = "".join(difflib.unified_diff(old.splitlines(True), text.splitlines(True), f"{k} (before)", f"{k} ({today})", n=2))
                diffs.append((k, d[:15000]))
            p.write_text(text, encoding="utf-8", newline="\n")

    if bad:
        reasons = list(bad)
        pend = status.get("pending") or {}
        if pend.get("reasons") != reasons:
            new_block = True
        status["pending"] = {"since": pend.get("since", today), "reasons": reasons}
        print("BLOCKED — rules.json kept as is:\n  " + "\n  ".join(reasons))
    else:
        status.pop("pending", None)
        if new_rules != old_rules:
            RULES.write_text(json.dumps(new_rules, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
            status["rulesChanged"] = today
            print("rules.json updated")
        else:
            print("rules unchanged")
    STATUS.write_text(json.dumps(status, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")

    if new_block:
        out = DFO / "out"
        out.mkdir(exist_ok=True)
        body = [f"DFO pages changed in a way the map updater does not understand, so the map keeps the rules from "
                f"{status.get('rulesChanged', 'the last update')} and shows a warning.\n", "**Reasons**\n"]
        body += [f"- {r}" for r in status["pending"]["reasons"]]
        body.append("\nFix `dfo/catalog.py` (or the parser in `dfo/update.py`), push, and the next run publishes the new rules.\n")
        for k, d in diffs:
            body.append(f"### {PAGES[k][0]}\n{PAGES[k][1]}\n\n```diff\n{d}```\n")
        (out / "issue.md").write_text(f"Map update blocked: DFO rules need a manual check ({today})\n" + "\n".join(body),
                                      encoding="utf-8", newline="\n")

    changed = old_status != json.dumps(status, sort_keys=True) or bool(diffs) or (not bad and new_rules != old_rules)
    gh = os.environ.get("GITHUB_OUTPUT")
    if gh:
        with open(gh, "a", encoding="utf-8") as f:
            f.write(f"changed={'true' if changed else 'false'}\nnew_block={'true' if new_block else 'false'}\n")
            f.write(f"checked_at={datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}\n")


if __name__ == "__main__":
    main()
