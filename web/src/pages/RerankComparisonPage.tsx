import { useEffect, useState, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import { Loader2, TrendingUp } from "lucide-react";
import { fetchCategories, searchProducts, fetchRerank } from "../api";
import type { Category, Product, SearchParams, RerankItem } from "../types";
import Navbar from "../components/Navbar";
import FilterSidebar from "../components/FilterSidebar";
import ProductCard from "../components/ProductCard";
import Footer from "../components/Footer";

const RERANK_STRATEGIES = [
  { value: "baseline", label: "Baseline (Heuristic Sort)" },
  { value: "hill_climbing", label: "Hill Climbing" },
  { value: "simulated_annealing", label: "Simulated Annealing" },
];

export default function RerankComparisonPage() {
  const [searchParams, setSearchParams] = useSearchParams();

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
    page: 1,
    page_size: 24,
  }), [searchParams]);

  const [filters, setFilters] = useState<SearchParams>(filtersFromURL);
  const [rerankStrategy, setRerankStrategy] = useState("hill_climbing");
  const [searchProductsList, setSearchProductsList] = useState<Product[]>([]);
  const [rerankItems, setRerankItems] = useState<RerankItem[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCategories()
      .then((cats: Category[]) => setCategories(cats.map((c) => c.name)))
      .catch(console.error);
  }, []);

  useEffect(() => {
    const params = new URLSearchParams();
    for (const [k, v] of Object.entries(filters)) {
      if (v !== undefined && v !== null && v !== "" && k !== "page" && k !== "page_size") {
        params.set(k, String(v));
      }
    }
    params.set("rerank_strategy", rerankStrategy);
    setSearchParams(params, { replace: true });
  }, [filters, rerankStrategy, setSearchParams]);

  useEffect(() => {
    let cancelled = false;
    const current = filtersFromURL();

    const searchParams = {
      category: current.category,
      price_min: current.price_min,
      price_max: current.price_max,
      min_rating: current.min_rating,
      store: current.store,
      page: 1,
      page_size: 24,
    };

    const rerankParams = {
      category: current.category,
      price_min: current.price_min,
      price_max: current.price_max,
      min_rating: current.min_rating,
      store: current.store,
      rerank_strategy: rerankStrategy,
      max_results: 24,
      k: 10,
    };

    Promise.all([
      searchProducts(searchParams),
      fetchRerank(rerankParams),
    ])
      .then(([searchRes, rerankRes]) => {
        if (!cancelled) {
          setSearchProductsList(searchRes.products);
          setRerankItems(rerankRes.items);
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
  }, [searchParams, rerankStrategy, filtersFromURL]);

  function handleFilterChange(next: SearchParams) {
    setLoading(true);
    setFilters({ ...next, page: 1, page_size: 24 });
  }

  const searchRankByProductId = Object.fromEntries(
    searchProductsList.map((p, i) => [p.id, i + 1])
  );

  return (
    <div className="flex min-h-screen flex-col bg-[var(--color-surface)]">
      <Navbar />

      <div className="mx-auto flex w-full max-w-7xl flex-1 gap-6 px-4 py-6">
        <div className="hidden w-60 shrink-0 md:block">
          <FilterSidebar
            filters={filters}
            onChange={handleFilterChange}
            categories={categories}
          />
          <div className="mt-6">
            <h4 className="mb-2 text-sm font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
              Re-rank Strategy
            </h4>
            <select
              value={rerankStrategy}
              onChange={(e) => {
                setLoading(true);
                setRerankStrategy(e.target.value);
              }}
              className="w-full rounded-md border border-[var(--color-border)] bg-white px-3 py-2 text-sm"
            >
              {RERANK_STRATEGIES.map((s) => (
                <option key={s.value} value={s.value}>
                  {s.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        <main className="flex-1">
          <h1 className="mb-4 text-2xl font-bold text-[var(--color-text)]">
            Search vs Re-ranked Results
          </h1>
          <p className="mb-6 text-sm text-[var(--color-text-muted)]">
            Compare Module 1 raw search results (left) with Module 2 heuristic re-ranking (right).
            Use the strategy dropdown to switch between baseline, hill climbing, and simulated annealing.
          </p>

          {loading ? (
            <div className="flex items-center justify-center py-32">
              <Loader2 className="h-8 w-8 animate-spin text-[var(--color-brand)]" />
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
              {/* Left: Module 1 raw results */}
              <div>
                <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold text-[var(--color-text)]">
                  Module 1 — Raw Search
                </h2>
                <p className="mb-4 text-xs text-[var(--color-text-muted)]">
                  {searchProductsList.length} results (filtered, no re-ranking)
                </p>
                <div className="grid grid-cols-2 gap-3 sm:grid-cols-2">
                  {searchProductsList.map((product, i) => (
                    <div key={product.id} className="relative">
                      <span className="absolute left-2 top-2 z-10 rounded bg-gray-800 px-1.5 py-0.5 text-xs font-medium text-white">
                        #{i + 1}
                      </span>
                      <ProductCard product={product} />
                    </div>
                  ))}
                </div>
              </div>

              {/* Right: Module 2 re-ranked results */}
              <div>
                <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold text-[var(--color-text)]">
                  <TrendingUp size={18} className="text-[var(--color-brand)]" />
                  Module 2 — Re-ranked
                </h2>
                <p className="mb-4 text-xs text-[var(--color-text-muted)]">
                  {rerankItems.length} results (strategy: {rerankStrategy})
                </p>
                <div className="grid grid-cols-2 gap-3 sm:grid-cols-2">
                  {rerankItems.map((item) => {
                    const prevRank = searchRankByProductId[item.product.id];
                    const rankChange = prevRank != null ? prevRank - item.rank : null;
                    return (
                      <div key={item.product.id} className="relative">
                        <span className="absolute left-2 top-2 z-10 flex items-center gap-1 rounded bg-[var(--color-brand)] px-1.5 py-0.5 text-xs font-medium text-white">
                          #{item.rank}
                          {rankChange != null && rankChange !== 0 && (
                            <span
                              className={
                                rankChange > 0
                                  ? "text-green-200"
                                  : "text-red-200"
                              }
                            >
                              ({rankChange > 0 ? "+" : ""}{rankChange})
                            </span>
                          )}
                        </span>
                        <ProductCard product={item.product} />
                        <p className="mt-1 text-xs text-[var(--color-text-muted)]">
                          Score: {item.score.toFixed(3)}
                        </p>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}
        </main>
      </div>

      <Footer />
    </div>
  );
}
