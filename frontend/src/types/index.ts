export interface TopArtistEntry {
  id: string;
  name: string;
  genres: string[];
  popularity: number;
  images: { url: string }[];
}

export interface AuthUser {
  spotify_id: string;
  display_name: string | null;
  refreshed_at: string | null;
  top_artists: {
    short_term?: TopArtistEntry[];
    medium_term?: TopArtistEntry[];
    long_term?: TopArtistEntry[];
  };
  genre_profile: Record<string, number>;
}

export interface FestivalArtist {
  id: number;
  name: string;
  genres: string[];
  popularity: number | null;
  image_url: string | null;
  spotify_id: string | null;
  stage: string | null;
  start_time: string | null;
  end_time: string | null;
  is_music: boolean;
}

export interface FestivalArtistDetail extends FestivalArtist {
  related_artists: { id: string; name: string }[];
}

export interface RecommendedArtist extends FestivalArtist {
  composite_score: number;
  genre_match_score: number;
  artist_match_score: number;
  discovery_score: number;
}

export interface RecommendationListResponse {
  user_spotify_id: string;
  refreshed_at: string | null;
  results: RecommendedArtist[];
}

export interface GenreScore {
  name: string;
  score: number;
}

export interface GenreProfileResponse {
  genres: GenreScore[];
}

export type ScoreTier = "must-see" | "great-match" | "discover" | "not-relevant";

export function getScoreTier(score: number): ScoreTier {
  if (score >= 0.65) return "must-see";
  if (score >= 0.45) return "great-match";
  if (score >= 0.20) return "discover";
  return "not-relevant";
}

export const TIER_LABELS: Record<ScoreTier, string> = {
  "must-see": "Must See",
  "great-match": "Great Match",
  "discover": "Discover Something New",
  "not-relevant": "Not Relevant",
};

export const TIER_COLORS: Record<ScoreTier, string> = {
  "must-see": "bg-green-500",
  "great-match": "bg-blue-500",
  "discover": "bg-yellow-500",
  "not-relevant": "bg-gray-400",
};
