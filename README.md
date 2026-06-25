# 15-Minute Shanghai - Track B Entertainment & Nightlife

This project implements the graduate brief in `shanghai_15min_brief.pdf` using the supplied 2023 Shanghai POI shapefiles. It chooses Track B, Entertainment & Nightlife, and produces three documented notebooks plus a public-ready static web map.

## Deliverables

- `notebooks/01_data_collection.ipynb` - data sourcing, cleaning, validation, and 894-word literature review.
- `notebooks/02_grid_isochrones.ipynb` - 500 m grid and four-mode 15-minute buffer scoring.
- `notebooks/03_scoring_h3.ipynb` - baseline + Track B scoring, H3 aggregation, GeoJSON export.
- `web/index.html` - interactive H3 map with mode toggle, baseline/nightlife toggle, hex detail panel, recommender sliders, and data transparency panel.
- `docs/trello_board_template.md` - ready-to-copy Trello board structure and sprint cards.

## Reproduce The Analysis

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe src\01_collect_pois.py
.\.venv\Scripts\python.exe src\02_grid_isochrones.py
.\.venv\Scripts\python.exe src\03_scoring_h3.py
.\.venv\Scripts\python.exe src\make_notebooks.py
```

The generated analysis files are in `data/processed/`. The web app reads `web/data/hexes.json` and `web/data/metadata.json`.

## Public Repository Notes

GitHub does not allow the raw Shanghai shapefile package and some intermediate CSV files to be stored directly in a normal class project repository because several files exceed the 100 MB per-file limit. For that reason:

- `2023_Shp/` is excluded from the public repo.
- large intermediate files such as `poi_catalog.csv` and `grid_scores.csv` are excluded.
- lightweight summaries, notebooks, scripts, and the compact web data remain in the repo.

The analysis pipeline still documents how to regenerate the outputs from the supplied local course dataset.

## Run The Web App Locally

```powershell
cd web
python -m http.server 8000
```

Open `http://localhost:8000`.

## Method Summary

The baseline score measures six universal needs: food, shopping, healthcare, education/culture, parks/public amenities, and transit. Track B measures restaurants, bars/nightlife, cultural venues, convenience stores, and a metro-late proxy.

Because the workspace does not include a routing API key, GTFS, or a routable street network, the four requested travel modes use transparent Euclidean proxies: walk 1.2 km, bike 3.5 km, transit 6 km, car 10 km. Car scores are exported for comparison but are not used in the main 15-minute-city score.

## Key Limitations

- Euclidean buffers approximate isochrones; replace them with Gaode/OpenRouteService/network analysis for a final production-grade submission.
- Late-night transit is proxied from metro/transit POIs; GTFS or official timetable data should replace it.
- Rent band is a district-level proxy for the detail panel field, not a listing-derived rent model.
- POI data may contain duplicates, closed venues, and inconsistent tags.

## Deployment

The `web/` folder is static. Deploy it to Vercel, Netlify, or GitHub Pages. Make sure `web/data/hexes.json` and `web/data/metadata.json` are included in the deployment.

This repository also includes a GitHub Actions workflow at `.github/workflows/deploy-pages.yml` that publishes the `web/` folder to GitHub Pages on every push to `main`.
