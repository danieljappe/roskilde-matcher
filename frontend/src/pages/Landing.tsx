import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { useSpotifyAuth } from "../hooks/useSpotifyAuth";

export function Landing() {
  const { isAuthenticated, isLoading } = useSpotifyAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (isAuthenticated) {
      navigate("/dashboard", { replace: true });
    }
  }, [isAuthenticated, navigate]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <div className="max-w-4xl mx-auto px-4 py-20 flex flex-col items-center text-center">
        <div className="mb-6 text-6xl">🎪</div>
        <h1 className="text-4xl md:text-6xl font-bold mb-4 bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
          Roskilde Matcher
        </h1>
        <p className="text-lg md:text-xl text-gray-300 mb-3 max-w-2xl">
          100+ artists. 8 days. Who should you actually see?
        </p>
        <p className="text-gray-400 mb-10 max-w-lg">
          Connect your Spotify to get a personalised match score for every Roskilde Festival 2026 artist — based on your listening history.
        </p>

        <button
          onClick={() => {
            window.location.href = api.loginUrl;
          }}
          className="bg-green-500 hover:bg-green-400 text-black font-bold px-8 py-4 rounded-full text-lg transition-colors min-h-[44px]"
        >
          Connect with Spotify
        </button>

        <p className="mt-6 text-xs text-gray-500">
          We only request read-only access to your top artists. We never modify your Spotify data.
        </p>

        {/* Preview cards */}
        <div className="mt-16 grid grid-cols-1 sm:grid-cols-3 gap-4 w-full opacity-60">
          {["Must See", "Great Match", "Discover"].map((tier, i) => (
            <div key={tier} className="bg-gray-800 rounded-xl p-4 text-left">
              <div
                className={`inline-block w-3 h-3 rounded-full mb-2 ${
                  i === 0 ? "bg-green-500" : i === 1 ? "bg-blue-500" : "bg-yellow-500"
                }`}
              />
              <div className="font-semibold text-sm text-gray-200">{tier}</div>
              <div className="text-xs text-gray-400 mt-1">
                {i === 0
                  ? "Artists you already love"
                  : i === 1
                    ? "Strong genre overlap"
                    : "Hidden gems to explore"}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
