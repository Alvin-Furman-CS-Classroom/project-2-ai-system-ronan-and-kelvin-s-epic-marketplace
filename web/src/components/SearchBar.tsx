import { Search, Tag, Package, Clock, TrendingUp, X } from "lucide-react";
import { useEffect, useState, useRef, type FormEvent } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { fetchAutocomplete } from "../api";
import { useSearchHistory } from "../hooks/useSearchHistory";
import type { AutocompleteSuggestion } from "../types";

interface Props {
  initialQuery?: string;
  compact?: boolean;
}

const DEBOUNCE_MS = 200;

const TRENDING_QUERIES = [
  "bluetooth headphones",
  "laptop stand",
  "usb-c cable",
  "wireless mouse",
  "phone charger",
];

type DropdownItem = {
  text: string;
  type: "history" | "trending" | "category" | "product";
  id?: string;
};

export default function SearchBar({ initialQuery = "", compact = false }: Props) {
  const [query, setQuery] = useState(initialQuery);
  const [suggestions, setSuggestions] = useState<AutocompleteSuggestion[]>([]);
  const [open, setOpen] = useState(false);
  const [activeIdx, setActiveIdx] = useState(-1);
  const navigate = useNavigate();
  const location = useLocation();
  const wrapperRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>();
  const { history, addQuery, removeQuery } = useSearchHistory();

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

  // Debounced autocomplete fetch
  useEffect(() => {
    const trimmed = query.trim();
    if (trimmed.length < 2) {
      setSuggestions([]);
      return;
    }

    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      fetchAutocomplete(trimmed)
        .then((res) => {
          setSuggestions(res.suggestions);
          setActiveIdx(-1);
        })
        .catch(() => setSuggestions([]));
    }, DEBOUNCE_MS);

    return () => clearTimeout(debounceRef.current);
  }, [query]);

  // Build the dropdown items based on what the user has typed
  const dropdownItems: DropdownItem[] = (() => {
    const trimmed = query.trim();

    // If user is typing, show autocomplete results
    if (trimmed.length >= 2 && suggestions.length > 0) {
      return suggestions.map((s) => ({
        text: s.text,
        type: s.type as "category" | "product",
        id: s.id,
      }));
    }

    // If input is empty/short, show history + trending
    if (trimmed.length < 2) {
      const items: DropdownItem[] = [];
      for (const q of history.slice(0, 5)) {
        items.push({ text: q, type: "history" });
      }
      for (const q of TRENDING_QUERIES) {
        if (!history.includes(q) && items.length < 8) {
          items.push({ text: q, type: "trending" });
        }
      }
      return items;
    }

    return [];
  })();

  function doSearch(q: string) {
    setOpen(false);
    const trimmed = q.trim();
    if (trimmed) addQuery(trimmed);
    const params = new URLSearchParams();
    if (trimmed) params.set("q", trimmed);
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

  function handleSelect(item: DropdownItem) {
    if (item.type === "category") {
      setOpen(false);
      addQuery(item.text);
      navigate(`/search?category=${encodeURIComponent(item.text)}`);
    } else if (item.type === "product" && item.id) {
      setOpen(false);
      navigate(`/product/${item.id}`);
    } else {
      setQuery(item.text);
      doSearch(item.text);
    }
  }

  function handleFocus() {
    if (dropdownItems.length > 0) setOpen(true);
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (!open || dropdownItems.length === 0) return;

    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIdx((prev) => (prev < dropdownItems.length - 1 ? prev + 1 : 0));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIdx((prev) => (prev > 0 ? prev - 1 : dropdownItems.length - 1));
    } else if (e.key === "Enter" && activeIdx >= 0) {
      e.preventDefault();
      handleSelect(dropdownItems[activeIdx]);
    } else if (e.key === "Escape") {
      setOpen(false);
    }
  }

  const iconForType = (type: DropdownItem["type"]) => {
    switch (type) {
      case "history":
        return <Clock size={14} className="shrink-0 text-gray-400" />;
      case "trending":
        return <TrendingUp size={14} className="shrink-0 text-orange-400" />;
      case "category":
        return <Tag size={14} className="shrink-0 text-purple-500" />;
      case "product":
        return <Package size={14} className="shrink-0 text-gray-400" />;
    }
  };

  const labelForType = (type: DropdownItem["type"]) => {
    switch (type) {
      case "history":
        return "Recent";
      case "trending":
        return "Trending";
      case "category":
        return "Category";
      case "product":
        return "Product";
    }
  };

  return (
    <div ref={wrapperRef} className={`relative ${compact ? "w-full max-w-xl" : "w-full max-w-2xl"}`}>
      <form onSubmit={handleSubmit} className="relative flex items-center">
        <input
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setOpen(true);
          }}
          onFocus={handleFocus}
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
      {open && dropdownItems.length > 0 && (
        <ul
          role="listbox"
          className="absolute left-0 right-0 top-full z-50 mt-1 max-h-80 overflow-y-auto rounded-xl border border-[var(--color-border)] bg-white py-1 text-gray-900 shadow-lg"
        >
          {dropdownItems.map((item, i) => (
            <li
              key={`${item.type}-${item.text}-${i}`}
              role="option"
              aria-selected={i === activeIdx}
              onMouseDown={() => handleSelect(item)}
              onMouseEnter={() => setActiveIdx(i)}
              className={`flex cursor-pointer items-center gap-3 px-4 py-2.5 text-sm transition-colors ${
                i === activeIdx ? "bg-[var(--color-brand-light)]" : "hover:bg-gray-50"
              }`}
            >
              {iconForType(item.type)}
              <span className="flex-1 truncate">{item.text}</span>
              <span className="shrink-0 text-xs text-[var(--color-text-muted)]">
                {labelForType(item.type)}
              </span>
              {item.type === "history" && (
                <button
                  onMouseDown={(e) => {
                    e.stopPropagation();
                    removeQuery(item.text);
                  }}
                  className="shrink-0 rounded p-0.5 text-gray-300 hover:text-gray-500"
                  aria-label={`Remove ${item.text} from history`}
                >
                  <X size={12} />
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
