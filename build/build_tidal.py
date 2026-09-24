"""Add DFO tidal subareas (Areas 28, 29) and the Mouth of the Fraser closure to geo.json."""
import json
from shapely.geometry import shape, mapping, Polygon, Point, LineString
from shapely.ops import unary_union, nearest_points

geo = json.load(open("geo.json"))
land = unary_union([shape(geo["land"]), shape(geo["us"])])
sub = json.load(open("sub.geojson"))


def rnd(g, nd=4):
    def r(c):
        if isinstance(c[0], (int, float)):
            return [round(c[0], nd), round(c[1], nd)]
        return [r(x) for x in c]
    m = mapping(g)
    return {"type": m["type"], "coordinates": r(m["coordinates"])}


subs, pts = {}, {}
for f in sub["features"]:
    lab = f["properties"]["LABEL"]
    g = shape(f["geometry"]).buffer(0)
    # Trim the 1:50K polygon to the OSM shoreline; keep river arms that the OSM coastline does not enter.
    water = g.difference(land)
    if water.area < 0.5 * g.area:
        water = g
    water = water.simplify(0.0003)
    subs[lab] = rnd(water)
    p = water.representative_point()
    pts[lab] = [round(p.x, 4), round(p.y, 4)]


# River arms below a tidal boundary (from build_geo.py) are tidal water, but the 1:50K polygons stop short of
# the boundary bridges. Add each arm, and the open water next to the bridge, to the nearest subarea;
# the arm is a ribbon about 50 m wide that runs on to the subarea edge. Nothing on the fresh side ("up") is added.
for a in geo.pop("arms", []):
    arm = unary_union([shape(a[k]) for k in ("cut", "line") if a[k]])
    sea = shape(a["sea"]) if a["sea"] else Polygon()
    lab = min(subs, key=lambda k: shape(subs[k]).distance(arm))
    poly = shape(subs[lab])
    link = LineString(nearest_points(arm.union(sea), poly))
    others = unary_union([shape(v) for k, v in subs.items() if k != lab])
    ribbon = unary_union([arm.buffer(0.0003), link.buffer(0.0003), sea]).difference(others).difference(shape(a["up"]))
    subs[lab] = rnd(unary_union([poly, ribbon]).simplify(0.0001))
    print("tidal arm", a["cut"]["coordinates"], "->", lab, round(link.length * 80000), "m link")


# One solid block per subarea: fill small holes (the 1:50K data has a few, e.g. at the Capilano mouth) and close
# gaps up to about 60 m wide, which the shoreline trim and the arm ribbons leave. Big islands (holes of 0.05 km2
# or more) stay open. A gap never takes water from another subarea.
KM2 = 1 / (111.32 * 72.6)                              # square degrees per km2 at 49.2 N
for lab in subs:
    poly = shape(subs[lab])
    solid = unary_union([poly, poly.buffer(0.0004, join_style=2).buffer(-0.0004, join_style=2)])
    solid = unary_union([Polygon(p.exterior, [h for h in p.interiors if Polygon(h).area >= 0.05 * KM2])
                         for p in getattr(solid, "geoms", [solid])])
    others = unary_union([shape(v) for k, v in subs.items() if k != lab])
    subs[lab] = rnd(unary_union([poly, solid.difference(others)]))


def dm(d, m):
    return d + m / 60


# Mouth of the Fraser River Salmon Closure: vertices from the DFO Area 29 description.
mouth = Polygon([(-dm(123, 20.404), dm(49, 17.519)), (-dm(123, 15.867), dm(49, 17.400)),
                 (-dm(123, 15.860), dm(49, 15.995)), (-dm(123, 15.860), dm(49, 15.936)),
                 (-dm(123, 16.772), dm(49, 15.443)), (-dm(123, 16.779), dm(49, 15.437)),
                 (-dm(123, 17.117), dm(49, 13.258)), (-dm(123, 20.797), dm(49, 13.349))])

geo["subs"] = subs
geo["subpts"] = pts
geo["mouth"] = rnd(mouth, 5)

# Which subarea holds each named spot closure (used for popup notes).
SPOTS = {"Whytecliff Park": (-123.292, 49.371), "Point Atkinson": (-123.264, 49.330),
         "Porteau Cove": (-123.236, 49.558), "Mannion Bay": (-123.330, 49.382),
         "Capilano mouth": (-123.137, 49.318), "Seymour mouth": (-123.030, 49.301),
         "Chapman ribbon": (-123.73, 49.44)}
for n, xy in SPOTS.items():
    p = Point(xy)
    best = min(subs, key=lambda k: shape(subs[k]).distance(p))
    print(n, "->", best, round(shape(subs[best]).distance(p), 4))

s = json.dumps(geo, separators=(",", ":"))
open("geo.json", "w").write(s)
print("bytes", len(s))
