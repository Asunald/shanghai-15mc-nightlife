# Trello Board Template - 15MC Shanghai

Board name: `15MC Shanghai - [Your Name]`

Invite the instructor on Day 1. Use labels: Data (red), Analysis (yellow), App (green), Literature (blue), Review (purple).

## Lists

- Backlog
- Sprint 1 - Week 1
- Sprint 2 - Week 2
- Sprint 3 - Week 3
- Sprint 4 - Week 4
- Sprint 5 - Week 5
- Done
- Blocked

## Sprint 1 - Literature And Environment

### Read 15MC literature

Label: Literature

Due: Week 1 Friday

Acceptance criteria: At least four papers are summarized in the notebook 01 header; notes cover measurement methodology and equity critique.

Checklist:

- Read Moreno et al. 2021
- Read Weng et al. 2019
- Read Pozoukidou and Chatziyiannaki 2021
- Read Khavarian-Garmsir et al. 2023
- Draft 800-word literature review

### Create Python environment

Label: Data

Due: Week 1 Friday

Acceptance criteria: `requirements.txt` installs successfully and all scripts run from a fresh virtual environment.

Checklist:

- Create `.venv`
- Install packages
- Confirm shapefile, h3, pandas, scipy, matplotlib imports
- Document setup command in README

### Choose project track

Label: Review

Due: Week 1 Friday

Acceptance criteria: Track B question, indicators, and limitations are documented in notebook 01 and README.

Checklist:

- Compare Track A/B/C against available data
- Select Track B
- Define baseline indicators
- Define nightlife indicators

## Sprint 2 - Data Collection And Grid

### Convert POI shapefiles

Label: Data

Due: Week 2 Wednesday

Acceptance criteria: `data/processed/poi_catalog.csv` is generated with clean coordinates, district names, indicators, and source file names.

Checklist:

- Read all supplied WGS84 shapefiles
- Map POI categories to indicators
- Exclude address text from classification
- Export POI summary JSON

### Validate POI categories

Label: Analysis

Due: Week 2 Thursday

Acceptance criteria: Indicator counts and sample POIs are inspected; obvious misclassification rules are corrected.

Checklist:

- Inspect category counts
- Inspect top examples
- Fix broad keyword rules
- Re-run collection script

### Build 500 m grid

Label: Analysis

Due: Week 2 Friday

Acceptance criteria: `grid_cells.csv` covers the Shanghai POI extent and records grid centroids.

Checklist:

- Define bounding box
- Generate 500 m lon/lat grid
- Store stable grid IDs
- Document grid limitation

## Sprint 3 - Isochrones, Scoring, And Notebooks

### Compute four-mode access proxies

Label: Analysis

Due: Week 3 Tuesday

Acceptance criteria: Walk, bike, transit, and car count/score fields are generated for all baseline and Track B indicators.

Checklist:

- Build KDTree per indicator
- Query walk radius
- Query bike radius
- Query transit radius
- Query car radius

### Design scoring method

Label: Analysis

Due: Week 3 Wednesday

Acceptance criteria: Baseline, track, and composite weights are documented in notebook 03 and metadata.

Checklist:

- Define baseline equal weights
- Define Track B weights
- Keep car as comparison only
- Add limitations

### Aggregate to H3

Label: Analysis

Due: Week 3 Friday

Acceptance criteria: H3 resolution 8 CSV and GeoJSON are exported and can be loaded by the web app.

Checklist:

- Assign grid cells to H3
- Average mode scores
- Add detail-panel fields
- Export compact web GeoJSON

## Sprint 4 - Track Analysis And App Skeleton

### Build static map shell

Label: App

Due: Week 4 Tuesday

Acceptance criteria: `web/index.html` loads a Leaflet map and the H3 GeoJSON locally.

Checklist:

- Add Leaflet map
- Load compact GeoJSON
- Style hexes by score
- Fit map to Shanghai extent

### Implement required interactions

Label: App

Due: Week 4 Thursday

Acceptance criteria: Mode toggle, baseline/nightlife toggle, click detail panel, and recommender sliders are functional.

Checklist:

- Add mode buttons
- Add layer buttons
- Add selected hex panel
- Add priority sliders
- Highlight top 10 hexes

### Add data transparency panel

Label: App

Due: Week 4 Friday

Acceptance criteria: Web app displays sources, scoring method, collection date context, and limitations.

Checklist:

- Export metadata JSON
- Render source list
- Render limitations
- Mention proxy isochrones

## Sprint 5 - Completion And Demo

### Polish mobile experience

Label: App

Due: Week 5 Tuesday

Acceptance criteria: The app is usable on a phone-sized viewport with no overlapping text or controls.

Checklist:

- Test desktop viewport
- Test mobile viewport
- Adjust panel layout
- Confirm text fits buttons

### Final reproducibility check

Label: Review

Due: Week 5 Wednesday

Acceptance criteria: From raw shapefiles, all scripts regenerate notebooks, H3 outputs, and web data.

Checklist:

- Re-run data collection
- Re-run grid scoring
- Re-run H3 export
- Re-run notebook generation
- Record final file paths

### Deploy web app

Label: App

Due: Week 5 Thursday

Acceptance criteria: Public URL opens in under four seconds on a normal connection and shows the H3 map.

Checklist:

- Deploy `web/` folder
- Confirm data files included
- Test URL on desktop
- Test URL on mobile

### Prepare final demo

Label: Review

Due: Week 5 Friday

Acceptance criteria: Demo can explain the research question, method, results, and limitations in five minutes.

Checklist:

- Pick three high-scoring examples
- Pick one low-access contrast area
- Explain mode toggle
- Explain recommender sliders
- Explain limitations and next data improvements
