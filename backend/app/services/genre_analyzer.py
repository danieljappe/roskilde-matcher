from __future__ import annotations

from thefuzz import fuzz

FUZZY_MATCH_THRESHOLD = 0.6


def _root_genre_match(artist_genre: str, user_genre: str) -> bool:
    """Check if any word token is shared between two genre strings."""
    artist_tokens = set(artist_genre.lower().split())
    user_tokens = set(user_genre.lower().split())
    return bool(artist_tokens & user_tokens)


def _best_match_score(artist_genre: str, user_genres: dict[str, float]) -> tuple[float, float]:
    """
    Return (match_quality, user_affinity) for the best matching user genre.
    match_quality: 1.0 exact, 0.8 root, fuzzy score otherwise
    """
    best_quality = 0.0
    best_affinity = 0.0

    artist_genre_lower = artist_genre.lower()

    for user_genre, affinity in user_genres.items():
        user_genre_lower = user_genre.lower()

        # Level 1: exact match
        if artist_genre_lower == user_genre_lower:
            if affinity > best_affinity or (affinity == best_affinity and 1.0 > best_quality):
                best_quality = 1.0
                best_affinity = affinity
            continue

        # Level 2: root-genre token match
        if _root_genre_match(artist_genre_lower, user_genre_lower):
            quality = 0.8
        else:
            # Level 3: fuzzy match
            ratio = fuzz.token_set_ratio(artist_genre_lower, user_genre_lower) / 100.0
            quality = ratio if ratio >= FUZZY_MATCH_THRESHOLD else 0.0

        if quality > best_quality or (quality == best_quality and affinity > best_affinity):
            best_quality = quality
            best_affinity = affinity

    return best_quality, best_affinity


def compute_genre_match(user_genres: dict[str, float], artist_genres: list[str]) -> float:
    """
    Compute genre match score between a user's genre profile and an artist's genres.
    Returns a float in [0, 1].
    """
    if not artist_genres or not user_genres:
        return 0.0

    total = 0.0
    for artist_genre in artist_genres:
        quality, affinity = _best_match_score(artist_genre, user_genres)
        total += quality * affinity

    # Sum contributions and cap at 1.0 — no penalty for unmatched genres
    return min(total, 1.0)
