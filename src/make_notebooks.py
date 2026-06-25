from __future__ import annotations

from pathlib import Path

import nbformat as nbf


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = ROOT / "notebooks"


LIT_REVIEW = """# Literature Review: Measuring the 15-Minute City in Shanghai

The 15-minute city (15MC) reframes urban quality as a question of everyday proximity: residents should be able to reach core needs such as food, health care, education, public space, and social life within a short walk or cycle trip. Moreno et al. (2021) connect the idea to chrono-urbanism, a planning argument that cities should reduce the amount of time residents must spend moving between separated functions. The concept is not only about transport efficiency. It is also about place identity, local services, social resilience, and the everyday dignity of having useful destinations close to home. For this project, that idea is operationalised through a 500 m grid, mode-specific 15-minute access proxies, and an H3 aggregation layer that can be inspected in an interactive map.

Measurement is the main methodological challenge. A strict 15MC study would use network travel times, sidewalk quality, intersection delay, service capacity, opening hours, and local demand. Many public dashboards simplify the idea into distance to amenities, which is understandable but risky: straight-line access can exaggerate true walkability, while POI counts can reward quantity even when services are small, closed, unaffordable, or difficult to reach. Weng et al. (2019) are especially relevant for this Shanghai project because they measured 15-minute walkable neighbourhoods in urban China and argued that amenity access should be sensitive to population groups, real traffic conditions, amenity scale, and social inequality. Their approach shows that the 15MC can be measured empirically, but also that the result depends heavily on assumptions about what counts as access.

The supplied project data contains 2023 Shanghai point-of-interest shapefiles rather than routable street geometry, GTFS timetables, current opening hours, rental listings, or API credentials. This notebook therefore uses Euclidean mode buffers as a transparent proxy: 1.2 km walking, 3.5 km cycling, 6 km transit, and 10 km car. The method is weaker than a real network isochrone produced by Gaode, OpenRouteService, or a local street graph, but it is reproducible, fast enough for the class project, and explicit about its assumptions. The web application labels car access as comparison only, because the 15MC baseline in the brief is explicitly about walking and cycling rather than automobile reach.

The baseline indicators follow the brief's universal-needs logic: food, shopping, health care, education/culture, parks/public amenities, and transit access. Track B adds restaurants, bars/nightlife, cultural venues, convenience stores, and a metro-late proxy. Counts are transformed using a mixed adequacy and richness score. A single nearby venue gives basic credit because the resident can reach the service, while denser districts receive additional credit for choice and variety. This avoids treating one shop the same as a large commercial street, while also avoiding a map where central Shanghai becomes a flat surface of maximum scores. H3 resolution 8 is used because it creates legible neighbourhood-scale hexagons while keeping the web payload manageable.

Equity critiques are central to the 15MC debate. Pozoukidou and Chatziyiannaki (2021) argue that the 15MC should be decomposed into measurable dimensions rather than treated as a universal slogan. Their framing matters because a polished map of access can hide whether services are inclusive, affordable, and socially useful. Khavarian-Garmsir et al. (2023) similarly review the concept's planning principles and implementation challenges, warning that 15MC policy can become a branding exercise if it does not confront housing affordability, governance capacity, service quality, and displacement. In high-demand cities, walkable amenity-rich districts can become expensive districts. A neighbourhood may therefore score well on proximity while excluding the residents who would most benefit from reduced travel burden.

For Shanghai nightlife, the key question is whether cultural and entertainment clusters are genuinely accessible to residents without relying on destination travel. Track B is a useful stress test because nightlife is not the same as daily-service access. A place can have schools, clinics, shops, and parks while still lacking evening social infrastructure. Conversely, a nightlife cluster can be attractive to visitors while offering weak everyday livability or high housing costs. The analysis expects high scores in dense central districts such as Huangpu, Jing'an, and Xuhui, with weaker coverage in peripheral areas. The important interpretation is not just where scores are high, but where baseline access and nightlife access diverge.

This version should be read as a reproducible analytical prototype rather than a definitive policy model. Real opening hours, Dianping ratings, review counts, late-night metro timetables, pedestrian network distances, bike-lane coverage, and rent data would all improve the analysis. The project still contributes a useful first pass: it documents the data provenance, translates the brief into a measurable scoring system, exposes limitations to users, and provides an interactive H3 map for exploring the geography of Shanghai's 15-minute nightlife access.

References:

- Moreno, C., Allam, Z., Chabaud, D., Gall, C., & Pratlong, F. (2021). Introducing the "15-Minute City": Sustainability, Resilience and Place Identity in Future Post-Pandemic Cities. Smart Cities, 4(1), 93-111. https://doi.org/10.3390/smartcities4010006
- Weng, M., Ding, N., Li, J., Jin, X., Xiao, H., He, Z., & Su, S. (2019). The 15-minute walkable neighborhoods: Measurement, social inequalities and implications for building healthy communities in urban China. Journal of Transport & Health, 13, 259-273.
- Pozoukidou, G., & Chatziyiannaki, Z. (2021). 15-Minute City: Decomposing the New Urban Planning Eutopia. Sustainability, 13(2), 928. https://doi.org/10.3390/su13020928
- Khavarian-Garmsir, A. R., Sharifi, A., & Sadeghi, A. (2023). The 15-minute city: Urban planning and design efforts toward creating sustainable neighborhoods. Cities, 132, 104101."""


