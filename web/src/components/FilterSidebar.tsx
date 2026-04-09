import { GraduationCap } from "lucide-react";
import type { SearchParams } from "../types";

interface Props {
  filters: SearchParams;
  onChange: (filters: SearchParams) => void;
  categories: string[];
}

const SORT_OPTIONS = [
  { value: "", label: "Relevance" },
  { value: "price_asc", label: "Price: Low to High" },
  { value: "price_desc", label: "Price: High to Low" },
  { value: "rating_desc", label: "Rating: High to Low" },
  { value: "rating_asc", label: "Rating: Low to High" },
];

const RATING_OPTIONS = [
  { value: 0, label: "Any Rating" },
  { value: 4, label: "4★ & Up" },
  { value: 3, label: "3★ & Up" },
  { value: 2, label: "2★ & Up" },
];

const STRATEGY_OPTIONS = [
  { value: "linear", label: "Linear Scan" },
  { value: "bfs", label: "BFS" },
  { value: "dfs", label: "DFS" },
  { value: "priority", label: "Priority (A*)" },
];

export default function FilterSidebar({ filters, onChange, categories }: Props) {
  function update(patch: Partial<SearchParams>) {
    onChange({ ...filters, ...patch });
  }

  return (
    <aside className="w-full space-y-6">
      {/* Category */}
      <div>
        <h4 className="mb-2 text-sm font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
          Category
        </h4>
        <select
          value={filters.category || ""}
          onChange={(e) => update({ category: e.target.value || undefined })}
          className="w-full rounded-md border border-[var(--color-border)] bg-white px-3 py-2 text-sm"
        >
          <option value="">All Categories</option>
          {categories.map((cat) => (
            <option key={cat} value={cat}>
              {cat}
            </option>
          ))}
        </select>
      </div>

      {/* Price Range */}
      <div>
        <h4 className="mb-2 text-sm font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
          Price Range
        </h4>
        <div className="flex items-center gap-2">
          <input
            type="number"
            min={0}
            step={1}
            placeholder="Min"
            value={filters.price_min ?? ""}
            onChange={(e) =>
              update({
                price_min: e.target.value ? Number(e.target.value) : undefined,
              })
            }
            className="w-full rounded-md border border-[var(--color-border)] px-3 py-2 text-sm"
          />
          <span className="text-[var(--color-text-muted)]">–</span>
          <input
            type="number"
            min={0}
            step={1}
            placeholder="Max"
            value={filters.price_max ?? ""}
            onChange={(e) =>
              update({
                price_max: e.target.value ? Number(e.target.value) : undefined,
              })
            }
            className="w-full rounded-md border border-[var(--color-border)] px-3 py-2 text-sm"
          />
        </div>
      </div>

      {/* Rating */}
      <div>
        <h4 className="mb-2 text-sm font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
          Rating
        </h4>
        <div className="space-y-1">
          {RATING_OPTIONS.map((opt) => (
            <label key={opt.value} className="flex items-center gap-2 text-sm cursor-pointer">
              <input
                type="radio"
                name="rating"
                checked={(filters.min_rating ?? 0) === opt.value}
                onChange={() =>
                  update({ min_rating: opt.value || undefined })
                }
                className="accent-[var(--color-brand)]"
              />
              {opt.label}
            </label>
          ))}
        </div>
      </div>

      {/* Sort */}
      <div>
        <h4 className="mb-2 text-sm font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
          Sort By
        </h4>
        <select
          value={filters.sort_by || ""}
          onChange={(e) => update({ sort_by: e.target.value || undefined })}
          className="w-full rounded-md border border-[var(--color-border)] bg-white px-3 py-2 text-sm"
        >
          {SORT_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      {/* Search Strategy (special — shows off Module 1) */}
      <div>
        <h4 className="mb-2 text-sm font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
          Search Strategy
        </h4>
        <select
          value={filters.strategy || "linear"}
          onChange={(e) => update({ strategy: e.target.value })}
          className="w-full rounded-md border border-[var(--color-border)] bg-white px-3 py-2 text-sm"
        >
          {STRATEGY_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        <p className="mt-1 text-xs text-[var(--color-text-muted)]">
          Module 1: Compare different search algorithms
        </p>
      </div>

      {/* Module 4 — learning-to-rank (matches /api/search use_ltr) */}
      <div>
        <h4 className="mb-2 text-sm font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
          Module 4 LTR
        </h4>
        <label className="flex cursor-pointer items-start gap-2.5 rounded-md border border-[var(--color-border)] bg-white p-3 text-sm text-[var(--color-text)] shadow-sm transition hover:bg-gray-50/80">
          <input
            type="checkbox"
            className="mt-0.5 h-4 w-4 shrink-0 rounded border-gray-300 text-[var(--color-brand)] focus:ring-[var(--color-brand)]"
            checked={filters.use_ltr !== false}
            onChange={(e) => update({ use_ltr: e.target.checked })}
          />
          <span className="min-w-0">
            <span className="flex items-center gap-1.5 font-medium">
              <GraduationCap className="h-4 w-4 shrink-0 text-[var(--color-brand)]" aria-hidden />
              Ranking model
            </span>
            <span className="mt-0.5 block text-xs font-normal leading-snug text-[var(--color-text-muted)]">
              When on, results are re-ordered with learning-to-rank after NLP. Turn off to compare the
              baseline order.
            </span>
          </span>
        </label>
      </div>

      {/* Clear */}
      <button
        onClick={() =>
          onChange({ strategy: "linear" })
        }
        className="w-full rounded-md border border-[var(--color-border)] bg-white px-3 py-2 text-sm font-medium text-[var(--color-text-muted)] transition hover:bg-gray-50"
      >
        Clear All Filters
      </button>
    </aside>
  );
}
