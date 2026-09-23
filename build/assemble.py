"""Inline Leaflet CSS, geo.json and city.json into template.html.

Writes:
  ../index.html        standalone page for GitHub Pages or any static host
  out/artifact.html    body-only variant for the claude.ai artifact host, which adds its own <html>/<head>
"""
import os

t = open("template.html", encoding="utf-8").read()
css = open("leaflet.css", encoding="utf-8").read()
geo = open("geo.json", encoding="utf-8").read()
city = open("city.json", encoding="utf-8").read().replace("</", "<\\u002f")
body = t.replace("/*__LEAFLET_CSS__*/", css).replace("__GEO__", geo).replace("__CITY__", city)

os.makedirs("out", exist_ok=True)
open("out/artifact.html", "w", encoding="utf-8").write(body)

HEAD = """<!doctype html>
<html lang="uk">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="description" content="Where to fish for salmon in the BC Lower Mainland: DFO Region 2 rivers and tidal Areas 28 and 29 by species and date. Українською та англійською.">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Cpath d='M3 16c5-7 13-8 20-3l6-4v14l-6-4c-7 5-15 4-20-3z' fill='%23c2410c'/%3E%3C/svg%3E">
</head>
<body style="margin:0">
"""
open("../index.html", "w", encoding="utf-8").write(HEAD + body + "\n</body>\n</html>\n")
print("index.html bytes", len((HEAD + body).encode()))
