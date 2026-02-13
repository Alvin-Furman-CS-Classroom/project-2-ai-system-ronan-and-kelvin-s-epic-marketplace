import { Search } from "lucide-react";
import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";

interface Props {
  initialQuery?: string;
  compact?: boolean;
}

export default function SearchBar({ initialQuery = "", compact = false }: Props) {
  const [query, setQuery] = useState(initialQuery);
  const navigate = useNavigate();

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const params = new URLSearchParams();
    if (query.trim()) params.set("q", query.trim());
    navigate(`/search?${params.toString()}`);
  }

  return (
    <form
      onSubmit={handleSubmit}
      className={`relative flex items-center ${
        compact ? "w-full max-w-xl" : "w-full max-w-2xl"
      }`}
    >
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search for electronics, computers, and more..."
        className={`w-full rounded-full border border-[var(--color-border)] bg-white pl-5 pr-12 text-sm focus:border-[var(--color-brand)] focus:outline-none focus:ring-2 focus:ring-[var(--color-brand)]/20 ${
          compact ? "py-2" : "py-3"
        }`}
      />
      <button
        type="submit"
        className="absolute right-1 top-1/2 -translate-y-1/2 rounded-full bg-[var(--color-brand)] p-2 text-white transition hover:bg-[var(--color-brand-dark)]"
        aria-label="Search"
      >
        <Search size={compact ? 16 : 18} />
      </button>
    </form>
  );
}
