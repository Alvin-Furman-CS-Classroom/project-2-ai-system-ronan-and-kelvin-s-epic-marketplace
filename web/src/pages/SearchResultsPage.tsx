import { useEffect, useState, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import { Loader2, ChevronLeft, ChevronRight } from "lucide-react";
import { fetchCategories, searchProducts } from "../api";
import type { Category, Product, SearchMetadata, SearchParams } from "../types";
import Navbar from "../components/Navbar";
import FilterSidebar from "../components/FilterSidebar";
import ProductCard from "../components/ProductCard";
import SearchMeta from "../components/SearchMeta";
import Footer from "../components/Footer";

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

  // Derive filters + page from URL
  const filtersFromURL = useCallback((): SearchParams => ({
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

  // Sync filters → URL
  useEffect(() => {
    const params = new URLSearchParams();
    for (const [k, v] of Object.entries(filters)) {
      if (v !== undefined && v !== null && v !== "") {
        params.set(k, String(v));
      }
    }
    // Remove page=1 from URL to keep it clean
    if (params.get("page") === "1") params.delete("page");
    // Remove default page_size
    params.delete("page_size");
    setSearchParams(params, { replace: true });
  }, [filters, setSearchParams]);

  // Fetch products whenever URL params change
  useEffect(() => {
    let cancelled = false;
    const current = filtersFromURL();

    searchProducts(current)
      .then((res) => {
        if (!cancelled) {
          setProducts(res.products);
          setMetadata(res.metadata);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          console.error(err);
          setLoading(false);
        }
      });

    return () => { cancelled = true; };
  }, [searchParams, filtersFromURL]);

  // Update filters from sidebar — reset to page 1
  function handleFilterChange(next: SearchParams) {
    setLoading(true);
    setFilters({ ...next, page: 1, page_size: PAGE_SIZE });
  }

  // Navigate to a specific page
  function goToPage(page: number) {
    setLoading(true);
    setFilters((prev) => ({ ...prev, page, page_size: PAGE_SIZE }));
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  const currentPage = filters.page ?? 1;
  const totalPages = metadata?.total_pages ?? 1;
  const queryText = filters.q || filters.category || "All Products";

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
              {queryText}
            </h1>
            {metadata && <div className="mt-2"><SearchMeta metadata={metadata} /></div>}
          </div>

          {/* Product Grid */}
          {loading ? (
            <div className="flex items-center justify-center py-32">
              <Loader2 className="h-8 w-8 animate-spin text-[var(--color-brand)]" />
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
        </main>
      </div>

      <Footer />
    </div>
  );
}
