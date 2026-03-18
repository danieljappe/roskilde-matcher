const GENRE_COLORS: Record<string, string> = {
  electronic: "bg-purple-100 text-purple-800",
  techno: "bg-purple-100 text-purple-800",
  house: "bg-purple-100 text-purple-800",
  dance: "bg-purple-100 text-purple-800",
  rock: "bg-red-100 text-red-800",
  metal: "bg-red-100 text-red-800",
  punk: "bg-red-100 text-red-800",
  indie: "bg-orange-100 text-orange-800",
  alternative: "bg-orange-100 text-orange-800",
  pop: "bg-pink-100 text-pink-800",
  hip: "bg-yellow-100 text-yellow-800",
  rap: "bg-yellow-100 text-yellow-800",
  jazz: "bg-teal-100 text-teal-800",
  soul: "bg-teal-100 text-teal-800",
  folk: "bg-green-100 text-green-800",
  country: "bg-green-100 text-green-800",
  classical: "bg-blue-100 text-blue-800",
};

function getGenreColor(genre: string): string {
  const lower = genre.toLowerCase();
  for (const [key, cls] of Object.entries(GENRE_COLORS)) {
    if (lower.includes(key)) return cls;
  }
  return "bg-gray-100 text-gray-700";
}

interface GenreTagProps {
  genre: string;
}

export function GenreTag({ genre }: GenreTagProps) {
  return (
    <span
      className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${getGenreColor(genre)}`}
    >
      {genre}
    </span>
  );
}
