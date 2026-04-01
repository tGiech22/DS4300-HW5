// Poster helper queries for Neo4j.
// Run these after import_nodes.cypher and import_edges.cypher.

// STEP 1) Set the seed artists used for recommendations and visualization.
:param seedArtists => ['The Strokes', 'Regina Spektor']

// STEP 2) Return the five recommendations with poster-friendly fields.
WITH $seedArtists AS seedArtists
MATCH (seed:Song)-[r:SIMILAR]->(candidate:Song)
WHERE any(a IN seedArtists WHERE seed.artists CONTAINS a)
  AND NOT any(a IN seedArtists WHERE candidate.artists CONTAINS a)
WITH candidate, seedArtists,
     count(DISTINCT seed.track_id) AS supporting_seed_songs,
     sum(r.score) AS total_score,
     avg(r.score) AS avg_score,
     collect(DISTINCT seed.artists) AS supporting_seed_artist_strings
WITH candidate,
     supporting_seed_songs,
     total_score,
     avg_score,
     size([
       a IN seedArtists
       WHERE any(s IN supporting_seed_artist_strings WHERE s CONTAINS a)
     ]) AS matched_seed_artists
WHERE supporting_seed_songs >= 2
RETURN
  candidate.artists AS artist,
  candidate.album_name AS album,
  candidate.track_name AS title,
  supporting_seed_songs,
  matched_seed_artists,
  round(total_score, 4) AS total_score,
  round(avg_score, 4) AS avg_score
ORDER BY matched_seed_artists DESC,
         supporting_seed_songs DESC,
         total_score DESC,
         avg_score DESC
LIMIT 5;

// STEP 3) Count the total graph size for the poster.
CALL {
  MATCH (s:Song)
  RETURN count(s) AS total_nodes
}
CALL {
  MATCH ()-[r:SIMILAR]->()
  RETURN count(r) AS total_edges
}
RETURN total_nodes, total_edges;

// STEP 4) Visualize seed songs and the recommendation paths used to justify them.
// Neo4j Browser will render the returned paths as a graph.
WITH $seedArtists AS seedArtists
MATCH (seed:Song)-[r:SIMILAR]->(candidate:Song)
WHERE any(a IN seedArtists WHERE seed.artists CONTAINS a)
  AND NOT any(a IN seedArtists WHERE candidate.artists CONTAINS a)
WITH candidate,
     collect(DISTINCT seed) AS seeds,
     count(DISTINCT seed.track_id) AS supporting_seed_songs,
     sum(r.score) AS total_score
WHERE supporting_seed_songs >= 2
ORDER BY total_score DESC
LIMIT 5
UNWIND seeds AS seed
MATCH path = (seed)-[:SIMILAR]->(candidate)
RETURN path;
