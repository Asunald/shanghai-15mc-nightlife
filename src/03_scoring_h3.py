from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import h3
import numpy as np
from scipy.spatial import cKDTree

from config import (
    BASELINE_INDICATORS,
    BASELINE_WEIGHTS,
    DATA_SOURCES,
    H3_RESOLUTION,
    MODE_RADII_M,
    MODE_WEIGHTING,
    PROCESSED_DIR,
    TRACK,
    TRACK_INDICATORS,
    TRACK_WEIGHTS,
    WEB_DATA_DIR,
)


GRID_SCORES_INPUT = PROCESSED_DIR / "grid_scores.csv"
POI_INPUT = PROCESSED_DIR / "poi_catalog.csv"
H3_CSV_OUTPUT = PROCESSED_DIR / "h3_scores_track_b.csv"
GEOJSON_OUTPUT = PROCESSED_DIR / "shanghai_15mc_h3_track_b.geojson"
WEB_COMPACT_JSON_OUTPUT = WEB_DATA_DIR / "hexes.json"
WEB_METADATA_OUTPUT = WEB_DATA_DIR / "metadata.json"

METERS_PER_DEG_LAT = 111_320
REF_LAT = 31.25


def weighted_mean(row: dict[str, str], mode: str, indicators: list[str], weights: dict[str, float]) -> float:
    return sum(float(row[f"{mode}_{indicator}_score"]) * weights[indicator] for indicator in indicators)


def composite_for_mode(row: dict[str, str], mode: str) -> dict[str, float]:
    baseline = weighted_mean(row, mode, BASELINE_INDICATORS, BASELINE_WEIGHTS)
    track = weighted_mean(row, mode, TRACK_INDICATORS, TRACK_WEIGHTS)
    # For car we expose a comparison view but keep the 15MC interpretation rooted
    # in walk/bike/transit. The field is useful for the mode toggle in the app.
    composite = 0.6 * baseline + 0.4 * track
    return {
        f"{mode}_baseline_score": round(baseline * 100, 2),
        f"{mode}_track_score": round(track * 100, 2),
        f"{mode}_composite_score": round(composite * 100, 2),
    }


def h3_boundary_geojson(cell: str) -> list[list[float]]:
    boundary = h3.cell_to_boundary(cell)
    coords = [[round(lon, 6), round(lat, 6)] for lat, lon in boundary]
    coords.append(coords[0])
    return coords


def lonlat_to_xy(lon: float, lat: float) -> tuple[float, float]:
    x = lon * METERS_PER_DEG_LAT * math.cos(math.radians(REF_LAT))
    y = lat * METERS_PER_DEG_LAT
    return x, y


def build_tree(points: list[tuple[float, float]]) -> cKDTree | None:
    if not points:
        return None
    xy = np.array([lonlat_to_xy(lon, lat) for lon, lat in points], dtype=float)
    return cKDTree(xy)


def bucket(score: float) -> str:
    if score >= 75:
        return "excellent"
    if score >= 55:
        return "strong"
    if score >= 35:
        return "emerging"
    return "low-access"


def district_rent_proxy(district: str) -> str:
    premium = {"黄浦区", "静安区", "徐汇区", "长宁区", "虹口区", "杨浦区", "浦东新区"}
    middle = {"普陀区", "闵行区", "宝山区", "嘉定区", "松江区", "青浦区"}
    if district in premium:
        return "high"
    if district in middle:
        return "medium"
    return "lower"


def load_poi_context() -> tuple[dict[str, Counter], dict[str, Counter], dict[str, Counter], cKDTree | None]:
    by_h3_indicator: dict[str, Counter] = defaultdict(Counter)
    by_h3_names: dict[str, Counter] = defaultdict(Counter)
    by_h3_district: dict[str, Counter] = defaultdict(Counter)
    metro_points: list[tuple[float, float]] = []
    display_block_terms = (
        "停车",
        "充电",
        "汽车",
        "汽修",
        "加油",
        "车行",
        "出入口",
        "入口",
        "出口",
        "地下车库",
    )
    with POI_INPUT.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cell = h3.latlng_to_cell(float(row["lat"]), float(row["lon"]), H3_RESOLUTION)
            indicators = row["indicators"].split("|")
            for indicator in indicators:
                by_h3_indicator[cell][indicator] += 1
            if "metro_late_proxy" in indicators:
                metro_points.append((float(row["lon"]), float(row["lat"])))
            name = row["name"]
            if (
                name
                and not any(term in name for term in display_block_terms)
                and any(
                indicator in indicators
                for indicator in TRACK_INDICATORS + ["food", "shopping", "transit"]
                )
            ):
                by_h3_names[cell][name] += 1
            if row["district"]:
                by_h3_district[cell][row["district"]] += 1
    return by_h3_indicator, by_h3_names, by_h3_district, build_tree(metro_points)


