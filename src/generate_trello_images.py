from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "trello_images"
PROCESSED = ROOT / "data" / "processed"


def save_poi_indicator_chart() -> None:
    summary = json.loads((PROCESSED / "poi_summary.json").read_text(encoding="utf-8"))
    counts = summary["by_indicator"]
    names = list(counts.keys())
    values = list(counts.values())

    fig, ax = plt.subplots(figsize=(10, 5.5))
    bars = ax.bar(names, values, color=["#0f766e", "#d97706", "#4d7c0f", "#b45309", "#1d4ed8"] * 3)
    ax.set_title("Shanghai POI Counts by Indicator")
    ax.set_ylabel("POI count")
    ax.set_xlabel("Indicator")
    ax.tick_params(axis="x", rotation=35, labelsize=9)
    ax.grid(axis="y", linestyle="--", alpha=0.25)
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, value, f"{value:,}", ha="center", va="bottom", fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "01_poi_indicator_counts.png", dpi=180)
    plt.close(fig)


def save_grid_scatter() -> None:
    grid = pd.read_csv(PROCESSED / "grid_cells.csv")
    sample = grid.sample(min(12000, len(grid)), random_state=42)
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.scatter(sample["lon"], sample["lat"], s=2, alpha=0.35, color="#0f766e")
    ax.set_title("500 m Analysis Grid Sample")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(alpha=0.2, linestyle=":")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "02_grid_sample.png", dpi=180)
    plt.close(fig)


def save_h3_score_map() -> None:
    df = pd.read_csv(PROCESSED / "h3_scores_track_b.csv")
    sample = df.sample(min(15000, len(df)), random_state=7)
    fig, ax = plt.subplots(figsize=(8, 7))
    sc = ax.scatter(
        sample["lon"],
        sample["lat"],
        c=sample["composite_score"],
        cmap="YlOrRd",
        s=5,
        alpha=0.8,
        linewidths=0,
    )
    ax.set_title("Track B Composite Score Distribution")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_aspect("equal", adjustable="box")
    fig.colorbar(sc, ax=ax, label="Composite score")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "03_h3_score_map.png", dpi=180)
    plt.close(fig)


def save_top_hex_table() -> None:
    rows = list(csv.DictReader((PROCESSED / "h3_scores_track_b.csv").open(encoding="utf-8")))[:8]
    table_rows = [
        [r["district"], r["composite_score"], r["baseline_score"], r["track_score"], r["top_amenities"][:38] + "..."]
        for r in rows
    ]
    fig, ax = plt.subplots(figsize=(12, 3.8))
    ax.axis("off")
    ax.set_title("Top H3 Cells for Track B", fontsize=14, pad=12)
    table = ax.table(
        cellText=table_rows,
        colLabels=["District", "Composite", "Baseline", "Nightlife", "Top amenities"],
        loc="center",
        cellLoc="left",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, 1.5)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "04_top_hex_table.png", dpi=180)
    plt.close(fig)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    save_poi_indicator_chart()
    save_grid_scatter()
    save_h3_score_map()
    save_top_hex_table()
    print(f"Wrote images to {OUT_DIR}")


if __name__ == "__main__":
    main()
