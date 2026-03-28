// Import song nodes into neo4j database
LOAD CSV WITH HEADERS
FROM 'file:///song_nodes.csv' AS row
MERGE (s:Song {track_id: row.track_id})
SET s.artists = row.artists,
    s.album_name = row.album_name,
    s.track_name = row.track_name,
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
    s.track_genre = row.track_genre;