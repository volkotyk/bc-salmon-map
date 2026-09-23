"""Rebuild the map from scratch, or only re-assemble the page.

  python run_all.py            fetch OSM + DFO data and reports, rebuild geo.json, write ../index.html
  python run_all.py --offline  skip downloads, reuse the raw files already in this folder
  python run_all.py --page     only re-assemble ../index.html from template.html + geo.json (+ reports.json if present)
"""
import subprocess, sys

FETCH = ["osm.py", "fetch_coast.py", "fetch_subareas.py", "fetch_reports.py"]
BUILD = ["build_geo.py", "build_tidal.py"]
PAGE = ["assemble.py"]

args = set(sys.argv[1:])
if "--page" in args:
    steps = PAGE
elif "--offline" in args:
    steps = BUILD + PAGE
else:
    steps = FETCH + BUILD + PAGE

for s in steps:
    print(f"== {s}", flush=True)
    subprocess.run([sys.executable, s], check=True)
