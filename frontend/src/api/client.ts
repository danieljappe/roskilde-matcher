import type {
  AuthUser,
  FestivalArtist,
  FestivalArtistDetail,
  GenreProfileResponse,
  RecommendationListResponse,
} from "../types";

const API_URL = import.meta.env.VITE_API_URL ?? "";

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    credentials: "include",
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail ?? response.statusText);
  }

  return response.json() as Promise<T>;
}

export const api = {
  getMe: () => apiFetch<AuthUser>("/auth/me"),

  logout: () =>
    apiFetch<{ status: string }>("/auth/logout", { method: "POST" }),

  getRecommendations: (limit = 100) =>
    apiFetch<RecommendationListResponse>(`/recommendations?limit=${limit}`),

  refreshRecommendations: () =>
    apiFetch<RecommendationListResponse>("/recommendations/refresh", { method: "POST" }),

  getGenreProfile: () => apiFetch<GenreProfileResponse>("/recommendations/genres"),

  syncProfile: () =>
    apiFetch<{ status: string }>("/recommendations/sync", { method: "POST" }),

  getArtists: (limit = 50, offset = 0) =>
    apiFetch<FestivalArtist[]>(`/artists?limit=${limit}&offset=${offset}`),

  getArtist: (id: number) => apiFetch<FestivalArtistDetail>(`/artists/${id}`),

  searchArtists: (q: string) =>
    apiFetch<FestivalArtist[]>(`/artists/search?q=${encodeURIComponent(q)}`),

  handleCallback: (code: string, state: string) =>
    apiFetch<{ status: string }>("/auth/callback", {
      method: "POST",
      body: JSON.stringify({ code, state }),
    }),

  loginUrl: `${API_URL}/auth/login`,
};
