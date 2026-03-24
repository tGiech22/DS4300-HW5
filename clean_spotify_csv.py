#!/usr/bin/env python3
"""Clean spotify.csv for Neo4j import.

This script:
- removes the unnamed first column
- trims whitespace from text fields
- normalizes booleans to TRUE/FALSE
- preserves numeric values as strings so Neo4j can cast them with toInteger/toFloat
- writes a clean CSV with stable column names

Usage:
    python3 clean_spotify_csv.py
    python3 clean_spotify_csv.py --input spotify.csv --output spotify_clean.csv
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


OUTPUT_COLUMNS = [
    "track_id",
    "artists",
    "album_name",
    "track_name",
    "popularity",
    "duration_ms",
    "explicit",
    "danceability",
    "energy",
    "key",
    "loudness",
    "mode",
    "speechiness",
    "acousticness",
    "instrumentalness",
    "liveness",
    "valence",
    "tempo",
    "time_signature",
    "track_genre",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clean spotify.csv for Neo4j import.")
    parser.add_argument("--input", default="spotify.csv", help="Path to the raw Spotify CSV.")
    parser.add_argument(
        "--output",
        default="spotify_clean.csv",
        help="Path for the cleaned CSV output.",
    )
    return parser.parse_args()


def normalize_text(value: str) -> str:
    return value.strip()


def normalize_bool(value: str) -> str:
    lowered = value.strip().lower()
    if lowered in {"true", "1", "yes"}:
        return "TRUE"
    if lowered in {"false", "0", "no"}:
        return "FALSE"
    return value.strip().upper()


def clean_row(row: dict[str, str]) -> dict[str, str]:
    cleaned: dict[str, str] = {}
    for column in OUTPUT_COLUMNS:
        value = row.get(column, "")
        if column == "explicit":
            cleaned[column] = normalize_bool(value)
        else:
            cleaned[column] = normalize_text(value)
    return cleaned


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)

    with input_path.open("r", newline="", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        missing_columns = [column for column in OUTPUT_COLUMNS if column not in reader.fieldnames]
        if missing_columns:
            missing = ", ".join(missing_columns)
            raise ValueError(f"Input CSV is missing expected columns: {missing}")

        with output_path.open("w", newline="", encoding="utf-8") as outfile:
            writer = csv.DictWriter(outfile, fieldnames=OUTPUT_COLUMNS)
            writer.writeheader()

            row_count = 0
            for row in reader:
                writer.writerow(clean_row(row))
                row_count += 1

    print(f"Wrote {row_count} cleaned rows to {output_path}")


if __name__ == "__main__":
    main()
