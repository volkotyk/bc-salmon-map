"""Inline Leaflet CSS, geo.json, rules.json, status.json, species/*.webp and reports.json into template.html.

CHECKED_AT (ISO time of the last successful DFO check) is taken from the environment when set.
reports.json (from fetch_reports.py) is optional: without it the page hides the "running now" panel.

Writes:
  ../index.html        standalone page for GitHub Pages or any static host
  out/artifact.html    body-only variant for the claude.ai artifact host, which adds its own <html>/<head>
"""
import base64, glob, json, os

t =open("template.html", encoding="utf-8").read()
css = open("leaflet.css", encoding="utf-8").read()
geo = open("geo.json", encoding="utf-8").read()
rules = open("rules.json", encoding="utf-8").read().replace("</", r"<\/")  # <\/ is valid JSON and keeps </script> out
status = json.load(open("status.json", encoding="utf-8"))
status["checkedAt"] = os.environ.get("CHECKED_AT") or None
status = json.dumps(status, ensure_ascii=False).replace("</", r"<\/")
# Species illustrations as data URIs: the page stays one file and works offline after the first load.
species = json.dumps({os.path.basename(p)[:-5]: "data:image/webp;base64," + base64.b64encode(open(p, "rb").read()).decode()
                      for p in sorted(glob.glob("species/*.webp"))})
reports = open("reports.json", encoding="utf-8").read() if os.path.exists("reports.json") else "{}"
# Report titles come from other sites: escape every "<" (also "<!--") so no text can end the <script> block.
reports = reports.replace("<", "\\u003c")
# Reports go in last, so a title that contains "__GEO__" or "__RULES__" stays plain text.
body = (t.replace("/*__LEAFLET_CSS__*/", css).replace("__GEO__", geo)
        .replace("__RULES__", rules).replace("__STATUS__", status).replace("__SPECIES__", species)
        .replace("__REPORTS__", reports))

os.makedirs("out", exist_ok=True)
open("out/artifact.html", "w", encoding="utf-8").write(body)

HEAD = """<!doctype html>
<html lang="uk">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#ffffff" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#142124" media="(prefers-color-scheme: dark)">
<meta name="author" content="Volodymyr Kotyk">
<meta name="description" content="Where to fish for salmon in the BC Lower Mainland: DFO Region 2 rivers and tidal Areas 28 and 29 by species and date. Українською та англійською.">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Cpath d='M3 16c5-7 13-8 20-3l6-4v14l-6-4c-7 5-15 4-20-3z' fill='%23c2410c'/%3E%3C/svg%3E">
</head>
<body style="margin:0">
"""
open("../index.html", "w", encoding="utf-8").write(HEAD + body + "\n</body>\n</html>\n")
print("index.html bytes", len((HEAD + body).encode()))
