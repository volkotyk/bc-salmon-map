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
| Base map | Real OpenStreetMap tiles when the host allows them; otherwise a built-in vector map (coastline, roads, streets within 700 m of fishing rivers, place names, parks, boat launches) | OpenStreetMap |

Features:

- Filter by species: Chinook, Coho, Chum, Pink, Sockeye (Ukrainian names always show the English DFO name).
- Pick a date: the map and list show the rules in force on that day, including ranges that cross New Year.
- Colours: Chinook + Coho, Chinook only, Coho only, release only, closed, closure.
- Click any water for the full rule table, notes, fishery-notice links, and the nearest road.
- Click anywhere on the map for the nearest road and a **Google Maps directions** / OpenStreetMap link.
- UA / EN switch (also `#uk` / `#en` in the URL; the choice is remembered). Light and dark themes.

## Repository layout

```
.github/workflows/pages.yml   builds index.html on every push to main and deploys it to GitHub Pages
build/
  template.html         page source: markup, CSS, JS, rules data, UA/EN texts
  leaflet.css           Leaflet 1.9.4 CSS (inlined at build time; Leaflet JS loads from cdnjs)
  geo.json              built map geometry: land, rivers, lakes, tidal subareas
  city.json             built city context: roads, streets, places, parks, boat launches
  sub.geojson           DFO PFMA subareas for Areas 28–29 (raw)
  *.py                  fetch + build scripts (see below)
  requirements.txt
```

The fishing rules live in `build/template.html` (`WATERS` array). Each rule has species, date range (MM-DD, may wrap past Dec 31), limit text and type (`retain`, `release`, `closed`, `gear`). English limit wording is in the `LIM_EN` table; other bilingual texts use `B('українською', 'English')`.

## Rebuild

Needs Python 3.10+.

```bash
pip install -r build/requirements.txt
cd build
python run_all.py            # download OSM + DFO data, rebuild everything (several minutes; Overpass can be slow)
python run_all.py --offline  # rebuild from raw files already downloaded
python run_all.py --page     # only re-assemble index.html after editing template.html
```

`index.html` (single file, ~2 MB, no backend) is a build output and is not committed. GitHub Actions runs `run_all.py --page` on every push to `main` and publishes the result.

Pipeline: `osm.py` (river/lake geometry) → `fetch_coast.py` (coastline) → `fetch_subareas.py` (DFO subareas) → `osm_city.py` (roads, places, POI) → `build_geo.py` → `build_tidal.py` → `osm_minor_bbox.py` (streets near rivers) → `build_city.py` → `assemble.py`.

### Update the rules

1. Open the DFO pages below and compare with `WATERS` in `build/template.html`.
2. Edit the rule rows (and `LIM_EN` if you add a new limit text).
3. Commit and push. The **Deploy to GitHub Pages** workflow rebuilds the page and publishes it in about a minute; check the result at the live URL.
4. Optional local preview: `python run_all.py --page`, then `python -m http.server` in the repo root and open `http://localhost:8000/`.

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
- OpenStreetMap contributors (ODbL 1.0), via the Overpass API: coastline, rivers, lakes, roads, places, boat launches
- Basemap tiles: © OpenStreetMap contributors, served by the OpenStreetMap Foundation

## Licence

Code: MIT, see [LICENSE](LICENSE). Map data in `build/geo.json` and `build/city.json` is derived from OpenStreetMap and is available under the [ODbL](https://opendatacommons.org/licenses/odbl/). Regulation summaries paraphrase DFO pages; the DFO pages are the authoritative source. Leaflet is BSD-2-Clause.
