"""Rebuild the map from scratch, or only re-assemble the page.

  python run_all.py            fetch OSM + DFO data, rebuild geo.json / city.json, write ../index.html
  python run_all.py --offline  skip downloads, reuse the raw files already in this folder
  python run_all.py --page     only re-assemble ../index.html from template.html + geo.json + city.json
"""
import subprocess, sys

FETCH = ["osm.py", "fetch_coast.py", "fetch_subareas.py", "osm_city.py"]
BUILD = ["build_geo.py", "build_tidal.py"]
FETCH_AFTER_GEO = ["osm_minor_bbox.py"]          # needs geo.json (river geometry) to pick street boxes
CITY = ["build_city.py"]
PAGE = ["assemble.py"]

args = set(sys.argv[1:])
if "--page" in args:
    steps = PAGE
elif "--offline" in args:
    steps = BUILD + CITY + PAGE
else:
    steps = FETCH + BUILD + FETCH_AFTER_GEO + CITY + PAGE

for s in steps:
    print(f"== {s}", flush=True)
    subprocess.run([sys.executable, s], check=True)
