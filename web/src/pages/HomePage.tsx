import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Search,
  Cpu,
  Smartphone,
  Headphones,
  MonitorSmartphone,
  Zap,
  TrendingUp,
} from "lucide-react";
import { fetchCategories, fetchProducts } from "../api";
import type { Category, Product } from "../types";
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
  const [query, setQuery] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    fetchCategories().then(setCategories).catch(console.error);
    fetchProducts(12, 0).then(setTrending).catch(console.error);
  }, []);

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    const params = new URLSearchParams();
    if (query.trim()) params.set("q", query.trim());
    navigate(`/search?${params.toString()}`);
  }

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
          <form
            onSubmit={handleSearch}
            className="mx-auto mt-8 flex max-w-2xl items-center overflow-hidden rounded-full bg-white shadow-lg"
          >
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search for headphones, laptops, cables..."
              className="flex-1 bg-transparent px-6 py-3.5 text-sm text-[var(--color-text)] placeholder:text-gray-400 focus:outline-none"
            />
            <button
              type="submit"
              className="m-1.5 flex items-center gap-2 rounded-full bg-[var(--color-brand)] px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-[var(--color-brand-dark)]"
            >
              <Search size={16} />
              Search
            </button>
          </form>
        </div>
      </section>

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
