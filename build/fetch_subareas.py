"""Fetch DFO Pacific Fishery Management Subareas for Areas 28 and 29 into sub.geojson."""
import requests

URL = "https://egisp.dfo-mpo.gc.ca/arcgis/rest/services/Pacific/DFO_BC_PFMA_SUBAREAS_50K_V3_1/MapServer/0/query"
params = {"where": "MGNT_AREA IN (28,29)", "outFields": "MGNT_AREA,SUBAREA_,NAME,LABEL,SQ_KM",
          "outSR": 4326, "geometryPrecision": 5, "f": "geojson"}
r = requests.get(URL, params=params, timeout=120)
r.raise_for_status()
open("sub.geojson", "w", encoding="utf-8").write(r.text)
print("sub.geojson features", len(r.json()["features"]))
