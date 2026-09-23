"""Build geo.json for the salmon map from OSM (Overpass) and Natural Earth extracts."""
import json
from collections import defaultdict
from shapely.geometry import LineString, MultiLineString, Polygon, box, mapping, shape, Point
from shapely.ops import unary_union, polygonize, linemerge

W, S, E, N = -124.7, 48.95, -121.35, 50.35
BB = box(W, S, E, N)


def rnd(g, nd=4):
    def r(c):
        if isinstance(c[0], (int, float)):
            return [round(c[0], nd), round(c[1], nd)]
        return [r(x) for x in c]
    m = mapping(g)
    return {"type": m["type"], "coordinates": r(m["coordinates"])}


def way_line(e):
    return LineString([(p["lon"], p["lat"]) for p in e["geometry"]])


# ---------- coastline -> land polygons ----------
coast = json.load(open("coast.json"))
coast_ways = [way_line(e) for e in coast["elements"]
              if e["tags"].get("natural") == "coastline" and len(e["geometry"]) > 1]
noded = unary_union([l.intersection(BB) for l in coast_ways] + [BB.exterior])
faces = list(polygonize(noded))
votes = defaultdict(int)
eps = 1e-5
from shapely.strtree import STRtree
tree = STRtree(faces)
for l in coast_ways:
    cs = list(l.coords)
    step = max(1, len(cs) // 6)
    for i in range(0, len(cs) - 1, step):
        (x1, y1), (x2, y2) = cs[i], cs[i + 1]
        dx, dy = x2 - x1, y2 - y1
        n = (dx * dx + dy * dy) ** .5
        if n == 0:
            continue
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        # OSM convention: land is on the left side of a coastline way.
        for sgn, v in ((1, 1), (-1, -1)):
            p = Point(mx - sgn * dy / n * eps, my + sgn * dx / n * eps)
            if not BB.contains(p):
                continue
            for idx in tree.query(p):
                if faces[idx].contains(p):
                    votes[idx] += v
                    break
land = unary_union([f for i, f in enumerate(faces) if votes[i] > 0])
print("faces", len(faces), "land faces", sum(1 for i in votes if votes[i] > 0))

# ---------- US / Canada split ----------
us_box = box(-123.1, S, E, 49.0)
us_land = land.intersection(us_box)
ca_land = land.difference(us_box)

# ---------- rivers and lakes ----------
osm = json.load(open("osm.json"))
extra = [e for e in coast["elements"] if "waterway" in e["tags"]]
lines = defaultdict(list)
lakes = {}
for e in osm["elements"] + extra:
    t = e["tags"]
    nm = t.get("name")
    if "waterway" in t and e["type"] == "way":
        lines[nm].append(way_line(e))
    elif t.get("natural") == "water":
        if e["type"] == "way":
            g = Polygon([(p["lon"], p["lat"]) for p in e["geometry"]])
        else:
            outers = [LineString([(p["lon"], p["lat"]) for p in m["geometry"]])
                      for m in e["members"] if m["role"] == "outer" and m.get("geometry")]
            polys = list(polygonize(linemerge(outers)))
            g = unary_union(polys)
        g = g.buffer(0)
        lakes[nm] = unary_union([lakes[nm], g]) if nm in lakes else g
print({k: len(v) for k, v in lines.items()})


def ml(*names, clip=None):
    ls = [l for n in names for l in lines.get(n, [])]
    g = unary_union(ls)
    if g.geom_type == "MultiLineString":
        g = linemerge(g)
    if clip is not None:
        g = g.intersection(clip)
    return g.simplify(0.0002)


# Clip boxes follow the legal descriptions on the DFO page (approximate).
WATERS = {
    "alouette": ml("Alouette River", "South Alouette River", clip=box(-122.75, 49.18, -122.45, 49.27)),
    "n-alouette": ml("North Alouette River", clip=box(-122.75, 49.2, -122.4, 49.35)),
    "ashlu": ml("Ashlu Creek"),
    "capilano": ml("Capilano River"),
    "chapman": ml("Chapman Creek"),
    "cheakamus": ml("Cheakamus River"),
    "chehalis": ml("Chehalis River", clip=box(-122.1, 49.2, -121.8, 49.47)),
    "chilliwack": ml("Chilliwack River", "Vedder River", "Vedder Canal", "Sumas River",
                     clip=box(-122.35, 49.0, -121.63, 49.25)),
    "coquitlam": ml("Coquitlam River", clip=box(-122.9, 49.2, -122.6, 49.355)),
    "deboville": ml("De Boville Slough"),
    "harrison": ml("Harrison River"),
    "kanaka": ml("Kanaka Creek"),
    "little-campbell": ml("Campbell River", clip=box(-122.9, 48.99, -122.6, 49.1)),
    "mamquam": ml("Mamquam River"),
    "nicomekl": ml("Nicomekl River"),
    "nicomen": ml("Nicomen Slough", "Dewdney Slough"),
    "norrish": ml("Norrish Creek"),
    "serpentine": ml("Serpentine River"),
    "squamish": ml("Squamish River", "Powerhouse Channel"),
    "stave": ml("Stave River", clip=box(-122.45, 49.1, -122.2, 49.2)),
    "fraser-closed": ml("Fraser River", clip=box(-122.305, 48.9, E, 49.6)),
}
LAKE_WATERS = {"khartoum": "Khartoum Lake", "lois": "Lois Lake"}
fraser_all = ml("Fraser River").intersection(BB)

out = {
    "land": rnd(ca_land.simplify(0.0004)),
    "us": rnd(us_land.simplify(0.0004)),
    "lakes": [rnd(g.simplify(0.0003)) for n, g in lakes.items() if n not in LAKE_WATERS.values()],
    "fraser": rnd(fraser_all),
    "waters": {k: rnd(v) for k, v in WATERS.items()},
}
for k, nm in LAKE_WATERS.items():
    out["waters"][k] = rnd(lakes[nm].simplify(0.0002))
for k, v in out["waters"].items():
    g = shape(v)
    print(k, g.geom_type, "empty" if g.is_empty else [round(x, 3) for x in g.bounds])
s = json.dumps(out, separators=(",", ":"))
open("geo.json", "w").write(s)
print("bytes", len(s))
