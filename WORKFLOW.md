# Song Recommendation Workflow

This project builds a general-purpose song recommendation graph from Spotify data and prepares it for import into Neo4j. The goal is not to recommend songs only for one listener, but to create a reusable graph structure where any song can be connected to similar songs.

## Overview

The Python workflow has two stages:

1. Clean the raw Spotify CSV so Neo4j can import it reliably.
2. Build a sampled song graph with similarity edges.

The two scripts in this repository are:

- [`clean_spotify_csv.py`](/Users/van/DS4300-HW5/clean_spotify_csv.py)
- [`build_song_graph_data.py`](/Users/van/DS4300-HW5/build_song_graph_data.py)

## Step 1: Clean The Raw CSV

Script:
- [`clean_spotify_csv.py`](/Users/van/DS4300-HW5/clean_spotify_csv.py)

Input:
- `spotify.csv`

Output:
- `spotify_clean.csv`

What this script does:
- removes the unnamed first column from the Kaggle export
- trims whitespace from text fields
- normalizes the `explicit` field to `TRUE` or `FALSE`
- writes a cleaner CSV with stable column names

Why this step matters:
- Neo4j `LOAD CSV` works best when the file has predictable headers
- the original unnamed first column is not useful for the graph
- keeping types and values consistent reduces import errors later

## Step 2: Load And Deduplicate

Script:
- [`build_song_graph_data.py`](/Users/van/DS4300-HW5/build_song_graph_data.py)

Input:
- `spotify_clean.csv`

The script first loads all rows and removes duplicate songs using `track_id`.

Why we do this:
- the raw dataset contains multiple rows for many tracks
- if duplicates remain, Neo4j may create multiple nodes for the same song
- duplicate songs would distort the recommendation graph by over-representing repeated tracks

Why `track_id` is used:
- Spotify `track_id` is the most reliable song identifier in the dataset
- song names alone are not enough because different songs can share titles

## Step 3: Force-Include The Seed Artists

The assignment says the recommendation system should be tested using songs by The Strokes and Regina Spektor. The script therefore always keeps songs whose `artists` field contains either of those names.

Why we do this:
- these songs are the starting points for the recommendation query
- if the graph sample accidentally excluded them, the recommendation step would fail
- force-including them ensures the graph supports the assignment's test case

Why this is still general-purpose:
- these songs are only the seed songs for one test
- the rest of the graph still contains a broad mix of music
- the recommendation method itself can be used for any artist or song in the graph

## Step 4: Sample Additional Songs By Genre

After keeping the seed artists, the script samples additional songs from the rest of the dataset, grouped by `track_genre`.

Default behavior:
- sample up to `35` non-seed songs per genre

Why we sample:
- the full deduplicated dataset is large enough that computing all pairwise similarities would be expensive
- the assignment explicitly allows sampling
- a smaller graph is easier to compute, import, visualize, and explain

Why we sample by genre instead of taking a fully random sample:
- a random sample can over-represent common genres and under-represent rare ones
- genre-based sampling gives the graph broader musical coverage
- that makes the graph more useful as a general recommendation network

Why this helps recommendations:
- recommendations come from a larger and more varied musical space
- the graph is less biased toward only one style of music

## Step 5: Standardize Audio Features

The script represents each song as a numeric feature vector using these columns:

- `danceability`
- `energy`
- `key`
- `loudness`
- `mode`
- `speechiness`
- `acousticness`
- `instrumentalness`
- `liveness`
- `valence`
- `tempo`
- `time_signature`
- `popularity`

Before comparing songs, the script standardizes these values.

What standardization means:
- for each feature, subtract the mean
- divide by the standard deviation

Why we do this:
- the audio features are on very different numeric scales
- for example, `tempo` can be around 60 to 200, while `danceability` is usually between 0 and 1
- without standardization, large-scale features would dominate the distance calculation
- standardization makes each feature contribute more fairly

Why these features were chosen:
- they capture broad musical characteristics from Spotify
- they give a mathematical description of how songs sound and behave
- they are suitable for a general-purpose similarity model

## Step 6: Compute Nearest Neighbors

Once each song has a standardized feature vector, the script computes which songs are closest to each other using Euclidean distance.

What Euclidean distance means:
- treat each song as a point in a multi-dimensional space
- songs that are close together have similar audio characteristics
- songs that are far apart are less similar

The script then connects each song to its `k` nearest neighbors.

Default behavior:
- `k = 5`

Why we do this:
- connecting every pair of songs would create an extremely dense graph
- a dense graph would be slower to build and harder to interpret
- nearest-neighbor edges create a sparse graph that still preserves local similarity structure

Why a sparse graph is better here:
- fewer edges means easier Neo4j import
- query results are cleaner
- the visualization is easier to understand
- the graph remains scalable

Why Euclidean distance was chosen:
- it is intuitive and easy to explain
- it works well once features are standardized
- it makes the recommendation method straightforward to justify in a report

## Step 7: Write The Node CSV

The script writes `song_nodes.csv`, which contains one row per song in the sampled graph.

This file becomes the Neo4j node import source.

Each row includes:
- `track_id`
- `artists`
- `album_name`
- `track_name`
- `track_genre`
- Spotify metadata and audio features

Why we write a separate node CSV:
- Neo4j imports nodes and relationships more cleanly when they are separated
- this makes the graph-building process reproducible
- it also gives a clear record of which songs ended up in the final graph

## Step 8: Write The Edge CSV

The script writes `song_edges.csv`, which contains one row per similarity edge.

Each edge has:
- `source_track_id`
- `target_track_id`
- `distance`
- `score`

What these values mean:
- `distance` is the raw Euclidean distance between two songs
- `score` is a transformed similarity value using `1 / (1 + distance)`

Why store both:
- `distance` preserves the original measurement
- `score` is easier to use in ranking queries because larger values mean stronger similarity

Why we write a separate edge CSV:
- Neo4j can match songs by `track_id` and then create `:SIMILAR` relationships
- separating nodes and edges makes debugging and import much easier

## Resulting Graph Model

The output is designed for this core Neo4j model:

```cypher
(:Song {track_id, track_name, artists, album_name, track_genre, ...})
(:Song)-[:SIMILAR {distance, score}]->(:Song)
```

Why this model was chosen:
- it is simple enough to implement and explain clearly
- it directly supports recommendation queries
- it keeps the focus on song-to-song similarity, which is the main goal of the assignment

## Why This Approach Fits The Assignment

This workflow satisfies the assignment requirements because it:

- builds a reusable recommendation graph rather than a one-off custom query
- includes songs by The Strokes and Regina Spektor for testing
- uses a larger sampled network so the system stays general-purpose
- defines an explicit similarity metric
- creates a graph that is small enough to visualize and discuss on a poster

## Reproducibility

Run the full workflow in this order:

```bash
python3 clean_spotify_csv.py
python3 build_song_graph_data.py
```

This produces:

- `spotify_clean.csv`
- `song_nodes.csv`
- `song_edges.csv`

Those files can then be imported into Neo4j with `LOAD CSV` to create the final recommendation graph.
