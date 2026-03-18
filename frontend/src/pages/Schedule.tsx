import { Link } from "react-router-dom";
import { ScheduleTimeline } from "../components/ScheduleTimeline";
import { useRecommendations } from "../hooks/useRecommendations";
import { useSchedule } from "../hooks/useSchedule";

export function Schedule() {
  const { data } = useRecommendations();
  const { savedIds, toggle } = useSchedule();

  const savedArtists = (data?.results ?? []).filter((a) => savedIds.has(a.id));

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-2xl mx-auto px-4 py-4 flex items-center justify-between">
          <Link to="/dashboard" className="text-indigo-600 text-sm hover:underline">
            ← Dashboard
          </Link>
          <h1 className="font-bold text-gray-900">My Schedule</h1>
          <span className="text-sm text-gray-400">{savedArtists.length} artists</span>
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 py-8">
        <ScheduleTimeline artists={savedArtists} onRemove={toggle} />
      </main>
    </div>
  );
}
