import {
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import type { GenreScore } from "../types";

interface GenreRadarProps {
  genres: GenreScore[];
}

export function GenreRadar({ genres }: GenreRadarProps) {
  const top8 = genres.slice(0, 8).map((g) => ({
    genre: g.name.length > 16 ? g.name.slice(0, 16) + "…" : g.name,
    score: Math.round(g.score * 100),
  }));

  if (top8.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-gray-400 text-sm">
        No genre data yet
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <RadarChart data={top8}>
        <PolarGrid />
        <PolarAngleAxis dataKey="genre" tick={{ fontSize: 11 }} />
        <Radar
          name="Score"
          dataKey="score"
          stroke="#6366f1"
          fill="#6366f1"
          fillOpacity={0.4}
        />
        <Tooltip formatter={(value: number) => [`${value}%`, "Match"]} />
      </RadarChart>
    </ResponsiveContainer>
  );
}
