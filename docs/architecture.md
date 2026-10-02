# Data sources and data flow (C4)

This page shows where the map gets its data, and which data come in automatically or by hand.
The diagrams use the [Mermaid C4 syntax](https://mermaid.js.org/syntax/c4.html). GitHub renders them in this file.

- **Automatic:** the GitHub Actions workflow `.github/workflows/pages.yml` gets the data. It runs every day at 15:23 and 16:41 UTC and on every push to `main`.
- **Manual:** a person reads a post or runs a script, edits a file in the repository and commits it.

## Level 1: system context

```mermaid
C4Context
  title Where the BC Salmon Map data comes from

  Boundary(auto, "Automatic: GitHub Actions cron") {
    System_Ext(dfo, "DFO", "Region 2, Area 28, Area 29 pages; FOS report of the Albion test fishery")
    System_Ext(psc, "PSC", "Whonnock and Qualark test-fishery PDFs")
    System_Ext(eccc, "ECCC", "Real-time hydrometric OGC API, 12 gauges")
    System_Ext(pa, "Tackle shops", "Pacific Angler and Fred's Custom Tackle fishing report Atom feeds")
    System_Ext(reddit, "Reddit", "r/fishingBC and r/chilliwack RSS feeds")
  }

  Boundary(core, "The map and its people") {
    System_Ext(tiles, "OSM tiles, Nominatim, CDNs", "Basemap tiles, place search, Leaflet JS, Google Fonts; at view time")
    Person(angler, "Angler", "Opens the map in a browser; My spots stay in localStorage")
    System(map, "BC Salmon Map", "GitHub Actions builds index.html, GitHub Pages serves it")
    Person(maint, "Maintainer", "Copies posts into CSV, fixes dfo/catalog.py, runs local scripts")
  }

  Boundary(manual, "Manual: a person copies or runs, then commits") {
    System_Ext(ig, "Instagram", "Posts and reels")
    System_Ext(fb, "Facebook", "Vedder River Chilliwack Fishing Report group")
    System_Ext(tt, "TikTok", "Videos")
    System_Ext(geo, "OSM Overpass, DFO ArcGIS", "River, lake, coast and subarea geometry")
    System_Ext(photos, "WDFW PDF, Wikimedia Commons", "Species images")
  }

  Rel(dfo, map, "auto: rules, Albion catch")
  Rel(psc, map, "auto: sockeye, pink catch")
  Rel(eccc, map, "auto: water level")
  Rel(pa, map, "auto: report links")
  Rel(reddit, map, "auto: filtered posts")

  Rel(ig, maint, "manual: reads")
  Rel(fb, maint, "manual: reads")
  Rel(tt, maint, "manual: reads")
  Rel(geo, maint, "manual: runs osm.py, fetch_subareas.py")
  Rel(photos, maint, "manual: runs fetch_species.py")

  Rel(maint, map, "manual: git push of CSV, catalog, geometry")
  Rel(map, maint, "auto: issue dfo-update")
  Rel(angler, map, "opens index.html")
  Rel(angler, tiles, "loads tiles, searches places")

  UpdateRelStyle(maint, map, $offsetX="10")
  UpdateRelStyle(map, maint, $offsetX="-130")

  UpdateElementStyle(ig, $bgColor="#BA7517", $borderColor="#854F0B")
  UpdateElementStyle(fb, $bgColor="#BA7517", $borderColor="#854F0B")
  UpdateElementStyle(tt, $bgColor="#BA7517", $borderColor="#854F0B")
  UpdateElementStyle(geo, $bgColor="#BA7517", $borderColor="#854F0B")
  UpdateElementStyle(photos, $bgColor="#BA7517", $borderColor="#854F0B")
  UpdateElementStyle(dfo, $bgColor="#0F6E56", $borderColor="#085041")
  UpdateElementStyle(psc, $bgColor="#0F6E56", $borderColor="#085041")
  UpdateElementStyle(eccc, $bgColor="#0F6E56", $borderColor="#085041")
  UpdateElementStyle(pa, $bgColor="#0F6E56", $borderColor="#085041")
  UpdateElementStyle(reddit, $bgColor="#0F6E56", $borderColor="#085041")

  UpdateLayoutConfig($c4ShapeInRow="1", $c4BoundaryInRow="3")
```

## Level 2: scripts and files

```mermaid
C4Container
  title Scripts and files that carry the data

  Boundary(ext, "External") {
    System_Ext(sources, "Automatic sources", "DFO, PSC, ECCC, Pacific Angler, Fred's Custom Tackle, Reddit")
    System_Ext(pages, "GitHub Pages", "Serves index.html")
  }

  Boundary(ci, "Runs in GitHub Actions (pages.yml)") {
    Container(update, "dfo/update.py", "Python stdlib", "Parses the 3 DFO pages; the safety check keeps the old rules")
    Container(fetchrep, "build/fetch_reports.py", "Python stdlib", "Test fisheries, feeds, and the manual CSV rows")
    Container(fetchhyd, "build/fetch_hydro.py", "Python stdlib", "ECCC water level, hourly, 14 days")
    Container(assemble, "build/assemble.py", "Python stdlib", "Puts the data into template.html")
  }

  Boundary(files, "Files in git") {
    ContainerDb(cat, "dfo/catalog.py", "Python", "Manual: names, translations")
    ContainerDb(rules, "rules.json, status.json", "JSON", "Auto: written by dfo/update.py")
    ContainerDb(csv, "build/manual/*.csv", "CSV", "Manual: Instagram, Facebook, TikTok rows")
    ContainerDb(rep, "reports.json", "JSON", "Auto: written by fetch_reports.py")
    ContainerDb(hyd, "hydro.json", "JSON", "Auto: written by fetch_hydro.py")
    ContainerDb(geo, "geo.json, species/*.webp", "JSON, WebP", "Manual run of the local scripts")
  }

  Boundary(people, "People") {
    Person(maint, "Maintainer", "Edits the manual files and commits them")
  }

  Rel(sources, update, "auto: DFO pages")
  Rel(sources, fetchrep, "auto: FOS, PSC, Atom, RSS")
  Rel(sources, fetchhyd, "auto: OGC API")
  Rel(assemble, pages, "auto: deploy index.html")

  Rel(maint, cat, "manual: edits")
  Rel(maint, csv, "manual: adds rows")
  Rel(maint, geo, "manual: runs scripts")

  Rel(cat, update, "reads")
  Rel(update, rules, "writes")
  Rel(csv, fetchrep, "reads")
  Rel(fetchrep, rep, "writes")
  Rel(fetchhyd, hyd, "writes")
  Rel(rules, assemble, "reads")
  Rel(rep, assemble, "reads")
  Rel(hyd, assemble, "reads")
  Rel(geo, assemble, "reads")

  UpdateElementStyle(cat, $bgColor="#BA7517", $borderColor="#854F0B")
  UpdateElementStyle(csv, $bgColor="#BA7517", $borderColor="#854F0B")
  UpdateElementStyle(geo, $bgColor="#BA7517", $borderColor="#854F0B")
  UpdateElementStyle(update, $bgColor="#0F6E56", $borderColor="#085041")
  UpdateElementStyle(fetchrep, $bgColor="#0F6E56", $borderColor="#085041")
  UpdateElementStyle(fetchhyd, $bgColor="#0F6E56", $borderColor="#085041")
  UpdateElementStyle(assemble, $bgColor="#0F6E56", $borderColor="#085041")
  UpdateElementStyle(rules, $bgColor="#0F6E56", $borderColor="#085041")
  UpdateElementStyle(rep, $bgColor="#0F6E56", $borderColor="#085041")
  UpdateElementStyle(hyd, $bgColor="#0F6E56", $borderColor="#085041")

  UpdateLayoutConfig($c4ShapeInRow="1", $c4BoundaryInRow="4")
```

Colours: green is automatic, amber is manual. The boundary names and the labels on the arrows say the same, so the diagrams also read without colour.

## Notes

- **Instagram, Facebook and TikTok** have no public search API for this use. A person adds each post as one row of `build/manual/reports.csv` (see "Add data by hand" in the [README](../README.md#add-data-by-hand)). If nobody adds rows, these reports leave the page after 21 days, and the page gives no warning.
- **Reddit** is automatic, but the filter keeps only posts that name a map water, salmon and a catch word, and are not questions. A person can add a post that the filter skips to `reports.csv`.
- **DFO** is automatic while the parser understands the pages. When the safety check blocks an update, the workflow opens an issue labelled `dfo-update`, and a person fixes `dfo/catalog.py`.
- **`build/manual/testfish.csv`** has only its header now.
- **Geometry and species images** come from scripts that a person runs locally (`python run_all.py`, `python fetch_species.py <pdf>`). The workflow does not run them; it uses the committed `geo.json` and `species/*.webp`.
- **Place search** sends a place name to [Nominatim](https://nominatim.org/) only when the viewer presses Enter. Coordinates, subarea codes and map waters are found in the page, with no network.
- **"My spots"** stay in the `localStorage` of the browser. The site does not receive them.
