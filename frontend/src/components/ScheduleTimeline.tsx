import { Link } from "react-router-dom";
import type { RecommendedArtist } from "../types";
import { ScoreBadge } from "./ScoreBadge";

interface ScheduleTimelineProps {
  artists: RecommendedArtist[];
  onRemove: (id: number) => void;
}

type ConflictLevel = "overlap" | "tight" | "close" | "none";


function formatTime(iso: string): string {
  const d = new Date(iso);
  return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
}

function getDayLabel(iso: string): string {
  return new Date(iso).toLocaleDateString("en-GB", { weekday: "long", day: "numeric", month: "long" });
}

function sortKey(iso: string): number {
  const d = new Date(iso);
  return d.getTime() + (d.getHours() < 6 ? 24 * 60 * 60 * 1000 : 0);
}

const MS_24H = 24 * 60 * 60 * 1000;

function adjustedMs(iso: string): number {
  const d = new Date(iso);
  return d.getTime() + (d.getHours() < 6 ? MS_24H : 0);
}

function getEffectiveEnd(artist: RecommendedArtist): number {
  if (artist.end_time) return adjustedMs(artist.end_time);
  return adjustedMs(artist.start_time!) + 60 * 60 * 1000;
}

function gapMinutes(a: RecommendedArtist, b: RecommendedArtist): number {
  const aStart = adjustedMs(a.start_time!);
  const aEnd = getEffectiveEnd(a);
  const bStart = adjustedMs(b.start_time!);
  const bEnd = getEffectiveEnd(b);
  return aStart < bStart
    ? (bStart - aEnd) / 60000
    : (aStart - bEnd) / 60000;
}

function conflictLevel(gap: number): ConflictLevel {
  if (gap < 0) return "overlap";   // actual overlap
  if (gap < 15) return "tight";    // ends as other starts
  if (gap <= 60) return "close";    // an hour
  return "none";
}

function buildConflictMap(artists: RecommendedArtist[]): Map<number, ConflictLevel> {
  const map = new Map<number, ConflictLevel>();
  const timed = artists.filter((a) => a.start_time);

  const severity: Record<ConflictLevel, number> = { overlap: 3, tight: 2, close: 1, none: 0 };
  for (const a of timed) {
    let worst: ConflictLevel = "none";
    for (const b of timed) {
      if (a.id === b.id) continue;
      const level = conflictLevel(gapMinutes(a, b));
      if (severity[level] > severity[worst]) worst = level;
      if (worst === "overlap") break;
    }
    if (worst !== "none") map.set(a.id, worst);
  }

  return map;
}

function formatGap(gap: number): string {
  if (gap < 0) return `${Math.round(-gap)} min overlap`;
  return `${Math.round(gap)} min gap`;
}
const CARD_STYLES: Record<ConflictLevel, string> = {
  overlap: "border-l-4 border-l-red-500 border border-red-200 bg-white",
  tight:   "border-l-4 border-l-orange-500 border border-orange-200 bg-white",
  close:   "border-l-4 border-l-yellow-400 border border-yellow-200 bg-white",
  none:    "border border-gray-100 bg-white",
};


interface ConnectorProps {
  gap: number;
  level: ConflictLevel;
}

const CONNECTOR_STYLES: Record<ConflictLevel, { border: string; bg: string; text: string } | null> = {
  overlap: { border: "border-red-300",    bg: "bg-red-50",    text: "text-red-500"    },
  tight:   { border: "border-orange-300", bg: "bg-orange-50", text: "text-orange-500" },
  close:   { border: "border-yellow-300", bg: "bg-yellow-50", text: "text-yellow-600" },
  none:    null,
};

function ConflictConnector({ gap, level }: ConnectorProps) {
  const s = CONNECTOR_STYLES[level];
  if (!s) return null;
  return (
    <div className="flex items-center gap-2 mx-4 my-1">
      <div className={`flex-1 border-t-2 border-dashed ${s.border}`} />
      <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${s.bg} ${s.text}`}>
        {formatGap(gap)}
      </span>
      <div className={`flex-1 border-t-2 border-dashed ${s.border}`} />
    </div>
  );
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

  const withTime = artists.filter((a) => a.start_time);
  const withoutTime = artists.filter((a) => !a.start_time);
  const conflictMap = buildConflictMap(artists);

  const sorted = [...withTime].sort((a, b) => sortKey(a.start_time!) - sortKey(b.start_time!));

  const dayGroups: { label: string; artists: RecommendedArtist[] }[] = [];
  for (const artist of sorted) {
    const label = getDayLabel(artist.start_time!);
    const existing = dayGroups.find((g) => g.label === label);
    if (existing) existing.artists.push(artist);
    else dayGroups.push({ label, artists: [artist] });
  }
  if (withoutTime.length > 0) {
    dayGroups.push({ label: "No date announced", artists: withoutTime });
  }

  return (
    <div className="space-y-8">
      {dayGroups.map(({ label, artists: group }) => (
        <div key={label}>
          <h2 className="text-sm font-bold text-gray-500 uppercase tracking-wide mb-3">{label}</h2>
          <div>
            {group.map((artist, idx) => {
              const level = conflictMap.get(artist.id) ?? "none";

              // Check if adjacent next artist conflicts directly with this one
              const next = group[idx + 1];
              let connectorProps: { gap: number; level: ConflictLevel } | null = null;
              if (next?.start_time && artist.start_time) {
                const gap = gapMinutes(artist, next);
                const cl = conflictLevel(gap);
                if (cl !== "none") connectorProps = { gap, level: cl };
              }

              return (
                <div key={artist.id}>
                  <div className={`rounded-xl shadow-sm flex items-center gap-4 p-4 ${CARD_STYLES[level]}`}>
                    {/* Time column */}
                    <div className="w-14 flex-shrink-0 text-center">
                      {artist.start_time ? (
                        <>
                          <p className="text-sm font-bold text-gray-900">{formatTime(artist.start_time)}</p>
                          {artist.end_time && (
                            <p className="text-xs text-gray-400">{formatTime(artist.end_time)}</p>
                          )}
                        </>
                      ) : (
                        <span className="text-xs text-gray-300">TBA</span>
                      )}
                    </div>

                    {/* Image */}
                    {artist.image_url ? (
                      <img
                        src={artist.image_url}
                        alt={artist.name}
                        className="w-12 h-12 rounded-lg object-cover flex-shrink-0"
                      />
                    ) : (
                      <div className="w-12 h-12 rounded-lg bg-indigo-50 flex items-center justify-center flex-shrink-0">
                        <span className="text-xl text-indigo-300">♪</span>
                      </div>
                    )}

                    {/* Name + stage + conflict details */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <Link
                          to={`/artists/${artist.id}`}
                          className="font-semibold text-gray-900 hover:text-indigo-600 truncate"
                        >
                          {artist.name}
                        </Link>
                        </div>
                      {artist.stage && (
                        <p className="text-xs text-gray-400 mt-0.5">{artist.stage}</p>
                      )}
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

                  {connectorProps && (
                    <ConflictConnector gap={connectorProps.gap} level={connectorProps.level} />
                  )}
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