def md(text: str):
    return nbf.v4.new_markdown_cell(text)


def code(text: str):
    return nbf.v4.new_code_cell(text)


def write_notebook(path: Path, cells: list) -> None:
    nb = nbf.v4.new_notebook()
    nb["cells"] = cells
    nb["metadata"] = {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {"name": "python", "pygments_lexer": "ipython3"},
    }
    path.write_text(nbf.writes(nb), encoding="utf-8")


def notebook_01() -> None:
    cells = [
        md(LIT_REVIEW),
        md(
            """## Notebook Purpose

This notebook documents data sourcing, POI cleaning, category mapping, validation, and provenance. It runs the project script `src/01_collect_pois.py`, which converts the supplied 2023 Shanghai POI shapefiles into a clean CSV used by the later notebooks."""
        ),
        code(
            """from pathlib import Path
import json
import pandas as pd

ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
RAW_DIR = ROOT / "2023_Shp" / "Shp"
PROCESSED = ROOT / "data" / "processed"
print(ROOT)
print(len(list(RAW_DIR.glob("*.shp"))), "raw shapefiles")"""
        ),
        md("## Run Data Collection"),
        code(
            """import subprocess, sys

subprocess.run([sys.executable, str(ROOT / "src" / "01_collect_pois.py")], check=True)"""
        ),
        md("## Validate Classified POIs"),
        code(
            """poi_path = PROCESSED / "poi_catalog.csv"
summary_path = PROCESSED / "poi_summary.json"
pois = pd.read_csv(poi_path)
summary = json.loads(summary_path.read_text(encoding="utf-8"))

print(f"Classified POIs: {len(pois):,}")
display(pois.head())
summary["by_indicator"]"""
        ),
        code(
            """district_counts = pois["district"].value_counts().head(16)
district_counts"""
        ),
        md(
            """## Data Provenance and Limitations

- Source: supplied `2023_Shp/Shp/*.shp` point shapefiles, WGS84 coordinates.
- Key fields used: `name`, `type`, `adname`, `经度`, `纬度`, `timestamp`.
- Category mapping: deterministic keyword rules in `src/config.py`.
- Address text is not used for category matching, because it can contain phrases such as "near metro station" that misclassify unrelated POIs.
- Known limitations: duplicated POIs, possible closed venues, no opening hours, no ratings, and no platform terms beyond the local supplied files."""
        ),
    ]
    write_notebook(NOTEBOOK_DIR / "01_data_collection.ipynb", cells)


