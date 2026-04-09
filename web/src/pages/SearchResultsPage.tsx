import { useEffect, useState, useCallback, useMemo, useRef } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { ChevronLeft, ChevronRight, Sparkles, Tag, Search, Clock, GraduationCap } from "lucide-react";
import { fetchCategories, searchProducts } from "../api";
import type { Category, Product, SearchMetadata, SearchParams, QueryUnderstandingInfo } from "../types";
import Navbar from "../components/Navbar";
import FilterSidebar from "../components/FilterSidebar";
import ProductCard from "../components/ProductCard";
import SkeletonCard from "../components/SkeletonCard";
import SearchMeta from "../components/SearchMeta";
import Footer from "../components/Footer";
import { useRecentlyViewed } from "../hooks/useRecentlyViewed";

const PAGE_SIZE = 24;

/** Build a compact page-number list with ellipses, e.g. [1, 2, '…', 9, 10] */
function pageRange(current: number, total: number): (number | "…")[] {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);
  const pages: (number | "…")[] = [];
  const addUnique = (n: number) => {
    if (n >= 1 && n <= total && !pages.includes(n)) pages.push(n);
  };
  addUnique(1);
  if (current > 3) pages.push("…");
  for (let i = current - 1; i <= current + 1; i++) addUnique(i);
  if (current < total - 2) pages.push("…");
  addUnique(total);
  return pages;
}

