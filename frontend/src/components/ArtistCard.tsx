import { Link } from "react-router-dom";
import type { RecommendedArtist } from "../types";
import { GenreTag } from "./GenreTag";
import { ScoreBadge } from "./ScoreBadge";

function fmt(iso: string) {
  const d = new Date(iso);
  const day = d.toLocaleDateString("en-GB", { weekday: "short", day: "numeric", month: "short" });
  const time = `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
  return `${day} · ${time}`;
}

function formatSchedule(start_time: string | null, end_time: string | null, stage: string | null): string | null {
  const parts: string[] = [];
  if (start_time) {
    const endStr = end_time
      ? `–${String(new Date(end_time).getHours()).padStart(2, "0")}:${String(new Date(end_time).getMinutes()).padStart(2, "0")}`
      : "";
    parts.push(`${fmt(start_time)}${endStr}`);
  }
  if (stage) parts.push(stage);
  return parts.length ? parts.join(" · ") : null;
}

interface ArtistCardProps {
  artist: RecommendedArtist;
  isSaved: boolean;
  onToggleSave: (id: number) => void;
}

export function ArtistCard({ artist, isSaved, onToggleSave }: ArtistCardProps) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden flex flex-col">
      <Link to={`/artists/${artist.id}`} className="flex-1">
        {artist.image_url ? (
          <img
            src={artist.image_url}
            alt={artist.name}
            className="w-full h-40 object-cover"
          />
        ) : (
          <div className="w-full h-40 bg-gradient-to-br from-indigo-100 to-purple-100 flex items-center justify-center">
            <span className="text-4xl text-indigo-300">♪</span>
          </div>
        )}
        <div className="p-4">
          <div className="flex items-start justify-between gap-2">
            <h3 className="font-semibold text-gray-900 text-sm leading-snug">{artist.name}</h3>
            <ScoreBadge score={artist.composite_score} size="sm" />
          </div>
          <div className="mt-2 flex flex-wrap gap-1">
            {artist.genres.slice(0, 3).map((g) => (
              <GenreTag key={g} genre={g} />
            ))}
          </div>
          {formatSchedule(artist.start_time, artist.end_time, artist.stage) && (
            <p className="mt-2 text-xs text-gray-500 truncate">
              {formatSchedule(artist.start_time, artist.end_time, artist.stage)}
            </p>
          )}
        </div>
      </Link>

      <div className="px-4 pb-4">
        <button
          onClick={() => onToggleSave(artist.id)}
          className={`w-full py-2 rounded-lg text-sm font-medium transition-colors min-h-[44px] ${
            isSaved
              ? "bg-indigo-600 text-white hover:bg-indigo-700"
              : "bg-gray-100 text-gray-700 hover:bg-gray-200"
          }`}
        >
          {isSaved ? "Saved to Schedule" : "Save to Schedule"}
        </button>
      </div>
    </div>
  );
}
