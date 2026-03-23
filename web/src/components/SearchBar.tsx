import { Search, Tag, Package } from "lucide-react";
import { useEffect, useState, useRef, type FormEvent } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { fetchAutocomplete } from "../api";
import type { AutocompleteSuggestion } from "../types";

interface Props {
  initialQuery?: string;
  compact?: boolean;
}

const DEBOUNCE_MS = 200;

export default function SearchBar({ initialQuery = "", compact = false }: Props) {
  const [query, setQuery] = useState(initialQuery);
  const [suggestions, setSuggestions] = useState<AutocompleteSuggestion[]>([]);
  const [open, setOpen] = useState(false);
  const [activeIdx, setActiveIdx] = useState(-1);
  const navigate = useNavigate();
  const location = useLocation();
  const wrapperRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>();

  useEffect(() => {
    setQuery(initialQuery);
  }, [initialQuery]);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  // Debounced fetch
  useEffect(() => {
    const trimmed = query.trim();
    if (trimmed.length < 2) {
      setSuggestions([]);
      setOpen(false);
      return;
    }

    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      fetchAutocomplete(trimmed)
        .then((res) => {
          setSuggestions(res.suggestions);
          setOpen(res.suggestions.length > 0);
          setActiveIdx(-1);
        })
        .catch(() => {
          setSuggestions([]);
          setOpen(false);
        });
    }, DEBOUNCE_MS);

    return () => clearTimeout(debounceRef.current);
  }, [query]);

  function doSearch(q: string) {
    setOpen(false);
    const params = new URLSearchParams();
    if (q.trim()) params.set("q", q.trim());
    const target = `/search?${params.toString()}`;
    if (location.pathname === "/search") {
      navigate(target, { replace: true });
    } else {
      navigate(target);
    }
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    doSearch(query);
  }

  function handleSelect(s: AutocompleteSuggestion) {
    if (s.type === "category") {
      setOpen(false);
      navigate(`/search?category=${encodeURIComponent(s.text)}`);
    } else if (s.id) {
      setOpen(false);
      navigate(`/product/${s.id}`);
    } else {
      setQuery(s.text);
      doSearch(s.text);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (!open || suggestions.length === 0) return;

    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIdx((prev) => (prev < suggestions.length - 1 ? prev + 1 : 0));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIdx((prev) => (prev > 0 ? prev - 1 : suggestions.length - 1));
    } else if (e.key === "Enter" && activeIdx >= 0) {
      e.preventDefault();
      handleSelect(suggestions[activeIdx]);
    } else if (e.key === "Escape") {
      setOpen(false);
    }
  }

  return (
    <div ref={wrapperRef} className={`relative ${compact ? "w-full max-w-xl" : "w-full max-w-2xl"}`}>
      <form onSubmit={handleSubmit} className="relative flex items-center">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => suggestions.length > 0 && setOpen(true)}
          onKeyDown={handleKeyDown}
          placeholder="Search for electronics, computers, and more..."
          className={`w-full rounded-full border border-[var(--color-border)] bg-white pl-5 pr-12 text-sm text-gray-900 caret-gray-900 placeholder:text-gray-400 focus:border-[var(--color-brand)] focus:outline-none focus:ring-2 focus:ring-[var(--color-brand)]/20 ${
            compact ? "py-2" : "py-3"
          }`}
          role="combobox"
          aria-expanded={open}
          aria-autocomplete="list"
        />
        <button
          type="submit"
          className="absolute right-1 top-1/2 -translate-y-1/2 rounded-full bg-[var(--color-brand)] p-2 text-white transition hover:bg-[var(--color-brand-dark)]"
          aria-label="Search"
        >
          <Search size={compact ? 16 : 18} />
        </button>
      </form>

      {/* Dropdown */}
      {open && suggestions.length > 0 && (
        <ul
          role="listbox"
          className="absolute left-0 right-0 top-full z-50 mt-1 max-h-72 overflow-y-auto rounded-xl border border-[var(--color-border)] bg-white py-1 text-gray-900 shadow-lg"
        >
          {suggestions.map((s, i) => (
            <li
              key={`${s.type}-${s.text}-${i}`}
              role="option"
              aria-selected={i === activeIdx}
              onMouseDown={() => handleSelect(s)}
              onMouseEnter={() => setActiveIdx(i)}
              className={`flex cursor-pointer items-center gap-3 px-4 py-2.5 text-sm transition-colors ${
                i === activeIdx ? "bg-[var(--color-brand-light)]" : "hover:bg-gray-50"
              }`}
            >
              {s.type === "category" ? (
                <Tag size={14} className="shrink-0 text-purple-500" />
              ) : (
                <Package size={14} className="shrink-0 text-gray-400" />
              )}
              <span className="flex-1 truncate">{s.text}</span>
              <span className="shrink-0 text-xs text-[var(--color-text-muted)]">
                {s.type === "category" ? "Category" : "Product"}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
