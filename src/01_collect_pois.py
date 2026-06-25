from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

import shapefile

from config import CATEGORY_RULES, PROCESSED_DIR, RAW_SHP_DIR


OUTPUT = PROCESSED_DIR / "poi_catalog.csv"
SUMMARY_OUTPUT = PROCESSED_DIR / "poi_summary.json"


def read_shapefile(path: Path) -> shapefile.Reader:
    try:
        return shapefile.Reader(str(path), encoding="utf-8")
    except UnicodeDecodeError:
        return shapefile.Reader(str(path), encoding="gb18030")


def normalize_text(value: object) -> str:
    if value is None:
        return ""
    text = str(value)
    return re.sub(r"\s+", " ", text).strip()


def classify_record(record: dict[str, object]) -> list[str]:
    haystack = " | ".join(
        normalize_text(record.get(key))
        for key in ("name", "type", "行业大", "行业中", "行业小")
    ).upper()
    indicators: list[str] = []
    for rule in CATEGORY_RULES:
        for keyword in rule["keywords"]:
            if keyword.upper() in haystack:
                indicators.append(rule["indicator"])
                break
    return sorted(set(indicators))


def iter_pois() -> Iterable[dict[str, object]]:
    for shp_path in sorted(RAW_SHP_DIR.glob("*.shp")):
        reader = read_shapefile(shp_path)
        for sr in reader.iterShapeRecords():
            record = sr.record.as_dict()
            indicators = classify_record(record)
            if not indicators:
                continue

            try:
                lon = float(record.get("经度") or sr.shape.points[0][0])
                lat = float(record.get("纬度") or sr.shape.points[0][1])
            except (ValueError, TypeError, IndexError):
                continue

            if not (70 <= lon <= 140 and 15 <= lat <= 55):
                continue

            yield {
                "id": normalize_text(record.get("id")) or f"{shp_path.stem}-{record.get('OBJECTID', '')}",
                "name": normalize_text(record.get("name")),
                "type": normalize_text(record.get("type")),
                "address": normalize_text(record.get("address")),
                "district": normalize_text(record.get("adname")),
                "lon": f"{lon:.8f}",
                "lat": f"{lat:.8f}",
                "indicators": "|".join(indicators),
                "source_file": shp_path.name,
                "timestamp": normalize_text(record.get("timestamp")),
            }


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "id",
        "name",
        "type",
        "address",
        "district",
        "lon",
        "lat",
        "indicators",
        "source_file",
        "timestamp",
    ]

    summary = {
        "total_pois": 0,
        "by_indicator": Counter(),
        "by_source_file": Counter(),
        "by_district": Counter(),
        "examples": defaultdict(list),
    }

    with OUTPUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in iter_pois():
            writer.writerow(row)
            summary["total_pois"] += 1
            summary["by_source_file"][row["source_file"]] += 1
            if row["district"]:
                summary["by_district"][row["district"]] += 1
            for indicator in row["indicators"].split("|"):
                summary["by_indicator"][indicator] += 1
                if len(summary["examples"][indicator]) < 5:
                    summary["examples"][indicator].append(
                        {
                            "name": row["name"],
                            "type": row["type"],
                            "district": row["district"],
                        }
                    )

    serializable = {
        "total_pois": summary["total_pois"],
        "by_indicator": dict(summary["by_indicator"].most_common()),
        "by_source_file": dict(summary["by_source_file"].most_common()),
        "by_district": dict(summary["by_district"].most_common()),
        "examples": dict(summary["examples"]),
    }
    SUMMARY_OUTPUT.write_text(json.dumps(serializable, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUTPUT} with {summary['total_pois']:,} classified POIs")
    print(f"Wrote {SUMMARY_OUTPUT}")


if __name__ == "__main__":
    main()
