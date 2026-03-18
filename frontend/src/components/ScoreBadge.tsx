interface ScoreBadgeProps {
  score: number; // 0–1
  size?: "sm" | "md" | "lg";
}

export function ScoreBadge({ score, size = "md" }: ScoreBadgeProps) {
  const pct = Math.round(score * 100);

  const color =
    pct >= 80
      ? "bg-green-500 text-white"
      : pct >= 60
        ? "bg-blue-500 text-white"
        : pct >= 40
          ? "bg-yellow-400 text-gray-900"
          : "bg-gray-300 text-gray-700";

  const sizeClass =
    size === "sm"
      ? "w-10 h-10 text-xs"
      : size === "lg"
        ? "w-16 h-16 text-lg font-bold"
        : "w-12 h-12 text-sm font-semibold";

  return (
    <div
      className={`rounded-full flex items-center justify-center flex-shrink-0 ${sizeClass} ${color}`}
      title={`Match score: ${pct}%`}
    >
      {pct}
    </div>
  );
}
