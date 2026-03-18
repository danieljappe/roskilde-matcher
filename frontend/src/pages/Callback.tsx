import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { api } from "../api/client";

export function Callback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const called = useRef(false);

  useEffect(() => {
    if (called.current) return;
    called.current = true;

    const code = searchParams.get("code");
    const state = searchParams.get("state");
    const error = searchParams.get("error");

    if (error || !code || !state) {
      navigate(`/?error=${error ?? "missing_code"}`, { replace: true });
      return;
    }

    api
      .handleCallback(code, state)
      .then(() => {
        queryClient.invalidateQueries({ queryKey: ["auth", "me"] });
        navigate("/dashboard", { replace: true });
      })
      .catch(() => navigate("/?error=callback_failed", { replace: true }));
  }, [searchParams, navigate, queryClient]);

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center">
      <div className="text-center text-white">
        <div className="w-10 h-10 border-2 border-green-400 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <p className="text-gray-300">Connecting to Spotify…</p>
      </div>
    </div>
  );
}
