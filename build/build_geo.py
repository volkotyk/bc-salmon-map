"""Build geo.json for the salmon map from OSM (Overpass) and Natural Earth extracts."""
import json
from collections import defaultdict
from shapely.geometry import LineString, MultiLineString, Polygon, box, mapping, shape, Point
from shapely.ops import unary_union, polygonize, linemerge, substring

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


def P(lat, lon):
    return Point(lon, lat)


def section(g, seed, cuts, gap=0.0004):
    """Keep the part of the line network g that seed reaches without passing a cut point.

    OSM sometimes breaks a river for a few metres (e.g. at a culvert). A loose line end is joined to the
    nearest other line end within `gap` degrees (about 30-45 m), before the cuts, so the walk can continue.
    """
    segs = list(getattr(g, "geoms", [g]))
    ends = [(i, e) for i, s in enumerate(segs) for e in (s.coords[0], s.coords[-1])]
    deg = defaultdict(int)
    for _, e in ends:
        deg[e] += 1
    for i, e in ends:
        near = [(Point(e).distance(Point(f)), f) for j, f in ends if j != i and f != e]
        d, f = min(near, default=(gap, None))
        if deg[e] == 1 and d < gap:
            segs.append(LineString([e, f]))
    stops = set()
    for c in cuts:
        i = min(range(len(segs)), key=lambda j: segs[j].distance(c))
        s, d = segs[i], segs[i].project(c)
        stops.add(s.interpolate(d).coords[0])
        segs[i:i + 1] = [x for x in (substring(s, 0, d), substring(s, d, s.length)) if x.length > 0]
    at = defaultdict(list)
    for i, s in enumerate(segs):
        for end in (s.coords[0], s.coords[-1]):
            at[end].append(i)
    assert stops <= at.keys(), "a cut point is not a line end"
    todo = [min(range(len(segs)), key=lambda j: segs[j].distance(seed))]
    seen = set(todo)
    while todo:
        s = segs[todo.pop()]
        for end in (s.coords[0], s.coords[-1]):
            if end not in stops:
                nxt = [j for j in at[end] if j not in seen]
                seen.update(nxt)
                todo += nxt
    g = unary_union([segs[i] for i in seen])
    return linemerge(g) if g.geom_type == "MultiLineString" else g


def ml(*names, clip=None, seed=None, cuts=()):
    ls = [l for n in names for l in lines.get(n, [])]
    g = unary_union(ls)
    if g.geom_type == "MultiLineString":
        g = linemerge(g)
    if clip is not None:
        g = g.intersection(clip)
    if seed is not None:
        g = section(g, seed, cuts)
    return g.simplify(0.0002)


# Section limits from the DFO table (Region 2 page), the tidal boundaries and the "No Fishing" limits of the
# BC Freshwater Fishing Regulations Synopsis 2025-2027, Region 2. A cut is the OSM object that the text names.
# The seed is any point inside the section. Waters without cuts are open along their full OSM length.
WATERS = {
    "alouette": ml("Alouette River", "South Alouette River", seed=P(49.24095, -122.62241),   # 216 Street bridge
                   cuts=[P(49.24650, -122.53467)]),     # Allco Park boundary signs (coordinates from the Synopsis)
    "n-alouette": ml("North Alouette River", clip=box(-122.75, 49.2, -122.4, 49.35)),
    "ashlu": ml("Ashlu Creek"),
    "capilano": ml("Capilano River", seed=P(49.32693, -123.13194),     # Marine Drive bridge
                   cuts=[P(49.32189, -123.13958),                      # CN rail bridge: tidal boundary
                         P(49.35534, -123.11082)]),                    # Cable Pool Bridge, 100 m below the fish fence
    "chapman": ml("Chapman Creek", seed=P(49.44062, -123.72217),       # Hwy 101 bridge
                  cuts=[P(49.47169, -123.72523)]),     # 100 m below the falls: 450 m upstream of the 2L47 power line
    "cheakamus": ml("Cheakamus River"),
    "chehalis": ml("Chehalis River", seed=P(49.29872, -121.93542),     # Morris Valley Road bridge
                   cuts=[P(49.38735, -122.02683)]),     # Maisel FSR bridge, the logging bridge below Chehalis Lake
    "chilliwack": ml("Chilliwack River", "Vedder River", "Vedder Canal", "Sumas River",
                     seed=P(49.09739, -121.96459),                     # Vedder Bridge
                     cuts=[P(49.07827, -121.71067),                    # 100 m below the Slesse Creek mouth
                           P(49.11391, -122.11114)]),                  # Barrowtown Pumping Station
    "coquitlam": ml("Coquitlam River", seed=P(49.26905, -122.78000),   # Lougheed Highway bridge
                    cuts=[P(49.22693, -122.80634),                     # Mary Hill Bypass bridge: tidal boundary
                          P(49.35411, -122.77674)]),                   # Coquitlam Dam
    "deboville": ml("De Boville Slough"),
    "harrison": ml("Harrison River"),
    "kanaka": ml("Kanaka Creek", seed=P(49.19906, -122.55672),         # 240 Street bridge
                 cuts=[P(49.20257, -122.58081),                        # CPR bridge: tidal boundary
                       P(49.20726, -122.53638)]),                      # 112 Avenue bridge
    "little-campbell": ml("Campbell River", seed=P(49.01238, -122.73625),   # 500 kV line crossing
                          cuts=[P(49.01280, -122.77796),               # BNSF rail bridge: tidal boundary
                                P(49.02392, -122.71943)]),             # 12 Avenue bridge
    "mamquam": ml("Mamquam River"),
    "nicomekl": ml("Nicomekl River", seed=P(49.08585, -122.73537),     # 176 Street bridge
                   cuts=[P(49.05772, -122.86968),                      # BNSF swing bridge: tidal boundary
                         P(49.10053, -122.64402)]),                    # 208 Street bridge
    "nicomen": ml("Nicomen Slough", "Dewdney Slough", seed=P(49.16308, -122.19334),   # Lougheed Highway bridge
                  cuts=[P(49.2097, -122.0111)]),       # Siddle (Bell's) Creek mouth (BC Geographical Names)
    "norrish": ml("Norrish Creek"),
    "serpentine": ml("Serpentine River", seed=P(49.09437, -122.80116),  # 152 Street bridge
                     cuts=[P(49.13221, -122.75648)]),  # 168 Street bridge; the BNSF tidal boundary is past the OSM line end
    "squamish": ml("Squamish River", "Powerhouse Channel"),
    "stave": ml("Stave River", seed=P(49.17251, -122.42323),           # Lougheed Highway bridge
                cuts=[P(49.17198, -122.42361),                         # CPR bridge: DFO limit and tidal boundary
                      P(49.19590, -122.40761)]),                       # Ruskin Dam (the BC Hydro dam)
    "fraser-closed": ml("Fraser River", clip=box(-122.31, 48.9, E, 49.6), seed=P(49.20486, -121.77699),  # Agassiz bridge
                        cuts=[P(49.12606, -122.30047)]),               # Mission Railway Bridge (CPR)
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
