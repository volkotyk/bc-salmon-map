# Metro Vancouver Salmon Map · Лосось Metro Vancouver

An interactive map of where you can fish for Pacific salmon in the BC Lower Mainland, by species and date.
Інтерактивна карта: де і коли можна ловити тихоокеанського лосося в Lower Mainland (B.C.), за видом і датою.

**Live map:** https://volkotyk.github.io/bc-salmon-map/ · English: [`#en`](https://volkotyk.github.io/bc-salmon-map/#en) · Українська: [`#uk`](https://volkotyk.github.io/bc-salmon-map/#uk)

> **Not an official source.** Rules change through DFO fishery notices. Always check the
> [DFO pages](#data-sources) before you fish. River section boundaries on the map are approximate.

## What it shows

| Layer | Content | Source |
|---|---|---|
| Rivers and lakes (lines) | 23 waters of DFO **Region 2 – Lower Mainland** with salmon openings, limits, gear rules, sections | DFO freshwater salmon table |
| Tidal subareas (shaded) | All 31 subareas of DFO **Areas 28 and 29**: Howe Sound, Burrard Inlet, Strait of Georgia, tidal Fraser | DFO tidal pages + DFO PFMA subarea boundaries |
| Seasonal closure | Mouth of the Fraser River salmon closure (Aug 1 – Sep 30), drawn from the DFO coordinates | DFO Area 29 page |
| Running now (panel) | Daily catch of the Fraser test fisheries: Albion for Chinook, Chum and Coho, Whonnock and Qualark for Sockeye (and Pink in pink years). Each row: last sample, 7-day total, trend, 28-day bar strip. The newest tackle shop reports with the species and map waters they name; a water button flies the map to that water | [DFO Albion test fishery](https://www.pac.dfo-mpo.gc.ca/fm-gp/fraser/albion-eng.html), [PSC test fishing results](https://www.psc.org/publications/fraser-panel-in-season-information/test-fishing-results/) (PDF tables), [Pacific Angler Friday Fishing Report](https://www.pacificangler.ca/blogs/learn) |
| Base map | Real OpenStreetMap tiles when the host allows them; otherwise a built-in outline map (coastline, lakes, rivers) | OpenStreetMap |

Features:

- Filter by species: Chinook, Coho, Chum, Pink, Sockeye (Ukrainian names always show the English DFO name).
- Species identification card: pick a species to see drawings of the sea phase and the spawning phase, plus the key marks (gums, tail spots, colours).
- Pick a date: the map and list show the rules in force on that day, including ranges that cross New Year.
- Licence switch: *Both*, *Freshwater* (BC Freshwater Fishing Licence) or *Tidal* (BC Tidal Waters Sport Fishing Licence). With one licence, the list and the summary show only the waters it covers; the other waters stay on the map as faint outlines, and their popup names the licence they need. The choice is remembered.
- Colours: Chinook + Coho, Chinook only, Coho only, release only, closed, closure.
- Click any water for the full rule table, notes and fishery-notice links.
- Click anywhere on the map for its coordinates and a **Google Maps directions** / OpenStreetMap link.
- **Updates itself:** every day GitHub Actions reads the three DFO pages and republishes the map with the new rules. The page shows when DFO was last checked and when the rules last changed.
- "Running now" panel, rebuilt every day: which salmon the DFO and PSC test nets on the Fraser catch, and links to recent tackle shop reports. The page keeps only titles, dates, links and species tags, not the report text. A species named in a report does not mean it is open. Social networks are not a source: Instagram, Facebook and TikTok have no public search API for this use, and Reddit gives new API access only after manual approval.
- UA / EN switch (also `#uk` / `#en` in the URL; the choice is remembered). Light and dark themes.
- Mobile first: on a phone the map fills the screen and the panel is a bottom sheet. Drag the sheet or tap its handle: the short position shows the species and the date, the middle position adds the list, the tall position shows everything. From 768 px wide the panel is a sidebar.

## Repository layout

```
.github/workflows/pages.yml   daily + on push: update rules from DFO, commit changes, fetch the running-now data, build index.html, deploy to Pages
dfo/
  update.py             reads the DFO pages, parses the tables, validates, writes build/rules.json + build/status.json
  catalog.py            hand-kept knowledge: DFO names -> map lines, group names, Ukrainian wording
  htmltable.py          small HTML table reader (rowspan/colspan)
  snapshots/            plain text of the salmon part of each DFO page (git history shows what DFO changed)
build/
  template.html         page source: markup, CSS, JS, UA/EN interface texts
  rules.json            fishing rules parsed from DFO (generated; readable diffs in git)
  status.json           last rules change, and "pending" when an update was blocked
  leaflet.css           Leaflet 1.9.4 CSS (inlined at build time; Leaflet JS loads from cdnjs)
  geo.json              map geometry: land, rivers, lakes, tidal subareas
  sub.geojson           DFO PFMA subareas for Areas 28–29 (raw)
  species/*.webp        species illustrations (public domain), inlined into the page; fetch_species.py downloads them
  fetch_reports.py      DFO/PSC test fisheries + shop report feeds -> reports.json (not committed; a failed source is skipped)
  *.py                  geometry fetch + build scripts, assemble.py
```

Python standard library only for everything that runs in GitHub Actions; `build/requirements.txt` is only for rebuilding the geometry.

## Automatic DFO updates

Every day at 15:23 UTC (08:23 Pacific daylight time), on every push, and on demand from the Actions tab,
`dfo/update.py`:

1. downloads the Region 2, Area 28 and Area 29 pages;
2. reads the tables: freshwater waters, sections, species, dates, limits, fishery notices; tidal species limits by subarea, gear restrictions, the Fraser mouth closure, and every other restriction as a popup note;
3. validates everything against `dfo/catalog.py`;
4. writes `build/rules.json`; the workflow commits it and republishes the map.

**Safety check.** If DFO shows something the updater does not understand — a water that has no line on the map,
an unreadable date, a new limit wording, a changed table layout, a changed Fraser-mouth boundary — the map keeps the
previous rules, shows a red *"DFO: changes pending"* warning, and the workflow opens an issue labelled `dfo-update`
with the reasons and the text diff. Fix `dfo/catalog.py` (for example add the new water and its Ukrainian name), push,
and the next run publishes the new rules and clears the warning. A limit wording without a Ukrainian translation does
not block: it is shown in English.

To test the parser without the network: `python dfo/update.py --cache` (reuses `dfo/cache/`, saved by the last online run).

The bot commits to `main`, so run `git pull` before your next push. GitHub pauses scheduled workflows after 60 days
without repository activity; re-enable the workflow from the Actions tab if that happens.

## Rebuild

Needs Python 3.10+.

```bash
pip install -r build/requirements.txt
cd build
python run_all.py            # download OSM + DFO data, rebuild everything (several minutes; Overpass can be slow)
python run_all.py --offline  # rebuild from raw files already downloaded
python run_all.py --page     # only re-assemble index.html after editing template.html
```

`index.html` (single file, ~0.9 MB with the inlined species drawings, no backend) is a build output and is not committed. GitHub Actions assembles and publishes it.

Pipeline: `osm.py` (river/lake geometry) → `fetch_coast.py` (coastline) → `fetch_subareas.py` (DFO subareas) → `fetch_reports.py` (running-now panel) → `build_geo.py` → `build_tidal.py` → `assemble.py`. `fetch_species.py` runs only when a species drawing changes; its output `species/*.webp` is committed.

### Local preview

`python dfo/update.py` (or `--cache`), then `cd build && python run_all.py --page`, then `python -m http.server` in the repo root and open `http://localhost:8000/`.

## Hosting

`index.html` is a static file. It works on GitHub Pages or any static host (free plan, public repo; limits: 1 GB site, ~100 GB/month soft bandwidth).

- **Normal web host:** the page loads [OpenStreetMap standard tiles](https://operations.osmfoundation.org/policies/tiles/) (no key; attribution shown; the browser sends the required Referer) and hides its own vector base. The dark theme inverts the tiles with a CSS filter.
- **Where external images are blocked** (for example the claude.ai artifact viewer): tiles fail, and the page keeps its built-in vector map.
- **Opened from disk (`file://`):** OSM may refuse tiles without a Referer; the page then keeps the vector map. Serve it locally instead: `python -m http.server` and open `http://localhost:8000/`.
- Directions use a plain link to Google Maps, so no Google API key is needed.

Other basemap options (checked September 2026):

| Option | Key | Free use | Notes |
|---|---|---|---|
| OpenStreetMap standard tiles (current) | none | light use, no SLA | may block abusive clients without notice |
| CARTO basemaps | required since 2026 (free, no account) | 5M tile requests/month non-commercial | without a key the tiles show an "API KEY REQUIRED" watermark |
| MapTiler / Stadia Maps / Thunderforest | required, restrict by domain | 100k–200k requests/month | good upgrade path if OSM blocks traffic |
| Google Maps (Map Tiles API or JS API + GoogleMutant) | required, billing account with a card | 10k map loads / 100k tiles per month | adds billing risk for no benefit here |

Free static hosts that work the same way: GitHub Pages, Cloudflare Pages, Netlify, Vercel (Hobby, non-commercial).

## Data sources

- DFO, Region 2 – Lower Mainland freshwater salmon: https://www.pac.dfo-mpo.gc.ca/fm-gp/rec/fresh-douce/region2-eng.html (as of 2026-09-16)
- DFO, Area 28 tidal: https://www.pac.dfo-mpo.gc.ca/fm-gp/rec/tidal-maree/a-s28-eng.html (as of 2026-09-01)
- DFO, Area 29 tidal: https://www.pac.dfo-mpo.gc.ca/fm-gp/rec/tidal-maree/a-s29-eng.html (as of 2026-09-05)
- DFO Pacific Fishery Management Subareas 1:50K: https://egisp.dfo-mpo.gc.ca/arcgis/rest/services/Pacific/DFO_BC_PFMA_SUBAREAS_50K_V3_1/MapServer
- OpenStreetMap contributors (ODbL 1.0), via the Overpass API: coastline, rivers, lakes
- Basemap tiles: © OpenStreetMap contributors, served by the OpenStreetMap Foundation
- Species illustrations (public domain, via Wikimedia Commons): U.S. Government Printing Office pamphlet *Lake Washington Ship Canal Fish Ladder* (1996) for Chinook, Coho and Sockeye; Timothy Knepp, U.S. Fish and Wildlife Service, for spawning Pink and Chum; A. Hoen & Co. plate in Evermann & Goldsborough, *The Fishes of Alaska* (1907), for sea-phase Pink. There is no public-domain sea-phase Chum drawing, so the card describes it in text.

## Licence

Code: MIT, see [LICENSE](LICENSE). Map data in `build/geo.json` is derived from OpenStreetMap and is available under the [ODbL](https://opendatacommons.org/licenses/odbl/). Regulation summaries paraphrase DFO pages; the DFO pages are the authoritative source. Leaflet is BSD-2-Clause.
