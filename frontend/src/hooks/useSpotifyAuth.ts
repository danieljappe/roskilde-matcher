import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import type { AuthUser } from "../types";

export function useSpotifyAuth() {
  const { data: user, isLoading, error } = useQuery<AuthUser, Error>({
    queryKey: ["auth", "me"],
    queryFn: api.getMe,
    retry: false,
    staleTime: 5 * 60 * 1000,
  });

  return {
    user: user ?? null,
    isAuthenticated: !!user && !error,
    isLoading,
  };
}
