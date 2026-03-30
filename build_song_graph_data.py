#!/usr/bin/env python3
"""Build Neo4j-ready song nodes and similarity edges from Spotify data.

This script:
- loads the cleaned Spotify CSV
- removes duplicate tracks
- force-includes songs by The Strokes and Regina Spektor
- samples additional songs across genres
- standardizes selected audio features
- computes k-nearest-neighbor similarity edges
- writes node and edge CSV files for Neo4j import

It uses only the Python standard library so it can run in a minimal setup.

Example:
    python3 build_song_graph_data.py
    python3 build_song_graph_data.py --songs-per-genre 25 --k 5
"""

from __future__ import annotations

import argparse
import csv
import math
import random
import statistics
from pathlib import Path

# -- STEP 1: DEFINE ATTRIBUTES -- # 

# attributes for comparing features between tracks 
FEATURE_COLUMNS = [
    "danceability",
    "energy",
    "loudness",
    "speechiness",
    "acousticness",
    "instrumentalness",
    "liveness",
    "valence",
    "tempo",
]

# attributes unique to a specific song
NODE_COLUMNS = [
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

# -- STEP 2: ADD ARGUMENTS TO FEED INTO GRAPH -- # 
def parse_args() -> argparse.Namespace:
    """
    Function: add and parses arguments to build nodes and edges for Neo4j; elimates need to hardcode values (i.e., k = 8, min_score = 0.35)
    Returns: parse ns arguments 
    """
    parser = argparse.ArgumentParser(description="Build song graph CSVs for Neo4j.")
    parser.add_argument("--input", default="spotify_clean.csv", help="Cleaned Spotify CSV input.")
    parser.add_argument("--nodes-output", default="song_nodes.csv", help="Node CSV output path.")
    parser.add_argument("--edges-output", default="song_edges.csv", help="Edge CSV output path.")
    parser.add_argument(
        "--songs-per-genre",
        type=int,
        default=35,
        help="How many non-seed songs to sample from each genre.",
    )
    parser.add_argument(
        "--k",
        type=int,
        default=8,
        help="How many nearest neighbors to connect for each song.",
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="Random seed for reproducible genre sampling.",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.35,
        help="Minimum similarity score required to create an edge.",
    )
    parser.add_argument(
    "--force-include-artists",
    nargs="*",
    default=["The Strokes", "Regina Spektor"],
    help="Artists to guarantee in the sampled graph.",
    )
    return parser.parse_args()

EDGE_COLUMNS = ["source_track_id", "target_track_id", "distance", "score"]


def load_and_deduplicate(input_path: Path) -> list[dict[str, str]]:
    """
    Function: deduplicated track_ids
    Returns: list of dicts containing track_id and data inside
    """
    seen_track_ids: set[str] = set()
    rows: list[dict[str, str]] = []
    with input_path.open("r", newline="", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            track_id = row["track_id"]
            if track_id in seen_track_ids:
                continue
            seen_track_ids.add(track_id)
            rows.append(row)
    return rows


def is_seed_song(row: dict[str, str], seed_artists: list[str]) -> bool:
    """
    Function: check whether artist exists in seed_artists 
    Returns: bool 
    """
    artists = row.get("artists", "")
    return any(artist in artists for artist in seed_artists)


def split_seed_and_other_songs(
    rows: list[dict[str, str]],
    seed_artists: list[str],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """
    Function: Assign seed artists to rows that are is_seed_song
    Returns: List of dictionaries containing strings 
    """
    seed_songs = [row for row in rows if is_seed_song(row, seed_artists)]
    other_songs = [row for row in rows if not is_seed_song(row, seed_artists)]
    return seed_songs, other_songs


def sample_by_genre(
    other_songs: list[dict[str, str]], songs_per_genre: int, random_state: int
) -> list[dict[str, str]]:
    """
    Function: create random_state samples to ensure reproducibility in KNN
    Returns: list of dictionaries containing strings 
    """
    rng = random.Random(random_state)
    songs_by_genre: dict[str, list[dict[str, str]]] = {}
    for row in other_songs:
        genre = row.get("track_genre", "") or "unknown"
        songs_by_genre.setdefault(genre, []).append(row)

    sampled_rows: list[dict[str, str]] = []
    for genre_rows in songs_by_genre.values():
        if len(genre_rows) <= songs_per_genre:
            sampled_rows.extend(genre_rows)
        else:
            sampled_rows.extend(rng.sample(genre_rows, songs_per_genre))
    return sampled_rows


def build_sampled_song_set(
    rows: list[dict[str, str]], 
    songs_per_genre: int, 
    random_state: int,
    seed_artists: list[str],
) -> list[dict[str, str]]:
    """
    Function: turn seen_track_ids into a set without duplicates and list containing seed/sampled songs
    Returns: list of dictionaries containing strings
    """
    seed_songs, other_songs = split_seed_and_other_songs(rows, seed_artists)
    sampled_other_songs = sample_by_genre(other_songs, songs_per_genre, random_state)

    combined_rows: list[dict[str, str]] = []
    seen_track_ids: set[str] = set()
    for row in seed_songs + sampled_other_songs:
        track_id = row["track_id"]
        if track_id in seen_track_ids:
            continue
        seen_track_ids.add(track_id)
        combined_rows.append(row)
    return combined_rows

# -- STEP 3: FEATURE ENGINEERING -- # 
def standardize_features(
    rows: list[dict[str, str]],
) -> tuple[list[dict[str, str]], list[list[float]]]:
    """
    Function: create an immutable tuple containing standardized features 
    Returns: tupled list of dictionaries 
    """
    valid_rows: list[dict[str, str]] = []
    raw_feature_vectors: list[list[float]] = []

    # vectorize each value in feature_column 
    for row in rows:
        try:
            vector = [float(row[column]) for column in FEATURE_COLUMNS]
        except (TypeError, ValueError):
            continue
        valid_rows.append(row)
        raw_feature_vectors.append(vector)

    # unzips vector and transposes it into a tuple 
    means = [statistics.fmean(column) for column in zip(*raw_feature_vectors)] 
    stdevs: list[float] = [] 
    
    # calculate stdev for each column in tuple (each row in tuple is functionally a column)
    for column in zip(*raw_feature_vectors):
        try:
            stdev = statistics.pstdev(column) 
        except statistics.StatisticsError:
            stdev = 0.0
        stdevs.append(stdev if stdev != 0 else 1.0)

    scaled_vectors: list[list[float]] = []
    for vector in raw_feature_vectors:
        scaled_vectors.append(
            [(value - mean) / stdev for value, mean, stdev in zip(vector, means, stdevs)]
        )

    return valid_rows, scaled_vectors

# -- STEP 4: FIND DISTANCE AND SIMILARITY -- # 
def euclidean_distance(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((left - right) ** 2 for left, right in zip(a, b)))


def compute_similarity_edges(
    rows: list[dict[str, str]],
    scaled_features: list[list[float]],
    k: int,
    min_score: float,
) -> list[dict[str, object]]:
    if len(rows) <= 1:
        return []

    edge_rows: list[dict[str, object]] = []
    neighbor_count = min(k, len(rows) - 1)

    for source_idx, source_vector in enumerate(scaled_features):
        distances: list[tuple[float, int, float]] = []

        # append score if vectors are similar 
        for target_idx, target_vector in enumerate(scaled_features):
            if source_idx == target_idx:
                continue

            distance = euclidean_distance(source_vector, target_vector)
            score = 1.0 / (1.0 + distance)

            # do not append if vectors are dissimilar 
            if score < min_score:
                continue

            distances.append((distance, target_idx, score)) 

        distances.sort(key=lambda item: item[0])

        for distance, target_idx, score in distances[:neighbor_count]:
            edge_rows.append(
                {
                    "source_track_id": rows[source_idx]["track_id"],
                    "target_track_id": rows[target_idx]["track_id"],
                    "distance": round(distance, 6),
                    "score": round(score, 6),
                }
            )

    return edge_rows


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    nodes_output = Path(args.nodes_output)
    edges_output = Path(args.edges_output)

    all_rows = load_and_deduplicate(input_path)
    sampled_rows = build_sampled_song_set(all_rows, args.songs_per_genre, args.random_state, args.force_include_artists)
    sampled_rows, scaled_features = standardize_features(sampled_rows)

    node_rows = [{column: row[column] for column in NODE_COLUMNS} for row in sampled_rows]
    edge_rows = compute_similarity_edges(sampled_rows, scaled_features, args.k, args.min_score)

    write_csv(nodes_output, node_rows, NODE_COLUMNS)
    write_csv(edges_output, edge_rows, EDGE_COLUMNS)

    seed_count = sum(1 for row in sampled_rows if is_seed_song(row, args.force_include_artists))
    print(f"Input songs after deduplication: {len(all_rows)}")
    print(f"Sampled graph songs: {len(node_rows)}")
    print(f"Seed songs included: {seed_count}")
    print(f"Similarity edges written: {len(edge_rows)}")
    print(f"Node CSV: {nodes_output}")
    print(f"Edge CSV: {edges_output}")


if __name__ == "__main__":
    main()
