import { useEffect, useState } from "react";
import { Loader2, TrendingUp, Search, ArrowUpDown } from "lucide-react";
import { fetchCategories, searchProducts, fetchRerank } from "../api";
import type { Category, Product, RerankItem } from "../types";
import Navbar from "../components/Navbar";
import Footer from "../components/Footer";

const SEARCH_STRATEGIES = [
  { value: "linear", label: "Linear Scan" },
  { value: "bfs", label: "BFS (Breadth-First)" },
  { value: "dfs", label: "DFS (Depth-First)" },
  { value: "priority", label: "Priority (A*)" },
];

const RERANK_STRATEGIES = [
  { value: "baseline", label: "Baseline (Sort by Score)" },
  { value: "hill_climbing", label: "Hill Climbing" },
  { value: "simulated_annealing", label: "Simulated Annealing" },
];

function MiniProductRow({
  product,
  rank,
  rankChange,
  score,
}: {
  product: Product;
  rank: number;
  rankChange?: number | null;
  score?: number | null;
}) {
  return (
    <div className="flex items-center gap-3 rounded-lg border border-[var(--color-border)] bg-white p-2.5 transition hover:shadow-sm">
      <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-gray-100 text-xs font-bold text-gray-600">
        {rank}
      </span>
      <img
        src={
          product.image_url ||
          "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=80&h=80&fit=crop"
        }
        alt=""
        className="h-12 w-12 shrink-0 rounded object-contain bg-gray-50"
        loading="lazy"
      />
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium leading-tight">
          {product.title}
        </p>
        <p className="text-xs text-[var(--color-text-muted)]">
          ${product.price.toFixed(2)} &middot; {product.seller_rating.toFixed(1)} stars
          {product.rating_number ? ` (${product.rating_number.toLocaleString()})` : ""}
        </p>
      </div>
      <div className="shrink-0 text-right">
        {score != null && (
          <p className="text-xs font-semibold text-[var(--color-brand)]">
            {score.toFixed(3)}
          </p>
        )}
        {rankChange != null && rankChange !== 0 && (
          <p
            className={`text-xs font-bold ${
              rankChange > 0 ? "text-green-600" : "text-red-500"
            }`}
          >
            {rankChange > 0 ? "\u2191" : "\u2193"}
            {Math.abs(rankChange)}
          </p>
        )}
      </div>
    </div>
  );
}

