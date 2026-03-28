// STEP 1) Set seed artists for recommendation algorithm (default assignment artists below)
:param seedArtists => ['The Strokes', 'Regina Spektor']

// STEP 2) Generate recommendations for seed artist(s)
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
  candidate.track_name AS title,
  candidate.artists AS artist,
  candidate.album_name AS album,
  supporting_seed_songs,
  matched_seed_artists,
  round(total_score, 4) AS total_score,
  round(avg_score, 4) AS avg_score
ORDER BY matched_seed_artists DESC,
         supporting_seed_songs DESC,
         total_score DESC,
         avg_score DESC
LIMIT 5;