import { useQuery } from "@tanstack/react-query";
import { useParams, Link } from "react-router-dom";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../api/client";
import { GenreTag } from "../components/GenreTag";
import { SpotifyEmbed } from "../components/SpotifyEmbed";
import { useSchedule } from "../hooks/useSchedule";

export function ArtistDetail() {
  const { id } = useParams<{ id: string }>();
  const artistId = Number(id);
  const { isSaved, toggle } = useSchedule();

  const { data: artist, isLoading, error } = useQuery({
    queryKey: ["artist", artistId],
    queryFn: () => api.getArtist(artistId),
    enabled: !isNaN(artistId),
  });

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (error || !artist) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="text-center">
          <p className="text-gray-500">Artist not found</p>
          <Link to="/dashboard" className="text-indigo-600 text-sm mt-2 block">
            Back to dashboard
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Back nav */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-2xl mx-auto px-4 py-4">
          <Link to="/dashboard" className="text-indigo-600 text-sm hover:underline">
            ← Back to Dashboard
          </Link>
        </div>
      </div>

      <main className="max-w-2xl mx-auto px-4 py-8 space-y-6">
        {/* Hero */}
        <div className="bg-white rounded-xl overflow-hidden shadow-sm">
          {artist.image_url ? (
            <img src={artist.image_url} alt={artist.name} className="w-full h-56 object-cover" />
          ) : (
            <div className="w-full h-56 bg-gradient-to-br from-indigo-100 to-purple-100 flex items-center justify-center">
              <span className="text-6xl text-indigo-300">♪</span>
            </div>
          )}
          <div className="p-6">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">{artist.name}</h1>
                {artist.popularity !== null && (
                  <p className="text-sm text-gray-500 mt-1">
                    Spotify popularity: {artist.popularity}/100
                  </p>
                )}
              </div>
              <button
                onClick={() => toggle(artist.id)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors min-h-[44px] whitespace-nowrap ${
                  isSaved(artist.id)
                    ? "bg-indigo-600 text-white hover:bg-indigo-700"
                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                }`}
              >
                {isSaved(artist.id) ? "Saved ✓" : "Save to Schedule"}
              </button>
            </div>

            <div className="mt-3 flex flex-wrap gap-1">
              {artist.genres.map((g) => (
                <GenreTag key={g} genre={g} />
              ))}
            </div>

            {(artist.start_time || artist.stage) && (
              <div className="mt-4 p-3 bg-gray-50 rounded-lg flex flex-wrap gap-x-6 gap-y-2 text-sm">
                {artist.start_time && (() => {
                  const d = new Date(artist.start_time);
                  const adjusted = new Date(d.getTime() + (d.getHours() < 6 ? 86400000 : 0));
                  const fmt = (iso: string) => {
                    const t = new Date(iso);
                    return `${String(t.getHours()).padStart(2, "0")}:${String(t.getMinutes()).padStart(2, "0")}`;
                  };
                  return (
                    <>
                      <div>
                        <p className="text-xs text-gray-400 uppercase tracking-wide mb-0.5">Day</p>
                        <p className="font-medium text-gray-800">
                          {adjusted.toLocaleDateString("en-DK", { weekday: "long", day: "numeric", month: "long" })}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-400 uppercase tracking-wide mb-0.5">Time</p>
                        <p className="font-medium text-gray-800">
                          {fmt(artist.start_time)}{artist.end_time && ` – ${fmt(artist.end_time)}`}
                        </p>
                      </div>
                    </>
                  );
                })()}
                {artist.stage && (
                  <div>
                    <p className="text-xs text-gray-400 uppercase tracking-wide mb-0.5">Stage</p>
                    <p className="font-medium text-gray-800">{artist.stage}</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Spotify embed */}
        {artist.spotify_id && (
          <div className="bg-white rounded-xl p-4 shadow-sm">
            <h2 className="font-semibold text-gray-800 mb-3">Listen on Spotify</h2>
            <SpotifyEmbed spotifyId={artist.spotify_id} />
          </div>
        )}

        {/* Related artists */}
        {artist.related_artists.length > 0 && (
          <div className="bg-white rounded-xl p-6 shadow-sm">
            <h2 className="font-semibold text-gray-800 mb-3">Related Artists</h2>
            <div className="flex flex-wrap gap-2">
              {artist.related_artists.slice(0, 10).map((r) => (
                <span key={r.id} className="bg-gray-100 text-gray-700 px-3 py-1 rounded-full text-sm">
                  {r.name}
                </span>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
