# Graph-Based Music Recommendation Engine

A song recommendation system built on a **Neo4j graph database** and the Spotify Tracks dataset (~114K songs). The project transforms a flat CSV of audio features into a similarity graph where any song can be connected to the songs that sound most like it, then generates recommendations by traversing those relationships in Cypher.

Built for Northeastern University's DS4300 (Large-Scale Information Storage and Retrieval).

---

## Overview

Rather than recommending songs for a single user, this project builds a **reusable similarity network**: every song is a node, and edges connect each song to its nearest neighbors in audio-feature space. Recommendations for one or more "seed" artists are produced on top of this graph by following similarity edges and ranking the candidates that surface most strongly.

The pipeline is fully reproducible and uses **only the Python standard library** — no pandas, scikit-learn, or external dependencies required.

```
spotify.csv  ──►  clean  ──►  sample + feature engineering + kNN  ──►  nodes.csv / edges.csv  ──►  Neo4j  ──►  recommendations
```

## Key Features

- **End-to-end data pipeline** — cleaning, deduplication, genre-stratified sampling, feature standardization, and k-nearest-neighbor edge construction.
- **From-scratch similarity model** — z-score standardization and Euclidean distance over 9 audio features, implemented without ML libraries.
- **Graph data modeling** — a clean `(:Song)-[:SIMILAR]->(:Song)` schema with weighted edges, imported via parameterized Cypher.
- **Generalizable recommendation logic** — works for any number of seed artists present in the graph; nothing is hardcoded to a specific test case.
- **Reproducible & configurable** — every parameter (sample size, `k`, similarity threshold, seed artists, random seed) is exposed as a CLI argument.

## Tech Stack

| Layer | Tools |
|-------|-------|
| Data processing | Python 3 (standard library only) |
| Graph database | Neo4j + Cypher |
| Data source | [Spotify Tracks Dataset](https://www.kaggle.com/datasets/maharshipandya/-spotify-tracks-dataset) (Kaggle) |

---

## How It Works

### 1. Data Cleaning — [`clean_spotify_csv.py`](clean_spotify_csv.py)
Strips the unnamed index column from the Kaggle export, trims whitespace, and normalizes the `explicit` field to `TRUE`/`FALSE`, producing a CSV with stable headers that Neo4j's `LOAD CSV` can import reliably.

### 2. Graph Construction — [`build_song_graph_data.py`](build_song_graph_data.py)
1. **Deduplicate** tracks by Spotify `track_id` so repeated rows don't over-represent songs.
2. **Sample by genre** (default 35 songs/genre) to keep the graph small while preserving musical diversity — avoiding the over-representation of common genres that a uniform random sample would produce.
3. **Standardize** 9 audio features (`danceability`, `energy`, `loudness`, `speechiness`, `acousticness`, `instrumentalness`, `liveness`, `valence`, `tempo`) via z-scores so no large-scale feature (e.g. tempo) dominates the distance metric.
4. **Build kNN edges** — for each song, connect to its `k` nearest neighbors by Euclidean distance, keeping only edges above a minimum similarity score. This yields a sparse, interpretable graph.
5. **Export** `song_nodes.csv` and `song_edges.csv` for Neo4j import.

Similarity is stored as both the raw `distance` and a ranking-friendly `score = 1 / (1 + distance)`.

### 3. Graph Model

```cypher
(:Song {track_id, track_name, artists, album_name, track_genre, ...audio features})
(:Song)-[:SIMILAR {distance, score}]->(:Song)
```

### 4. Recommendation Query — [`song_recommendations.cypher`](song_recommendations.cypher)
Given a list of seed artists, the query traverses outgoing `:SIMILAR` edges from their songs, excludes the seed artists themselves, aggregates the candidates, and ranks them by:
1. number of seed artists connected to the candidate,
2. number of seed songs supporting it,
3. total similarity score, then
4. average similarity score.

The same query pattern works for any seed artists in the graph.

---

## Running the Pipeline

**Prerequisites:** Python 3.9+ and a running Neo4j instance.

```bash
# 1. Clean the raw dataset
python3 clean_spotify_csv.py

# 2. Build the graph CSVs (all parameters are configurable)
python3 build_song_graph_data.py \
    --songs-per-genre 35 \
    --k 8 \
    --min-score 0.35 \
    --force-include-artists "The Strokes" "Regina Spektor"
```

This produces `spotify_clean.csv`, `song_nodes.csv`, and `song_edges.csv`.

**Import into Neo4j:**
1. Copy `song_nodes.csv` and `song_edges.csv` into Neo4j's `import/` folder.
2. Run [`import_nodes.cypher`](import_nodes.cypher), then [`import_edges.cypher`](import_edges.cypher) in the Neo4j Browser.

**Generate recommendations:**
- Open [`song_recommendations.cypher`](song_recommendations.cypher), set the `seedArtists` parameter, and run.
- [`poster_queries.cypher`](poster_queries.cypher) contains additional queries for graph-size statistics and path visualization.

---

## Repository Structure

| File | Purpose |
|------|---------|
| [`clean_spotify_csv.py`](clean_spotify_csv.py) | Normalize the raw Kaggle CSV for import |
| [`build_song_graph_data.py`](build_song_graph_data.py) | Build the similarity graph (nodes + edges) |
| [`import_nodes.cypher`](import_nodes.cypher) | Load `Song` nodes into Neo4j |
| [`import_edges.cypher`](import_edges.cypher) | Create `:SIMILAR` relationships |
| [`song_recommendations.cypher`](song_recommendations.cypher) | Generate recommendations from seed artists |
| [`poster_queries.cypher`](poster_queries.cypher) | Graph statistics and visualization queries |
| [`WORKFLOW.md`](WORKFLOW.md) | Detailed design rationale for each pipeline step |

For an in-depth explanation of every design decision, see [`WORKFLOW.md`](WORKFLOW.md).
