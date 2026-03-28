// STEP 1) Set seed artists for recommendation algorithm (default assignment artists below)
:param seedArtists => ['The Strokes', 'Regina Spektor']

// STEP 2) Generate recommendations for seed artist(s)
WITH $seedArtists AS seedArtists,
     $seedArtists[0] AS artistA,
     $seedArtists[1] AS artistB

MATCH (seed:Song)-[r:SIMILAR]->(candidate:Song)
WHERE any(a IN seedArtists WHERE seed.artists CONTAINS a)
  AND NOT any(a IN seedArtists WHERE candidate.artists CONTAINS a)

WITH candidate, artistA, artistB,
     count(DISTINCT seed.track_id) AS supporting_seed_songs,
     sum(r.score) AS total_score,
     avg(r.score) AS avg_score,
     max(CASE WHEN seed.artists CONTAINS artistA THEN 1 ELSE 0 END) AS has_artistA,
     max(CASE WHEN seed.artists CONTAINS artistB THEN 1 ELSE 0 END) AS has_artistB,
     sum(CASE WHEN seed.artists CONTAINS artistA THEN r.score ELSE 0.0 END) AS artistA_score,
     sum(CASE WHEN seed.artists CONTAINS artistB THEN r.score ELSE 0.0 END) AS artistB_score

WHERE supporting_seed_songs >= 2

RETURN
  candidate.track_name AS title,
  candidate.artists AS artist,
  candidate.album_name AS album,
  supporting_seed_songs,
  has_artistA + has_artistB AS matched_seed_artists,
  round(artistA_score, 4) AS artistA_score,
  round(artistB_score, 4) AS artistB_score,
  round(total_score, 4) AS total_score,
  round(avg_score, 4) AS avg_score
ORDER BY matched_seed_artists DESC, supporting_seed_songs DESC, total_score DESC, avg_score DESC
LIMIT 5;