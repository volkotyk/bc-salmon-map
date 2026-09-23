import json, requests
from shapely.geometry import shape
geo = json.load(open("geo.json"))
parts = []
for k, g in geo["waters"].items():
    if k == "fraser-closed":
        continue
    w, s, e, n = shape(g).bounds
    m = 0.01
    parts.append(f'way["highway"~"^(residential|unclassified|living_street|track|path|footway|cycleway|service)$"]({s-m:.4f},{w-m:.4f},{n+m:.4f},{e+m:.4f});')
q = "[out:json][timeout:900];(" + "".join(parts) + ");out tags geom;"
for url in ["https://overpass.kumi.systems/api/interpreter", "https://overpass-api.de/api/interpreter"]:
    try:
        r = requests.post(url, data={"data": q}, timeout=950, headers={"User-Agent": "salmon-map-build/1.0"})
        r.raise_for_status(); d = r.json(); break
    except Exception as ex:
        print("fail", url, ex)
fish = shape({"type": "GeometryCollection", "geometries": [g for k, g in geo["waters"].items() if k != "fraser-closed"]}).buffer(0.0063)  # ~700 m
from shapely.geometry import LineString
from shapely.prepared import prep
pf = prep(fish)
keep = []
for e in d["elements"]:
    t = e["tags"]
    if t.get("highway") == "service" and "service" in t:
        continue
    if len(e.get("geometry", [])) < 2:
        continue
    if pf.intersects(LineString([(p["lon"], p["lat"]) for p in e["geometry"]])):
        keep.append(e)
json.dump({"elements": keep}, open("city_minor_bbox.json", "w"))
print("raw", len(d["elements"]), "kept", len(keep))
