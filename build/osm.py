import json, os, requests
SP = os.path.dirname(os.path.abspath(__file__))
BBOX = "48.95,-124.7,50.35,-121.35"
NAMES = ["Alouette River", "North Alouette River", "South Alouette River", "Ashlu Creek", "Capilano River",
         "Chapman Creek", "Cheakamus River", "Chehalis River", "Chilliwack River", "Vedder River",
         "Vedder Canal", "Sumas River", "Coquitlam River", "De Boville Slough", "Fraser River",
         "Harrison River", "Kanaka Creek", "Little Campbell River", "Mamquam River", "Nicomekl River",
         "Nicomen Slough", "Dewdney Slough", "Norrish Creek", "Serpentine River", "Squamish River",
         "Stave River", "Powerhouse Channel",
         "Ruskin Channel", "Northrop Channel", "Thompson Creek"]  # Stave spawning channels (no fishing)
LAKES = ["Khartoum Lake", "Lois Lake", "Harrison Lake", "Stave Lake", "Pitt Lake", "Alouette Lake",
         "Chehalis Lake", "Chilliwack Lake", "Coquitlam Lake", "Capilano Lake", "Cultus Lake"]
rx = "^(" + "|".join(NAMES) + ")$"
lx = "^(" + "|".join(LAKES) + ")$"
q = f"""[out:json][timeout:180];
(
  way["waterway"~"river|stream|canal|ditch|drain|fish_pass"]["name"~"{rx}"]({BBOX});
  way["natural"="water"]["name"~"{lx}"]({BBOX});
  relation["natural"="water"]["name"~"{lx}"]({BBOX});
);
out geom;"""
for url in ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]:
    try:
        r = requests.post(url, data={"data": q}, timeout=240, headers={"User-Agent": "salmon-map-build/1.0"})
        r.raise_for_status()
        break
    except Exception as e:
        print("fail", url, e)
d = r.json()
json.dump(d, open(os.path.join(SP, "osm.json"), "w"))
from collections import Counter
print(len(d["elements"]))
print(Counter(e["tags"].get("name") for e in d["elements"]))