def notebook_02() -> None:
    cells = [
        md(
            """# 02 - Grid, Isochrone Proxies, and Spatial Joins

This notebook builds a 500 m grid over the supplied Shanghai POI extent, computes mode-specific 15-minute proximity counts, and caches the grid-level scores. The assignment asks for four modes: walk, bike, transit, and car. Because no routing API key or routable network is included, the implementation uses transparent Euclidean buffers as a reproducible isochrone proxy."""
        ),
        code(
            """from pathlib import Path
import json
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
PROCESSED = ROOT / "data" / "processed"
print(ROOT)"""
        ),
        md("## Run Grid and Mode-Buffer Scoring"),
        code(
            """import subprocess, sys

subprocess.run([sys.executable, str(ROOT / "src" / "02_grid_isochrones.py")], check=True)"""
        ),
        md("## Inspect Grid Coverage"),
        code(
            """grid = pd.read_csv(PROCESSED / "grid_cells.csv")
scores = pd.read_csv(PROCESSED / "grid_scores.csv")
summary = json.loads((PROCESSED / "grid_summary.json").read_text(encoding="utf-8"))
print(summary)
display(grid.head())
display(scores.head())"""
        ),
        code(
            """fig, ax = plt.subplots(figsize=(7, 7))
sample = scores.sample(min(12000, len(scores)), random_state=42)
ax.scatter(sample["lon"], sample["lat"], s=1, alpha=0.25)
ax.set_title("500 m Grid Sample over Shanghai POI Extent")
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
ax.set_aspect("equal", adjustable="box")
plt.show()"""
        ),
        md(
            """## Spatial Method

For each grid centroid and each mode radius, the script uses `scipy.spatial.cKDTree` to count POIs in every baseline and Track B category. Counts are converted into scores from 0 to 1 with an adequacy plus richness transform. This keeps the first nearby amenity meaningful while preserving differences between sparse and dense nightlife areas."""
        ),
    ]
    write_notebook(NOTEBOOK_DIR / "02_grid_isochrones.ipynb", cells)


def notebook_03() -> None:
    cells = [
        md(
            """# 03 - Baseline, Track B Scoring, and H3 Export

This notebook combines the baseline layer and Track B nightlife layer, aggregates grid scores to Uber H3 resolution 8, and exports the final GeoJSON used by the web application."""
        ),
        code(
            """from pathlib import Path
import json
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
PROCESSED = ROOT / "data" / "processed"
WEB_DATA = ROOT / "web" / "data"
print(ROOT)"""
        ),
        md("## Run H3 Scoring"),
        code(
            """import subprocess, sys

subprocess.run([sys.executable, str(ROOT / "src" / "03_scoring_h3.py")], check=True)"""
        ),
        md("## Inspect Scores"),
        code(
            """h3_scores = pd.read_csv(PROCESSED / "h3_scores_track_b.csv")
metadata = json.loads((WEB_DATA / "metadata.json").read_text(encoding="utf-8"))
print(metadata["score_summary"])
display(h3_scores.head(10))
h3_scores[["baseline_score", "track_score", "composite_score"]].describe()"""
        ),
        code(
            """fig, ax = plt.subplots(figsize=(8, 4))
h3_scores["composite_score"].hist(bins=40, ax=ax)
ax.set_title("Composite H3 Score Distribution")
ax.set_xlabel("Score")
ax.set_ylabel("H3 cells")
plt.show()"""
        ),
        code(
            """fig, ax = plt.subplots(figsize=(8, 7))
plot_data = h3_scores.sample(min(15000, len(h3_scores)), random_state=1)
sc = ax.scatter(plot_data["lon"], plot_data["lat"], c=plot_data["composite_score"], s=3, cmap="viridis", alpha=0.75)
fig.colorbar(sc, ax=ax, label="Composite score")
ax.set_title("Track B H3 Scores - Shanghai")
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
ax.set_aspect("equal", adjustable="box")
plt.show()"""
        ),
        md(
            """## Weighting Rationale

Baseline score is the average of six universal needs using walk and bike scores only. Track B is a weighted nightlife layer: restaurants 30%, bars/nightlife 25%, cultural venues 20%, convenience stores 15%, and metro late proxy 10%. The final composite is 60% baseline and 40% track layer. Car mode scores are exported for comparison in the application but are not used in the main 15-minute-city score."""
        ),
        md(
            """## Exported Files

- `data/processed/h3_scores_track_b.csv`: full tabular H3 scores.
- `data/processed/shanghai_15mc_h3_track_b.geojson`: complete H3 GeoJSON.
- `web/data/hexes.json`: compact front-end payload.
- `web/data/metadata.json`: source, scoring, and limitation metadata for the transparency panel."""
        ),
    ]
    write_notebook(NOTEBOOK_DIR / "03_scoring_h3.ipynb", cells)


def main() -> None:
    NOTEBOOK_DIR.mkdir(parents=True, exist_ok=True)
    notebook_01()
    notebook_02()
    notebook_03()
    print(f"Wrote notebooks to {NOTEBOOK_DIR}")


if __name__ == "__main__":
    main()