def aggregate_rows() -> list[dict[str, object]]:
    poi_counts, poi_names, poi_districts, metro_tree = load_poi_context()
    aggregates: dict[str, dict[str, object]] = {}
    numeric_fields: list[str] = []

    with GRID_SCORES_INPUT.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            lat = float(row["lat"])
            lon = float(row["lon"])
            cell = h3.latlng_to_cell(lat, lon, H3_RESOLUTION)

            mode_scores: dict[str, float] = {}
            for mode in MODE_RADII_M:
                mode_scores.update(composite_for_mode(row, mode))

            if not numeric_fields:
                numeric_fields = sorted(mode_scores)

            agg = aggregates.setdefault(
                cell,
                {
                    "h3": cell,
                    "grid_count": 0,
                    "center_lon_sum": 0.0,
                    "center_lat_sum": 0.0,
                    "values": defaultdict(float),
                },
            )
            agg["grid_count"] = int(agg["grid_count"]) + 1
            agg["center_lon_sum"] = float(agg["center_lon_sum"]) + lon
            agg["center_lat_sum"] = float(agg["center_lat_sum"]) + lat
            values = agg["values"]
            for key, value in mode_scores.items():
                values[key] += value

    rows: list[dict[str, object]] = []
    for cell, agg in aggregates.items():
        grid_count = int(agg["grid_count"])
        values = agg["values"]
        row: dict[str, object] = {
            "h3": cell,
            "grid_count": grid_count,
            "lon": round(float(agg["center_lon_sum"]) / grid_count, 6),
            "lat": round(float(agg["center_lat_sum"]) / grid_count, 6),
        }
        for key in numeric_fields:
            row[key] = round(values[key] / grid_count, 2)

        walk_bike_baseline = sum(row[f"{mode}_baseline_score"] for mode in MODE_WEIGHTING["baseline_modes"])
        row["baseline_score"] = round(walk_bike_baseline / len(MODE_WEIGHTING["baseline_modes"]), 2)

        track_modes = MODE_WEIGHTING["track_modes"]
        track_score = sum(row[f"{mode}_track_score"] for mode in track_modes) / len(track_modes)
        row["track_score"] = round(track_score, 2)
        row["composite_score"] = round(0.6 * row["baseline_score"] + 0.4 * row["track_score"], 2)
        row["access_band"] = bucket(float(row["composite_score"]))

        district = poi_districts[cell].most_common(1)[0][0] if poi_districts[cell] else ""
        row["district"] = district
        row["rent_band_proxy"] = district_rent_proxy(district)
        if metro_tree is not None:
            dist, _ = metro_tree.query(lonlat_to_xy(float(row["lon"]), float(row["lat"])))
            row["metro_distance_m"] = int(round(float(dist)))
        else:
            row["metro_distance_m"] = ""

        top_indicators = poi_counts[cell].most_common(6)
        top_names = [name for name, _ in poi_names[cell].most_common(5)]
        row["top_amenities"] = "; ".join(top_names)
        for indicator in BASELINE_INDICATORS + TRACK_INDICATORS:
            row[f"poi_{indicator}"] = poi_counts[cell][indicator]
        row["poi_total"] = sum(poi_counts[cell].values())
        row["top_indicator_mix"] = "; ".join(f"{name}:{count}" for name, count in top_indicators)
        rows.append(row)

    return sorted(rows, key=lambda item: float(item["composite_score"]), reverse=True)


def write_csv(rows: list[dict[str, object]]) -> None:
    if not rows:
        raise RuntimeError("No H3 rows generated.")
    fieldnames = list(rows[0].keys())
    with H3_CSV_OUTPUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def compact_props(row: dict[str, object]) -> dict[str, object]:
    return {
        "h": row["h3"],
        "g": row["grid_count"],
        "x": row["lon"],
        "y": row["lat"],
        "d": row["district"],
        "r": row["rent_band_proxy"],
        "a": row["access_band"],
        "am": row["top_amenities"],
        "mx": row["top_indicator_mix"],
        "bs": row["baseline_score"],
        "ts": row["track_score"],
        "cs": row["composite_score"],
        "w_b": row["walk_baseline_score"],
        "w_t": row["walk_track_score"],
        "w_c": row["walk_composite_score"],
        "b_b": row["bike_baseline_score"],
        "b_t": row["bike_track_score"],
        "b_c": row["bike_composite_score"],
        "t_b": row["transit_baseline_score"],
        "t_t": row["transit_track_score"],
        "t_c": row["transit_composite_score"],
        "c_b": row["car_baseline_score"],
        "c_t": row["car_track_score"],
        "c_c": row["car_composite_score"],
        "pr": row["poi_restaurants"],
        "pb": row["poi_bars_night"],
        "pc": row["poi_culture_venues"],
        "pv": row["poi_convenience_24h"],
        "pm": row["poi_metro_late_proxy"],
        "pt": row["poi_total"],
        "md": row["metro_distance_m"],
    }