export default function RerankComparisonPage() {
  const [searchStrategy, setSearchStrategy] = useState("linear");
  const [rerankStrategy, setRerankStrategy] = useState("hill_climbing");
  const [category, setCategory] = useState("");
  const [categories, setCategories] = useState<string[]>([]);
  const [searchProducts_, setSearchProducts_] = useState<Product[]>([]);
  const [rerankItems, setRerankItems] = useState<RerankItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [rerankMeta, setRerankMeta] = useState<{
    iterations: number;
    objective_value: number;
    elapsed_ms: number;
  } | null>(null);

  useEffect(() => {
    fetchCategories()
      .then((cats: Category[]) => setCategories(cats.map((c) => c.name)))
      .catch(console.error);
  }, []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);

    const searchParams = {
      category: category || undefined,
      strategy: searchStrategy,
      page: 1,
      page_size: 12,
    };

    const rerankParams = {
      category: category || undefined,
      rerank_strategy: rerankStrategy,
      max_results: 12,
      k: 10,
    };

    Promise.all([searchProducts(searchParams), fetchRerank(rerankParams)])
      .then(([searchRes, rerankRes]) => {
        if (!cancelled) {
          setSearchProducts_(searchRes.products);
          setRerankItems(rerankRes.items);
          setRerankMeta(rerankRes.metadata);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          console.error(err);
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [searchStrategy, rerankStrategy, category]);

  const searchRankById = Object.fromEntries(
    searchProducts_.map((p, i) => [p.id, i + 1])
  );

  return (
    <div className="flex min-h-screen flex-col bg-[var(--color-surface)]">
      <Navbar />

      <div className="mx-auto w-full max-w-6xl px-4 py-6">
        <h1 className="mb-2 text-2xl font-bold text-[var(--color-text)]">
          Search vs Re-ranked Results
        </h1>
        <p className="mb-6 text-sm text-[var(--color-text-muted)]">
          See how Module 2 re-ranking reorders Module 1's raw search results.
          Change the strategies and category below to see the difference.
        </p>

        {/* Controls */}
        <div className="mb-6 flex flex-wrap items-end gap-4 rounded-lg border border-[var(--color-border)] bg-white p-4">
          <div>
            <label className="mb-1 block text-xs font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
              Category
            </label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="rounded-md border border-[var(--color-border)] bg-white px-3 py-2 text-sm"
            >
              <option value="">All Categories</option>
              {categories.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-xs font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
              Search Strategy (Module 1)
            </label>
            <select
              value={searchStrategy}
              onChange={(e) => setSearchStrategy(e.target.value)}
              className="rounded-md border border-[var(--color-border)] bg-white px-3 py-2 text-sm"
            >
              {SEARCH_STRATEGIES.map((s) => (
                <option key={s.value} value={s.value}>
                  {s.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-xs font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
              Re-rank Strategy (Module 2)
            </label>
            <select
              value={rerankStrategy}
              onChange={(e) => setRerankStrategy(e.target.value)}
              className="rounded-md border border-[var(--color-border)] bg-white px-3 py-2 text-sm"
            >
              {RERANK_STRATEGIES.map((s) => (
                <option key={s.value} value={s.value}>
                  {s.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-32">
            <Loader2 className="h-8 w-8 animate-spin text-[var(--color-brand)]" />
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            {/* Left: Raw search */}
            <div>
              <div className="mb-3 rounded-t-lg border-l-4 border-gray-400 bg-gray-50 px-4 py-3">
                <h2 className="flex items-center gap-2 text-base font-bold text-gray-700">
                  <Search size={16} />
                  Module 1 — Raw Search
                </h2>
                <p className="text-xs text-gray-500">
                  {searchProducts_.length} results &middot; strategy: {searchStrategy} &middot; no scoring or optimization
                </p>
              </div>
              <div className="space-y-2">
                {searchProducts_.map((product, i) => (
                  <MiniProductRow
                    key={product.id}
                    product={product}
                    rank={i + 1}
                  />
                ))}
                {searchProducts_.length === 0 && (
                  <p className="py-8 text-center text-sm text-gray-400">
                    No results
                  </p>
                )}
              </div>
            </div>

            {/* Right: Re-ranked */}
            <div>
              <div className="mb-3 rounded-t-lg border-l-4 border-[var(--color-brand)] bg-red-50 px-4 py-3">
                <h2 className="flex items-center gap-2 text-base font-bold text-[var(--color-brand)]">
                  <TrendingUp size={16} />
                  Module 2 — Re-ranked
                </h2>
                <p className="text-xs text-gray-500">
                  {rerankItems.length} results &middot; strategy: {rerankStrategy}
                  {rerankMeta && (
                    <>
                      {" "}&middot; NDCG: {rerankMeta.objective_value.toFixed(3)}
                      {" "}&middot; {rerankMeta.iterations} iters
                      {" "}&middot; {rerankMeta.elapsed_ms.toFixed(1)}ms
                    </>
                  )}
                </p>
              </div>
              <div className="space-y-2">
                {rerankItems.map((item) => {
                  const prevRank = searchRankById[item.product.id];
                  const rankChange =
                    prevRank != null ? prevRank - item.rank : null;
                  return (
                    <MiniProductRow
                      key={item.product.id}
                      product={item.product}
                      rank={item.rank}
                      rankChange={rankChange}
                      score={item.score}
                    />
                  );
                })}
                {rerankItems.length === 0 && (
                  <p className="py-8 text-center text-sm text-gray-400">
                    No results
                  </p>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      <Footer />
    </div>
  );
}
