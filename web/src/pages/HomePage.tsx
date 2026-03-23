import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Cpu,
  Smartphone,
  Headphones,
  MonitorSmartphone,
  Zap,
  TrendingUp,
  Flame,
  GitCompare,
  Clock,
} from "lucide-react";
import { fetchCategories, fetchProducts, fetchDeals } from "../api";
import type { Category, Product, DealProduct } from "../types";
import { useRecentlyViewed } from "../hooks/useRecentlyViewed";
import SearchBar from "../components/SearchBar";
import ProductCard from "../components/ProductCard";
import Footer from "../components/Footer";

/* ------------------------------------------------------------------ */
/* Hero category quick-links (map category names → icons)             */
/* ------------------------------------------------------------------ */
const CATEGORY_ICONS: Record<string, React.ReactNode> = {
  Computers: <Cpu size={28} />,
  "Cell Phones & Accessories": <Smartphone size={28} />,
  Electronics: <Headphones size={28} />,
  "Industrial & Scientific": <MonitorSmartphone size={28} />,
  "Arts, Crafts & Sewing": <Zap size={28} />,
};

export default function HomePage() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [trending, setTrending] = useState<Product[]>([]);
  const [deals, setDeals] = useState<DealProduct[]>([]);
  const { items: recentlyViewed } = useRecentlyViewed();

  useEffect(() => {
    fetchCategories().then(setCategories).catch(console.error);
    fetchProducts(12, 0).then(setTrending).catch(console.error);
    fetchDeals(undefined, 8).then((r) => setDeals(r.deals)).catch(console.error);
  }, []);

  return (
    <div className="flex min-h-screen flex-col">
      {/* ---- Hero ---- */}
      <section className="relative bg-gradient-to-br from-[var(--color-brand)] to-[var(--color-brand-dark)] text-white">
        <div className="mx-auto max-w-5xl px-4 py-16 text-center">
          {/* Logo */}
          <div className="mb-4 inline-flex h-16 w-16 items-center justify-center rounded-full bg-white/20 text-2xl font-bold">
            EM
          </div>
          <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl">
            Epic Marketplace
          </h1>
          <p className="mt-3 text-lg text-white/80">
            AI-powered search across thousands of electronics products
          </p>

          {/* Search bar */}
          <p className="mt-4">
            <Link
              to="/compare"
              className="inline-flex items-center gap-2 text-sm text-white/90 hover:text-white underline"
            >
              <GitCompare size={16} />
              Compare Search vs Re-ranked Results
            </Link>
          </p>
          <div className="mx-auto mt-8 max-w-2xl">
            <SearchBar />
          </div>
        </div>
      </section>

      {/* ---- Recently Viewed ---- */}
      {recentlyViewed.length > 0 && (
        <section className="mx-auto max-w-7xl px-4 pt-10">
          <h2 className="mb-6 text-xl font-bold flex items-center gap-2">
            <Clock size={20} className="text-[var(--color-brand)]" />
            Recently Viewed
          </h2>
          <div className="flex gap-4 overflow-x-auto pb-2 scrollbar-thin">
            {recentlyViewed.map((product) => (
              <div key={product.id} className="w-44 shrink-0">
                <ProductCard product={product} />
              </div>
            ))}
          </div>
        </section>
      )}

      {/* ---- Category Tiles ---- */}
      <section className="mx-auto max-w-7xl px-4 py-10">
        <h2 className="mb-6 text-xl font-bold flex items-center gap-2">
          <TrendingUp size={20} className="text-[var(--color-brand)]" />
          Browse Categories
        </h2>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-5">
          {categories.slice(0, 5).map((cat) => (
            <Link
              key={cat.name}
              to={`/search?category=${encodeURIComponent(cat.name)}`}
              className="flex flex-col items-center gap-2 rounded-xl border border-[var(--color-border)] bg-white p-5 text-center transition hover:shadow-md hover:border-[var(--color-brand)]/40"
            >
              <div className="flex h-14 w-14 items-center justify-center rounded-full bg-[var(--color-brand-light)] text-[var(--color-brand)]">
                {CATEGORY_ICONS[cat.name] || <Zap size={28} />}
              </div>
              <span className="text-sm font-medium">{cat.name}</span>
              <span className="text-xs text-[var(--color-text-muted)]">
                {cat.count.toLocaleString()} products
              </span>
            </Link>
          ))}
        </div>
      </section>

      {/* ---- Deals ---- */}
      {deals.length > 0 && (
        <section className="mx-auto max-w-7xl px-4 py-10">
          <div className="mb-6 flex items-center justify-between">
            <h2 className="text-xl font-bold flex items-center gap-2">
              <Flame size={20} className="text-orange-500" />
              Top Deals
            </h2>
          </div>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
            {deals.map((deal) => (
              <ProductCard
                key={deal.product.id}
                product={deal.product}
                dealType={deal.deal_type}
                priceVsAvg={deal.price_vs_avg}
              />
            ))}
          </div>
        </section>
      )}

      {/* ---- Trending Products ---- */}
      <section className="mx-auto max-w-7xl px-4 pb-16">
        <div className="mb-6 flex items-center justify-between">
          <h2 className="text-xl font-bold">Trending Products</h2>
          <Link
            to="/search"
            className="text-sm font-medium text-[var(--color-brand)] hover:underline"
          >
            View all →
          </Link>
        </div>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
          {trending.map((product) => (
            <ProductCard key={product.id} product={product} />
          ))}
        </div>
      </section>

      <Footer />
    </div>
  );
}