export default function SearchResultsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  // Derive filters directly from URL — no sync effect needed
  const filtersFromURL = useMemo((): SearchParams => ({
    q: searchParams.get("q") || undefined,
    category: searchParams.get("category") || undefined,
    price_min: searchParams.get("price_min")
      ? Number(searchParams.get("price_min"))
      : undefined,
    price_max: searchParams.get("price_max")
      ? Number(searchParams.get("price_max"))
      : undefined,
    min_rating: searchParams.get("min_rating")
      ? Number(searchParams.get("min_rating"))
      : undefined,
    store: searchParams.get("store") || undefined,
    sort_by: searchParams.get("sort_by") || undefined,
    strategy: searchParams.get("strategy") || "linear",
    page: searchParams.get("page") ? Number(searchParams.get("page")) : 1,
    page_size: PAGE_SIZE,
    use_ltr: searchParams.get("use_ltr") !== "0",
  }), [searchParams]);

  const [filters, setFilters] = useState<SearchParams>(filtersFromURL);
  const [products, setProducts] = useState<Product[]>([]);
  const [metadata, setMetadata] = useState<SearchMetadata | null>(null);
  const [categories, setCategories] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  // Load categories once
  useEffect(() => {
    fetchCategories()
      .then((cats: Category[]) => setCategories(cats.map((c) => c.name)))
      .catch(console.error);
  }, []);

  // Keep filters state in sync for the sidebar
  useEffect(() => {
    setFilters(filtersFromURL);
  }, [filtersFromURL]);

  // Fetch products whenever URL params change
  const fetchRef = useRef(0);
  useEffect(() => {
    const fetchId = ++fetchRef.current;
    setLoading(true);
    setProducts([]);
    setMetadata(null);

    searchProducts(filtersFromURL)
      .then((res) => {
        if (fetchId === fetchRef.current) {
          setProducts(res.products);
          setMetadata(res.metadata);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (fetchId === fetchRef.current) {
          console.error(err);
          setLoading(false);
        }
      });
  }, [filtersFromURL]);

  // Push filter changes to URL — filters are derived from searchParams
  const pushFilters = useCallback((next: SearchParams) => {
    setLoading(true);
    const params = new URLSearchParams();
    for (const [k, v] of Object.entries(next)) {
      if (v === undefined || v === null || v === "") continue;
      if (k === "use_ltr") {
        if (v === true) continue;
        params.set("use_ltr", "0");
        continue;
      }
      params.set(k, String(v));
    }
    if (params.get("page") === "1") params.delete("page");
    params.delete("page_size");
    setSearchParams(params, { replace: true });
  }, [setSearchParams]);

  function handleFilterChange(next: SearchParams) {
    pushFilters({ ...next, page: 1, page_size: PAGE_SIZE });
  }

  function goToPage(page: number) {
    pushFilters({ ...filtersFromURL, page, page_size: PAGE_SIZE });
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  const currentPage = filtersFromURL.page ?? 1;
  const totalPages = metadata?.total_pages ?? 1;
  const quInfo: QueryUnderstandingInfo | null | undefined =
    metadata?.query_understanding;
  const { items: recentlyViewed } = useRecentlyViewed();

  return (
    <div className="flex min-h-screen flex-col bg-[var(--color-surface)]">
      <Navbar query={filters.q} />

      <div className="mx-auto flex w-full max-w-7xl flex-1 gap-6 px-4 py-6">
        {/* Sidebar */}
        <div className="hidden w-60 shrink-0 md:block">
          <FilterSidebar
            filters={filters}
            onChange={handleFilterChange}
            categories={categories}
          />
        </div>

        {/* Main content */}
        <main className="flex-1">
          {/* Header */}
          <div className="mb-4">
            <h1 className="text-2xl font-bold text-[var(--color-text)]">
              {filters.q
                ? `Results for "${filters.q}"`
                : filters.category || "All Products"}
            </h1>
            {metadata && <div className="mt-2"><SearchMeta metadata={metadata} /></div>}
          </div>

          {/* Module 4 toggle: sidebar is hidden on small screens */}
          <div className="mb-4 md:hidden">
            <label className="flex cursor-pointer items-center gap-2 rounded-lg border border-[var(--color-border)] bg-white px-3 py-2.5 text-sm text-[var(--color-text)] shadow-sm">
              <input
                type="checkbox"
                className="h-4 w-4 rounded border-gray-300 text-[var(--color-brand)] focus:ring-[var(--color-brand)]"
                checked={filtersFromURL.use_ltr !== false}
                onChange={(e) =>
                  handleFilterChange({
                    ...filtersFromURL,
                    use_ltr: e.target.checked,
                  })
                }
              />
              <GraduationCap className="h-4 w-4 shrink-0 text-[var(--color-brand)]" aria-hidden />
              <span className="font-medium">Module 4 LTR ranking</span>
            </label>
          </div>

          {/* Module 3: "Did you mean?" spell correction */}
          {quInfo?.corrected_query && (
            <div className="mb-3 flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 px-4 py-2.5">
              <Search className="h-4 w-4 shrink-0 text-amber-600" />
              <span className="text-sm text-amber-800">
                Did you mean:{" "}
                <button
                  className="font-semibold text-amber-900 underline decoration-amber-400 underline-offset-2 hover:text-amber-700"
                  onClick={() => {
                    const params = new URLSearchParams(searchParams);
                    params.set("q", quInfo.corrected_query!);
                    navigate(`/search?${params.toString()}`, { replace: true });
                  }}
                >
                  {quInfo.corrected_query}
                </button>
                ?
              </span>
            </div>
          )}

          {/* Module 3: Query Understanding Chips */}
          {quInfo && (
            <div className="mb-4 flex flex-wrap items-center gap-2">
              {quInfo.inferred_category && (
                <span className="inline-flex items-center gap-1.5 rounded-full bg-purple-100 px-3 py-1 text-sm font-medium text-purple-800">
                  <Sparkles className="h-3.5 w-3.5" />
                  Category: {quInfo.inferred_category}
                  <span className="ml-0.5 text-xs text-purple-500">
                    {(quInfo.confidence * 100).toFixed(0)}%
                  </span>
                </span>
              )}
              {quInfo.keywords.slice(0, 5).map(([kw, score]) => (
                <span
                  key={kw}
                  className="inline-flex items-center gap-1 rounded-full bg-blue-50 px-2.5 py-1 text-xs font-medium text-blue-700"
                >
                  <Tag className="h-3 w-3" />
                  {kw}
                  {score > 0 && (
                    <span className="text-blue-400">
                      {score.toFixed(2)}
                    </span>
                  )}
                </span>
              ))}
            </div>
          )}

          {/* Product Grid */}
          {loading ? (
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {Array.from({ length: 12 }).map((_, i) => (
                <SkeletonCard key={i} />
              ))}
            </div>
          ) : products.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-32 text-center">
              <p className="text-lg font-medium text-[var(--color-text)]">
                No products found
              </p>
              <p className="mt-1 text-sm text-[var(--color-text-muted)]">
                Try adjusting your filters or search term.
              </p>
            </div>
          ) : (
            <>
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                {products.map((product) => (
                  <ProductCard key={product.id} product={product} />
                ))}
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <nav
                  aria-label="Pagination"
                  className="mt-8 flex items-center justify-center gap-1"
                >
                  <button
                    onClick={() => goToPage(currentPage - 1)}
                    disabled={currentPage <= 1}
                    className="flex h-9 w-9 items-center justify-center rounded-md border border-gray-300 text-sm disabled:cursor-not-allowed disabled:opacity-40 hover:bg-gray-100"
                    aria-label="Previous page"
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </button>

                  {pageRange(currentPage, totalPages).map((p, i) =>
                    p === "…" ? (
                      <span
                        key={`ellipsis-${i}`}
                        className="flex h-9 w-9 items-center justify-center text-sm text-gray-400"
                      >
                        …
                      </span>
                    ) : (
                      <button
                        key={p}
                        onClick={() => goToPage(p)}
                        className={`flex h-9 w-9 items-center justify-center rounded-md border text-sm font-medium transition-colors ${
                          p === currentPage
                            ? "border-[var(--color-brand)] bg-[var(--color-brand)] text-white"
                            : "border-gray-300 hover:bg-gray-100"
                        }`}
                        aria-label={`Page ${p}`}
                        aria-current={p === currentPage ? "page" : undefined}
                      >
                        {p}
                      </button>
                    )
                  )}

                  <button
                    onClick={() => goToPage(currentPage + 1)}
                    disabled={currentPage >= totalPages}
                    className="flex h-9 w-9 items-center justify-center rounded-md border border-gray-300 text-sm disabled:cursor-not-allowed disabled:opacity-40 hover:bg-gray-100"
                    aria-label="Next page"
                  >
                    <ChevronRight className="h-4 w-4" />
                  </button>
                </nav>
              )}
            </>
          )}
          {/* Recently Viewed */}
          {recentlyViewed.length > 0 && (
            <div className="mt-10 border-t border-[var(--color-border)] pt-6">
              <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-[var(--color-text-muted)]">
                <Clock className="h-4 w-4" />
                Recently Viewed
              </h3>
              <div className="flex gap-3 overflow-x-auto pb-2 scrollbar-thin">
                {recentlyViewed.slice(0, 6).map((product) => (
                  <div key={product.id} className="w-36 shrink-0">
                    <ProductCard product={product} />
                  </div>
                ))}
              </div>
            </div>
          )}
        </main>
      </div>

      <Footer />
    </div>
  );
}
