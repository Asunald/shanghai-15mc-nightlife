from __future__ import annotations

import csv
import json
import math
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

from config import (
    BASELINE_INDICATORS,
    GRID_STEP_M,
    MODE_RADII_M,
    PROCESSED_DIR,
    SHANGHAI_BOUNDS,
    TRACK_INDICATORS,
)


POI_INPUT = PROCESSED_DIR / "poi_catalog.csv"
GRID_OUTPUT = PROCESSED_DIR / "grid_cells.csv"
SCORES_OUTPUT = PROCESSED_DIR / "grid_scores.csv"
SUMMARY_OUTPUT = PROCESSED_DIR / "grid_summary.json"


METERS_PER_DEG_LAT = 111_320


def lon_step_meters(lat: float) -> float:
    return METERS_PER_DEG_LAT * math.cos(math.radians(lat))


def lonlat_to_xy(lon: np.ndarray, lat: np.ndarray, ref_lat: float) -> tuple[np.ndarray, np.ndarray]:
    x = (lon - SHANGHAI_BOUNDS["min_lon"]) * lon_step_meters(ref_lat)
    y = (lat - SHANGHAI_BOUNDS["min_lat"]) * METERS_PER_DEG_LAT
    return x, y


def generate_grid() -> list[dict[str, float | str]]:
    bounds = SHANGHAI_BOUNDS
    ref_lat = (bounds["min_lat"] + bounds["max_lat"]) / 2
    d_lat = GRID_STEP_M / METERS_PER_DEG_LAT
    d_lon = GRID_STEP_M / lon_step_meters(ref_lat)

    rows: list[dict[str, float | str]] = []
    lat = bounds["min_lat"] + d_lat / 2
    i = 0
    while lat <= bounds["max_lat"]:
        lon = bounds["min_lon"] + d_lon / 2
        j = 0
        while lon <= bounds["max_lon"]:
            rows.append(
                {
                    "grid_id": f"g{i:03d}_{j:03d}",
                    "lon": round(lon, 8),
                    "lat": round(lat, 8),
                }
            )
            lon += d_lon
            j += 1
        lat += d_lat
        i += 1
    return rows


def load_pois() -> tuple[list[dict[str, str]], dict[str, np.ndarray]]:
    pois: list[dict[str, str]] = []
    indicator_points: dict[str, list[tuple[float, float]]] = {
        indicator: [] for indicator in set(BASELINE_INDICATORS + TRACK_INDICATORS)
    }
    with POI_INPUT.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            lon = float(row["lon"])
            lat = float(row["lat"])
            pois.append(row)
            for indicator in row["indicators"].split("|"):
                if indicator in indicator_points:
                    indicator_points[indicator].append((lon, lat))

    ref_lat = (SHANGHAI_BOUNDS["min_lat"] + SHANGHAI_BOUNDS["max_lat"]) / 2
    arrays: dict[str, np.ndarray] = {}
    for indicator, points in indicator_points.items():
        if not points:
            arrays[indicator] = np.empty((0, 2))
            continue
        arr = np.array(points, dtype=float)
        x, y = lonlat_to_xy(arr[:, 0], arr[:, 1], ref_lat)
        arrays[indicator] = np.column_stack((x, y))
    return pois, arrays


def score_count(count: int, radius_m: int) -> float:
    # The first nearby POI matters for 15MC adequacy, while dense places receive
    # extra credit for choice. A high target keeps central Shanghai from becoming
    # a flat wall of 100s.
    if count <= 0:
        return 0.0
    area_scale = (radius_m / 1200) ** 2
    density_target = max(10.0, 100.0 * area_scale)
    adequacy = 0.35
    richness = 0.65 * min(1.0, math.log1p(count) / math.log1p(density_target))
    return round(adequacy + richness, 4)


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    grid = generate_grid()
    pois, indicator_points = load_pois()

    ref_lat = (SHANGHAI_BOUNDS["min_lat"] + SHANGHAI_BOUNDS["max_lat"]) / 2
    grid_lon = np.array([row["lon"] for row in grid], dtype=float)
    grid_lat = np.array([row["lat"] for row in grid], dtype=float)
    grid_x, grid_y = lonlat_to_xy(grid_lon, grid_lat, ref_lat)
    grid_xy = np.column_stack((grid_x, grid_y))

    trees = {
        indicator: cKDTree(points) if len(points) else None
        for indicator, points in indicator_points.items()
    }

    fieldnames = ["grid_id", "lon", "lat"]
    for mode in MODE_RADII_M:
        for indicator in BASELINE_INDICATORS + TRACK_INDICATORS:
            fieldnames.append(f"{mode}_{indicator}_count")
            fieldnames.append(f"{mode}_{indicator}_score")

    with GRID_OUTPUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["grid_id", "lon", "lat"])
        writer.writeheader()
        writer.writerows(grid)

    indicator_totals = Counter()
    with SCORES_OUTPUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for idx, row in enumerate(grid):
            scored = dict(row)
            point = grid_xy[idx]
            for mode, radius in MODE_RADII_M.items():
                for indicator in BASELINE_INDICATORS + TRACK_INDICATORS:
                    tree = trees[indicator]
                    count = 0 if tree is None else len(tree.query_ball_point(point, radius))
                    scored[f"{mode}_{indicator}_count"] = count
                    scored[f"{mode}_{indicator}_score"] = score_count(count, radius)
                    if count:
                        indicator_totals[(mode, indicator)] += 1
            writer.writerow(scored)

    summary = {
        "grid_step_m": GRID_STEP_M,
        "grid_cells": len(grid),
        "classified_pois": len(pois),
        "mode_radii_m": MODE_RADII_M,
        "nonzero_grid_counts": {f"{k[0]}_{k[1]}": v for k, v in indicator_totals.items()},
        "bounds": SHANGHAI_BOUNDS,
        "method": "Euclidean mode buffers around 500 m grid centroids, queried with scipy cKDTree.",
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {GRID_OUTPUT} with {len(grid):,} cells")
    print(f"Wrote {SCORES_OUTPUT}")
    print(f"Wrote {SUMMARY_OUTPUT}")


if __name__ == "__main__":
    main()
