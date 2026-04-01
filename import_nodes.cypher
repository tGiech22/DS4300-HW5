// Create a stable key for Song nodes before import.
CREATE CONSTRAINT song_track_id IF NOT EXISTS
FOR (s:Song)
REQUIRE s.track_id IS UNIQUE;

// Import song nodes into Neo4j from the prepared CSV.
LOAD CSV WITH HEADERS
FROM 'file:///song_nodes.csv' AS row
WITH row
WHERE row.track_id IS NOT NULL
  AND trim(row.track_id) <> ''
MERGE (s:Song {track_id: trim(row.track_id)})
SET s.artists = trim(row.artists),
    s.album_name = trim(row.album_name),
    s.track_name = trim(row.track_name),
    s.popularity = toInteger(row.popularity),
    s.duration_ms = toInteger(row.duration_ms),
    s.explicit = toBoolean(row.explicit),
    s.danceability = toFloat(row.danceability),
    s.energy = toFloat(row.energy),
    s.key = toInteger(row.key),
    s.loudness = toFloat(row.loudness),
    s.mode = toInteger(row.mode),
    s.speechiness = toFloat(row.speechiness),
    s.acousticness = toFloat(row.acousticness),
    s.instrumentalness = toFloat(row.instrumentalness),
    s.liveness = toFloat(row.liveness),
    s.valence = toFloat(row.valence),
    s.tempo = toFloat(row.tempo),
    s.time_signature = toInteger(row.time_signature),
    s.track_genre = trim(row.track_genre);
