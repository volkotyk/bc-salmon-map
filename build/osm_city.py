"""Fetch city context from OSM: major roads, place names, parks, boat launches.

Usage: python osm_city.py [roads] [places] [poi]   (no arguments = all)
Minor streets near rivers come from osm_minor_bbox.py.
"""
import json, requests

BBOX = "48.95,-124.7,50.35,-121.35"
Q = {
    "roads": f"""[out:json][timeout:600];
way["highway"~"^(motorway|trunk|primary|secondary|tertiary)$"]({BBOX});
out tags geom;""",
    "places": f"""[out:json][timeout:300];
node["place"~"^(city|town|village|suburb|neighbourhood|hamlet)$"]({BBOX});
out body;""",
    "poi": f"""[out:json][timeout:300];
(
  nwr["leisure"="slipway"]({BBOX});
  nwr["leisure"="fishing"]({BBOX});
  nwr["leisure"="park"]["name"]({BBOX});
  nwr["boundary"~"protected_area|national_park"]["name"]({BBOX});
);
out tags center;""",
}
EP = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]
import sys
for key, q in [(k, Q[k]) for k in (sys.argv[1:] or Q)]:
    for url in EP:
        try:
            r = requests.post(url, data={"data": q}, timeout=700, headers={"User-Agent": "salmon-map-build/1.0"})
            r.raise_for_status()
            d = r.json()
            break
        except Exception as e:
            print("fail", key, url, e)
    json.dump(d, open(f"city_{key}.json", "w"))
    print(key, len(d["elements"]))
