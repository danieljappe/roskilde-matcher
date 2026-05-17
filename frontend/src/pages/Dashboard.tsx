import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import { ArtistCard } from "../components/ArtistCard";
import { GenreRadar } from "../components/GenreRadar";
import { useRecommendations, useRefreshRecommendations } from "../hooks/useRecommendations";
import { useSchedule } from "../hooks/useSchedule";
import { useSpotifyAuth } from "../hooks/useSpotifyAuth";
import { getScoreTier, TIER_LABELS, type ScoreTier } from "../types";

export function Dashboard() {
  const { user } = useSpotifyAuth();
  const { data, isLoading, error } = useRecommendations();
  const { mutate: refresh, isPending: isRefreshing } = useRefreshRecommendations();
  const { isSaved, toggle } = useSchedule();
  const [minScore, setMinScore] = useState(0);
  const [genreFilter, setGenreFilter] = useState("");
  const [showEvents, setShowEvents] = useState(false);
  const [debugOpen, setDebugOpen] = useState(false);

  const { data: genreData } = useQuery({
    queryKey: ["genres"],
    queryFn: api.getGenreProfile,
    enabled: !!user,
    staleTime: 5 * 60 * 1000,
  });

  const filtered = (data?.results ?? []).filter((a) => {
    const isEvent = !a.start_time && a.genres.length === 0;
    if (showEvents ? !isEvent : isEvent) return false;
    if (a.composite_score < minScore) return false;
    if (genreFilter && !a.genres.some((g) => g.toLowerCase().includes(genreFilter.toLowerCase())))
      return false;
    return true;
  });

  const tiers: ScoreTier[] = ["must-see", "great-match", "discover", "not-relevant"];
  const grouped = Object.fromEntries(
    tiers.map((t) => [t, filtered.filter((a) => getScoreTier(a.composite_score) === t)])
  ) as Record<ScoreTier, typeof filtered>;

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-10 h-10 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-500 text-sm">Building your recommendations…</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-xl p-8 text-center max-w-sm shadow-sm">
          <p className="text-red-500 font-medium">Failed to load recommendations</p>
          <p className="text-gray-500 text-sm mt-2">{error.message}</p>
          <button
            onClick={() => refresh()}
            className="mt-4 bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-indigo-700"
          >
            Try again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="font-bold text-gray-900">
            🎪 Roskilde Matcher
          </h1>
          <div className="flex items-center gap-3">
            <Link to="/schedule" className="text-sm text-gray-600 hover:text-gray-900 min-h-[44px] flex items-center">
              My Schedule
            </Link>
            <button
              onClick={() => refresh()}
              disabled={isRefreshing}
              className="text-sm bg-indigo-600 text-white px-3 py-2 rounded-lg hover:bg-indigo-700 disabled:opacity-50 min-h-[44px]"
            >
              {isRefreshing ? "Refreshing…" : "Refresh"}
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8">
        {/* Debug accordion */}
        {user && (
          <section className="bg-gray-900 rounded-xl shadow-sm mb-8 text-white overflow-hidden">
            <button
              onClick={() => setDebugOpen((o) => !o)}
              className="w-full flex items-center justify-between px-6 py-4 hover:bg-gray-800 transition-colors"
            >
              <span className="font-semibold text-green-400 text-sm">Debug info</span>
              <span className="text-gray-400 text-xs">{debugOpen ? "▲" : "▼"}</span>
            </button>
            {debugOpen && (
              <div className="px-6 pb-6">
                <h2 className="font-semibold mb-2 text-green-400">top_artists</h2>
                <p className="text-xs text-gray-400 mb-3">
                  short_term: {user.top_artists?.short_term?.length ?? 0} |{" "}
                  medium_term: {user.top_artists?.medium_term?.length ?? 0} |{" "}
                  long_term: {user.top_artists?.long_term?.length ?? 0}
                </p>
                {(["short_term", "medium_term", "long_term"] as const).map((range) => {
                  const artists = user.top_artists?.[range];
                  if (!artists?.length) return null;
                  return (
                    <div key={range} className="mb-4">
                      <h3 className="text-sm font-medium text-gray-300 mb-2 capitalize">{range.replace("_", " ")}</h3>
                      <div className="flex flex-wrap gap-2">
                        {artists.slice(0, 20).map((a, i) => (
                          <span key={a.id} className="text-xs bg-gray-800 px-2 py-1 rounded">
                            {i + 1}. {a.name}
                            {(a.genres?.length ?? 0) > 0 && (
                              <span className="text-gray-500 ml-1">({a.genres.slice(0, 2).join(", ")})</span>
                            )}
                          </span>
                        ))}
                      </div>
                    </div>
                  );
                })}
                <h2 className="font-semibold mb-2 text-yellow-400 mt-4">genre_profile</h2>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(user.genre_profile ?? {})
                    .sort(([, a], [, b]) => b - a)
                    .slice(0, 30)
                    .map(([genre, score]) => (
                      <span key={genre} className="text-xs bg-gray-800 px-2 py-1 rounded">
                        {genre}: <span className="text-yellow-400">{(score as number).toFixed(3)}</span>
                      </span>
                    ))}
                  {Object.keys(user.genre_profile ?? {}).length === 0 && (
                    <span className="text-gray-500 text-xs">empty — run enrichment first</span>
                  )}
                </div>
              </div>
            )}
          </section>
        )}

        {/* Genre radar */}
        {genreData && genreData.genres.length > 0 && (
          <section className="bg-white rounded-xl p-6 shadow-sm mb-8">
            <h2 className="font-semibold text-gray-800 mb-4">Your Genre Profile</h2>
            <GenreRadar genres={genreData.genres} />
          </section>
        )}

        {/* Filters */}
        <div className="bg-white rounded-xl p-4 shadow-sm mb-6 flex flex-wrap gap-4 items-center">
          <button
            onClick={() => setShowEvents((v) => !v)}
            className={`text-sm px-3 py-2 rounded-lg font-medium transition-colors min-h-[44px] ${
              showEvents
                ? "bg-indigo-600 text-white"
                : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}
          >
            {showEvents ? "Events: On" : "Events: Off"}
          </button>
          <div className="flex items-center gap-2">
            <label htmlFor="min-score" className="text-sm text-gray-600 whitespace-nowrap">
              Min score: {Math.round(minScore * 100)}%
            </label>
            <input
              id="min-score"
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={minScore}
              onChange={(e) => setMinScore(Number(e.target.value))}
              className="w-32"
            />
          </div>
          <input
            type="text"
            placeholder="Filter by genre…"
            value={genreFilter}
            onChange={(e) => setGenreFilter(e.target.value)}
            className="border border-gray-200 rounded-lg px-3 py-2 text-sm flex-1 min-w-32 focus:outline-none focus:ring-2 focus:ring-indigo-300"
          />
        </div>

        {/* Tiered sections */}
        {tiers.map((tier) => {
          const artists = grouped[tier];
          if (artists.length === 0) return null;
          return (
            <section key={tier} className="mb-10">
              <h2 className="font-bold text-gray-800 text-lg mb-4">{TIER_LABELS[tier]}</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {artists.map((artist) => (
                  <ArtistCard
                    key={artist.id}
                    artist={artist}
                    isSaved={isSaved(artist.id)}
                    onToggleSave={toggle}
                  />
                ))}
              </div>
            </section>
          );
        })}

        {filtered.length === 0 && (
          <div className="text-center py-16 text-gray-400">
            <p className="text-lg">No artists match your filters</p>
          </div>
        )}
      </main>
    </div>
  );
}
