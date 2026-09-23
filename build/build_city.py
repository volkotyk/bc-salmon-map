"""Compact OSM city context (roads, places, parks, boat launches) into city.json."""
import json
from collections import defaultdict
from shapely.geometry import LineString, Point, shape
from shapely.ops import linemerge, unary_union
from shapely.strtree import STRtree

CLASSES = ["motorway", "trunk", "primary", "secondary", "tertiary", "minor"]
TOL = {"motorway": .00008, "trunk": .00008, "primary": .00006, "secondary": .00006, "tertiary": .00005, "minor": .00004}

geo = json.load(open("geo.json"))
fishing = unary_union([shape(g) for g in geo["waters"].values()])
near_fishing = fishing.buffer(0.015)          # ~1.5 km: parks worth naming near fishing water

groups = defaultdict(list)                      # (class, name) -> [LineString]
import os
for fn, forced in (("city_roads.json", None), ("city_minor_bbox.json", "minor")):
    if not os.path.exists(fn):
        print("skip", fn)
        continue
    for e in json.load(open(fn))["elements"]:
        if e["type"] != "way" or len(e.get("geometry", [])) < 2:
            continue
        cls = forced or e["tags"]["highway"]
        name = e["tags"].get("name") or e["tags"].get("ref")
        groups[(cls, name)].append(LineString([(p["lon"], p["lat"]) for p in e["geometry"]]))

names, name_ix, roads = [], {}, []
for (cls, name), ls in groups.items():
    g = unary_union(ls)
    if g.geom_type == "MultiLineString":
        g = linemerge(g)
    g = g.simplify(TOL[cls])
    parts = [g] if g.geom_type == "LineString" else list(getattr(g, "geoms", []))
    if name and name not in name_ix:
        name_ix[name] = len(names)
        names.append(name)
    for p in parts:
        cs = [(round(x * 1e5), round(y * 1e5)) for x, y in p.coords]
        flat, px, py = [], 0, 0
        for x, y in cs:
            if flat and x == px and y == py:
                continue
            flat += [x - px, y - py]
            px, py = x, y
        if len(flat) >= 4:
            roads.append([CLASSES.index(cls), name_ix[name] if name else -1, flat])

places = []
for e in json.load(open("city_places.json"))["elements"]:
    t = e["tags"]
    if "name" in t:
        places.append([t["name"], t["place"], round(e["lon"], 5), round(e["lat"], 5)])

parks, poi = [], []
for e in json.load(open("city_poi.json"))["elements"]:
    t = e["tags"]
    c = (e["lon"], e["lat"]) if e["type"] == "node" else (e.get("center", {}).get("lon"), e.get("center", {}).get("lat"))
    if c[0] is None:
        continue
    lon, lat = round(c[0], 5), round(c[1], 5)
    if t.get("leisure") in ("slipway", "fishing"):
        poi.append([t["leisure"], t.get("name", ""), lon, lat])
    elif "name" in t and ("wikidata" in t or near_fishing.contains(Point(c))):
        parks.append([t["name"], lon, lat])

out = {"names": names, "roads": roads, "places": places, "parks": parks, "poi": poi}
s = json.dumps(out, separators=(",", ":"), ensure_ascii=False)
open("city.json", "w", encoding="utf-8").write(s)
from collections import Counter
print("roads", len(roads), Counter(CLASSES[r[0]] for r in roads))
print("names", len(names), "places", len(places), Counter(p[1] for p in places))
print("parks", len(parks), "poi", len(poi), Counter(p[0] for p in poi))
print("bytes", len(s.encode()))