def compact_web_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    compact = []
    for row in rows:
        score = float(row["composite_score"])
        poi_total = int(row["poi_total"])
        if score <= 0 and poi_total <= 0:
            continue
        item = compact_props(row)
        if isinstance(item.get("am"), str) and len(item["am"]) > 180:
            item["am"] = item["am"][:177] + "..."
        if isinstance(item.get("mx"), str) and len(item["mx"]) > 120:
            item["mx"] = item["mx"][:117] + "..."
        compact.append(item)
    return compact


def write_geojson(rows: list[dict[str, object]]) -> dict[str, object]:
    features = []
    for row in rows:
        props = dict(row)
        cell = str(props["h3"])
        geometry = {
            "type": "Polygon",
            "coordinates": [h3_boundary_geojson(cell)],
        }
        features.append(
            {
                "type": "Feature",
                "id": cell,
                "properties": props,
                "geometry": geometry,
            }
        )
    geojson = {
        "type": "FeatureCollection",
        "name": "Shanghai 15-minute city H3 scores - Track B",
        "features": features,
    }
    GEOJSON_OUTPUT.write_text(json.dumps(geojson, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    WEB_DATA_DIR.mkdir(parents=True, exist_ok=True)
    WEB_COMPACT_JSON_OUTPUT.write_text(
        json.dumps({"hexes": compact_web_rows(rows)}, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    return geojson


def write_metadata(rows: list[dict[str, object]], geojson: dict[str, object]) -> None:
    scores = [float(row["composite_score"]) for row in rows]
    metadata = {
        "project": "15-Minute Shanghai - Track B Entertainment & Nightlife",
        "track": TRACK,
        "h3_resolution": H3_RESOLUTION,
        "hex_count": len(rows),
        "web_hex_count": len(compact_web_rows(rows)),
        "mode_radii_m": MODE_RADII_M,
        "scoring": {
            "baseline_indicators": BASELINE_INDICATORS,
            "baseline_weights": BASELINE_WEIGHTS,
            "track_indicators": TRACK_INDICATORS,
            "track_weights": TRACK_WEIGHTS,
            "composite": "0.6 * walk/bike baseline mean + 0.4 * walk/bike/transit track mean",
            "note": "Mode-specific scores are shown for comparison; car is not used in the main 15MC score.",
        },
        "score_summary": {
            "min": round(min(scores), 2),
            "max": round(max(scores), 2),
            "mean": round(sum(scores) / len(scores), 2),
            "top_hexes": [
                {
                    "h3": row["h3"],
                    "district": row["district"],
                    "score": row["composite_score"],
                    "amenities": row["top_amenities"],
                }
                for row in rows[:10]
            ],
        },
        "data_sources": DATA_SOURCES,
        "limitations": [
            "Euclidean buffers are used as reproducible proxies for 15-minute isochrones because no routing API key was provided.",
            "Late-night transit is proxied by metro/transit POI access; timetable data should replace this in a production submission.",
            "Rent band is a district-level proxy for the required detail panel field, not a listing-derived rent model.",
            "Metro distance is straight-line distance to the nearest metro-tagged POI, not a routed walking distance.",
            "Gaode/Amap POIs may contain duplicates, closed venues, and inconsistent category tags.",
        ],
    }
    WEB_METADATA_OUTPUT.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    rows = aggregate_rows()
    write_csv(rows)
    geojson = write_geojson(rows)
    write_metadata(rows, geojson)
    print(f"Wrote {H3_CSV_OUTPUT} with {len(rows):,} H3 cells")
    print(f"Wrote {GEOJSON_OUTPUT}")
    print(f"Wrote {WEB_COMPACT_JSON_OUTPUT}")
    print(f"Wrote {WEB_METADATA_OUTPUT}")


if __name__ == "__main__":
    main()
