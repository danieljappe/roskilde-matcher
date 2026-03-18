import { Link } from "react-router-dom";
import type { RecommendedArtist } from "../types";
import { GenreTag } from "./GenreTag";
import { ScoreBadge } from "./ScoreBadge";

interface ScheduleTimelineProps {
  artists: RecommendedArtist[];
  onRemove: (id: number) => void;
}

export function ScheduleTimeline({ artists, onRemove }: ScheduleTimelineProps) {
  if (artists.length === 0) {
    return (
      <div className="text-center py-16 text-gray-400">
        <p className="text-4xl mb-3">🎵</p>
        <p className="text-lg font-medium">Your schedule is empty</p>
        <p className="text-sm mt-1">Save artists from the dashboard to build your lineup</p>
      </div>
    );
  }

  const sorted = [...artists].sort((a, b) => a.name.localeCompare(b.name));

  return (
    <div className="space-y-3">
      {sorted.map((artist) => (
        <div
          key={artist.id}
          className="bg-white rounded-xl border border-gray-100 shadow-sm flex items-center gap-4 p-4"
        >
          {artist.image_url ? (
            <img
              src={artist.image_url}
              alt={artist.name}
              className="w-14 h-14 rounded-lg object-cover flex-shrink-0"
            />
          ) : (
            <div className="w-14 h-14 rounded-lg bg-indigo-50 flex items-center justify-center flex-shrink-0">
              <span className="text-2xl text-indigo-300">♪</span>
            </div>
          )}

          <div className="flex-1 min-w-0">
            <Link
              to={`/artists/${artist.id}`}
              className="font-semibold text-gray-900 hover:text-indigo-600 truncate block"
            >
              {artist.name}
            </Link>
            <div className="flex flex-wrap gap-1 mt-1">
              {artist.genres.slice(0, 2).map((g) => (
                <GenreTag key={g} genre={g} />
              ))}
            </div>
          </div>

          <ScoreBadge score={artist.composite_score} size="sm" />

          <button
            onClick={() => onRemove(artist.id)}
            className="text-gray-400 hover:text-red-500 transition-colors min-w-[44px] min-h-[44px] flex items-center justify-center"
            aria-label="Remove from schedule"
          >
            ×
          </button>
        </div>
      ))}
    </div>
  );
}
