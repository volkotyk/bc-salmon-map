"""Fetch the water level of the map rivers for the page. Standard library only.

Source: Environment and Climate Change Canada (ECCC), real-time hydrometric data, OGC API
(https://api.weather.gc.ca). The data are provisional. The API keeps about 30 days of 5-minute
readings, so one run gets the full window again and no history has to be stored between runs.

For each gauge in STATIONS the script keeps:
  name, ll     station name and position (the page puts a marker there)
  now          the newest reading: [UTC time, level m, discharge m3/s or null]
  t0, lv       hourly mean level for the last KEEP_HOURS hours: lv[i] is the hour t0 + i, null for no data

Writes hydro.json next to this script. The file is committed: git history keeps the daily snapshots.
A gauge that fails keeps its data from the previous snapshot and is logged as a warning; the page hides
a gauge whose newest reading is too old. With GITHUB_OUTPUT set, it writes changed=true when the data
(not only the time stamp) differ from the previous snapshot.

  python fetch_hydro.py            deploy mode: warnings only
  python fetch_hydro.py --strict   PR check: exit code 1 when a gauge failed
"""
import json, os, re, sys, urllib.parse
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fetch_reports import dump, fetch, warn, warnings

HERE = Path(__file__).resolve().parent
OUT = HERE / "hydro.json"
API = "https://api.weather.gc.ca/collections/{}/items?"
KEEP_HOURS = 14 * 24

# ECCC gauge -> water id of build/rules.json. One gauge per water: the real-time gauge nearest to the
# fishing section. Waters without a real-time gauge (Ashlu, Chapman, Stave below Ruskin, the sloughs,
# Serpentine, Little Campbell, Norrish, the lakes) are left out.
STATIONS = {
    "08MH001": "chilliwack",   # Chilliwack River at Vedder Crossing
    "08GA031": "capilano",     # Capilano River at Canyon (below Cleveland Dam)
    "08GA022": "squamish",     # Squamish River near Brackendale
    "08GA043": "cheakamus",    # Cheakamus River near Brackendale
    "08GA075": "mamquam",      # Mamquam River above Ring Creek
    "08MH002": "coquitlam",    # Coquitlam River at Port Coquitlam
    "08MH005": "alouette",     # Alouette River near Haney
    "08MH006": "n-alouette",   # North Alouette River at 232nd Street
    "08MH076": "kanaka",       # Kanaka Creek near Webster Corners
    "08MH155": "nicomekl",     # Nicomekl River at 203 Street, Langley
    "08MG022": "harrison",     # Harrison River below Morris Creek (level only)
    "08MG001": "chehalis",     # Chehalis River near Harrison Mills
}
BBOX = "-124.5,48.9,-121.3,50.3"  # the map area: one request gets all the station positions


def get(collection, **query):
    query.setdefault("f", "json")
    return json.loads(fetch(API.format(collection) + urllib.parse.urlencode(query)))


SMALL = {"at", "near", "above", "below", "of", "the", "and"}


def title(name):
    """'NORTH ALOUETTE RIVER AT 232ND STREET' -> 'North Alouette River at 232nd Street'."""
    words = re.sub(r"[A-Za-z]+", lambda m: m.group(0).lower() if m.group(0).lower() in SMALL else m.group(0).capitalize(), name)
    return re.sub(r"(?<=\d)[A-Z]+", lambda m: m.group(0).lower(), words)


def stations():
    """{station id: {"name", "ll"}} for STATIONS, from the ECCC station list."""
    d = get("hydrometric-stations", PROV_TERR_STATE_LOC="BC", bbox=BBOX, limit=1000, skipGeometry="false",
            properties="STATION_NUMBER,STATION_NAME")
    out = {}
    for f in d["features"]:
        sid = f["properties"]["STATION_NUMBER"]
        if sid in STATIONS:
            lng, lat = f["geometry"]["coordinates"][:2]
            out[sid] = {"name": title(f["properties"]["STATION_NAME"]), "ll": [round(lng, 5), round(lat, 5)]}
    return out


