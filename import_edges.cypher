// Import similarity edges into Neo4j from the prepared CSV.
LOAD CSV WITH HEADERS
FROM 'file:///song_edges.csv' AS row
WITH row
WHERE row.source_track_id IS NOT NULL
  AND row.target_track_id IS NOT NULL
  AND trim(row.source_track_id) <> ''
  AND trim(row.target_track_id) <> ''
MATCH (source:Song {track_id: trim(row.source_track_id)})
MATCH (target:Song {track_id: trim(row.target_track_id)})
WHERE source <> target
MERGE (source)-[r:SIMILAR]->(target)
SET r.distance = toFloat(row.distance),
    r.score = toFloat(row.score);
