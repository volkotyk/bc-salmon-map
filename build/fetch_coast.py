"""Fetch the OSM coastline (for land polygons) and a few extra waterways into coast.json."""
import json, requests

Q = """[out:json][timeout:240];
(
 way["natural"="coastline"](48.95,-124.7,50.35,-121.35);
 way["waterway"]["name"~"Campbell|Dewdney|Nicomen"](48.95,-123.0,49.3,-121.9);
);
out geom;"""
for url in ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]:
    try:
        r = requests.post(url, data={"data": Q}, timeout=300, headers={"User-Agent": "bc-salmon-map-build/1.0"})
        r.raise_for_status()
        break
    except Exception as e:
        print("fail", url, e)
d = r.json()
json.dump(d, open("coast.json", "w"))
print("coast.json elements", len(d["elements"]))
