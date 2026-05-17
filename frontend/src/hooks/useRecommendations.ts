import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";
import type { RecommendationListResponse } from "../types";
import { useSpotifyAuth } from "./useSpotifyAuth";

export function useRecommendations(limit = 500) {
  const { isAuthenticated } = useSpotifyAuth();

  return useQuery<RecommendationListResponse, Error>({
    queryKey: ["recommendations", limit],
    queryFn: () => api.getRecommendations(limit),
    enabled: isAuthenticated,
    staleTime: 5 * 60 * 1000,
  });
}

export function useRefreshRecommendations() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: api.refreshRecommendations,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["recommendations"] });
    },
  });
}
