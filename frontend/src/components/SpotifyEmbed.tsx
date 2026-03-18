interface SpotifyEmbedProps {
  spotifyId: string;
}

export function SpotifyEmbed({ spotifyId }: SpotifyEmbedProps) {
  return (
    <iframe
      title="Spotify Player"
      src={`https://open.spotify.com/embed/artist/${spotifyId}?utm_source=generator`}
      width="100%"
      height="152"
      allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
      loading="lazy"
      className="rounded-xl"
    />
  );
}