def readings(sid, since):
    """Real-time readings since the given UTC time, oldest first: [(time, level, discharge), ...]."""
    start = since.strftime("%Y-%m-%dT%H:%M:%SZ")
    end = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    d = get("hydrometric-realtime", STATION_NUMBER=sid, datetime=f"{start}/{end}", limit=10000, sortby="DATETIME",
            skipGeometry="true", properties="DATETIME,LEVEL,DISCHARGE")
    if d.get("numberMatched", 0) > len(d["features"]):
        raise RuntimeError(f"{d['numberMatched']} readings, more than one page: raise the limit")
    return [(p["DATETIME"], p["LEVEL"], p["DISCHARGE"]) for p in (f["properties"] for f in d["features"])]


MISSING = 9999           # ECCC writes a missing level as 99999
SPIKE_M = 0.5            # a reading this far from the median of its neighbours is a sensor glitch
SPIKE_WINDOW = 6         # neighbours on each side (5-minute readings: half an hour)


def clean(levels):
    """Readings without the missing-value code and without single-reading spikes.
    The median of a centred window follows a real rise or fall, so only a glitch differs from it."""
    rows = [r for r in levels if abs(r[1]) < MISSING]
    vals = [r[1] for r in rows]
    out = []
    for i, r in enumerate(rows):
        near = sorted(vals[max(0, i - SPIKE_WINDOW):i + SPIKE_WINDOW + 1])
        if abs(r[1] - near[len(near) // 2]) <= SPIKE_M:
            out.append(r)
    return out


def gauge(sid, meta, t0):
    rows = readings(sid, t0)
    levels = clean([r for r in rows if r[1] is not None])
    if not levels:
        raise RuntimeError("no level readings in the window")
    hours = {}
    for iso, lv, _ in levels:
        hours.setdefault(iso[:13], []).append(lv)
    lv = [None] * KEEP_HOURS
    for key, vals in hours.items():
        i = int((datetime.fromisoformat(key + ":00+00:00") - t0).total_seconds() // 3600)
        if 0 <= i < KEEP_HOURS:
            lv[i] = round(sum(vals) / len(vals), 3)
    iso, level, flow = levels[-1]
    print(f"{sid} {meta['name']}: {len(rows)} readings, {sum(v is not None for v in lv)} hours, now {level} m, {flow} m3/s")
    return {"id": sid, "w": STATIONS[sid], **meta, "now": [iso[:16] + "Z", level, flow],
            "t0": t0.strftime("%Y-%m-%dT%H:00Z"), "lv": lv}


def main():
    try:
        prev = json.loads(OUT.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        prev = {}
    old = {s["id"]: s for s in prev.get("stations", [])}
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    t0 = now - timedelta(hours=KEEP_HOURS - 1)          # the current hour is the last slot
    try:
        meta = stations()
    except Exception as e:
        warn(f"hydro station list: {e} (station names and positions of the previous snapshot kept)")
        meta = {}
    out = []
    for sid in STATIONS:
        m = meta.get(sid) or ({k: old[sid][k] for k in ("name", "ll")} if sid in old else None)
        try:
            if not m:
                raise RuntimeError("not in the ECCC station list")
            out.append(gauge(sid, m, t0))
        except Exception as e:
            if sid in old:
                out.append(old[sid])
            warn(f"hydro {sid}: {e} ({'kept the previous snapshot' if sid in old else 'left out'})")
    data = {"generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"), "stations": out}
    OUT.write_text(dump(data), encoding="utf-8", newline="\n")
    changed = {k: v for k, v in data.items() if k != "generated"} != {k: v for k, v in prev.items() if k != "generated"}
    print(f"{OUT.name}: {len(out)} gauges, {'changed' if changed else 'no data change'}")
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as f:
            f.write(f"changed={'true' if changed else 'false'}\n")
    if "--strict" in sys.argv and warnings:
        sys.exit(f"--strict: {len(warnings)} gauge(s) failed")


if __name__ == "__main__":
    main()
