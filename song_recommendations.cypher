// STEP 1) Set the seed artists used to start the recommendation search.
:param seedArtists => ['The Strokes', 'Regina Spektor']

// STEP 2) Expand the seed artist list into a query variable.
WITH $seedArtists AS seedArtists

// Find candidate songs reachable by SIMILAR edges from seed songs.
MATCH (seed:Song)-[r:SIMILAR]->(candidate:Song)

// Keep only seed songs by the selected artists, and exclude recommending those artists back.
WHERE any(a IN seedArtists WHERE seed.artists CONTAINS a)
  AND NOT any(a IN seedArtists WHERE candidate.artists CONTAINS a)

// Aggregate recommendation evidence for each candidate song.
WITH candidate, seedArtists,
     count(DISTINCT seed.track_id) AS supporting_seed_songs,           
     sum(r.score) AS total_score,                                      
     avg(r.score) AS avg_score,                                        
     collect(DISTINCT seed.artists) AS supporting_seed_artist_strings  

// Count how many of the selected seed artists are represented in the support set.
WITH candidate,
     supporting_seed_songs,
     total_score,
     avg_score,
     size([
       a IN seedArtists
       WHERE any(s IN supporting_seed_artist_strings WHERE s CONTAINS a)
     ]) AS matched_seed_artists

// Require at least minimal graph evidence before recommending a song.
WHERE supporting_seed_songs >= 2

// Return the final recommendation table.
RETURN
  candidate.artists AS artist,
  candidate.album_name AS album,
  candidate.track_name AS title,
  supporting_seed_songs,
  matched_seed_artists,
  round(total_score, 4) AS total_score,
  round(avg_score, 4) AS avg_score

// Rank by breadth of support first, then by score.
ORDER BY matched_seed_artists DESC,
         supporting_seed_songs DESC,
         total_score DESC,
         avg_score DESC,
         artist ASC,
         title ASC

// Return the top 5 recommendations.
LIMIT 5;