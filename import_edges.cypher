// Import song edges into neo4j database
LOAD CSV WITH HEADERS
FROM 'file:///song_edges.csv' AS row
WITH row
WHERE row.source_track_id IS NOT NULL
  AND row.target_track_id IS NOT NULL
  AND row.source_track_id <> ''
  AND row.target_track_id <> ''
MATCH (source:Song {track_id: row.source_track_id})
MATCH (target:Song {track_id: row.target_track_id})
WHERE source <> target
MERGE (source)-[r:SIMILAR]->(target)
SET r.distance = toFloat(row.distance),
    r.score = toFloat(row.score);