import { useEffect, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { ArrowLeft, Package, Store, Tag } from "lucide-react";
import { fetchProduct } from "../api";
import type { Product } from "../types";
import Navbar from "../components/Navbar";
import StarRating from "../components/StarRating";
import Badge from "../components/Badge";
import Footer from "../components/Footer";

const PLACEHOLDER =
  "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600&h=600&fit=crop";

export default function ProductDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [product, setProduct] = useState<Product | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    fetchProduct(id)
      .then(setProduct)
      .catch(() => setError("Product not found"));
  }, [id]);

  if (error) {
    return (
      <div className="flex min-h-screen flex-col">
        <Navbar />
        <div className="flex flex-1 items-center justify-center">
          <div className="text-center">
            <p className="text-lg font-medium">{error}</p>
            <Link
              to="/"
              className="mt-4 inline-block text-sm text-[var(--color-brand)] hover:underline"
            >
              ← Back to home
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (!product) {
    return (
      <div className="flex min-h-screen flex-col">
        <Navbar />
        <div className="flex flex-1 items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-[var(--color-brand)] border-t-transparent" />
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col bg-[var(--color-surface)]">
      <Navbar />

      <div className="mx-auto w-full max-w-6xl px-4 py-8">
        {/* Breadcrumb */}
        <button
          onClick={() => navigate(-1)}
          className="mb-6 inline-flex items-center gap-1 text-sm text-[var(--color-text-muted)] hover:text-[var(--color-brand)] cursor-pointer"
        >
          <ArrowLeft size={14} />
          Back to results
        </button>

        <div className="grid gap-10 md:grid-cols-2">
          {/* Image */}
          <div className="flex items-center justify-center rounded-xl bg-white p-8 border border-[var(--color-border)]">
            <img
              src={product.image_url || PLACEHOLDER}
              alt={product.title}
              className="max-h-96 object-contain"
            />
          </div>

          {/* Details */}
          <div className="flex flex-col gap-4">
            {/* Badges */}
            <div className="flex gap-2">
              {product.seller_rating >= 4.7 && (
                <Badge label="Top Rated" variant="top-rated" />
              )}
              {product.rating_number && product.rating_number >= 5000 && (
                <Badge label="Bestseller" variant="bestseller" />
              )}
            </div>

            <h1 className="text-2xl font-bold leading-tight text-[var(--color-text)]">
              {product.title}
            </h1>

            <StarRating
              rating={product.seller_rating}
              showValue
              count={product.rating_number}
              size={20}
            />

            <p className="text-3xl font-bold text-[var(--color-text)]">
              ${product.price.toFixed(2)}
            </p>

            {/* Meta */}
            <div className="flex flex-wrap gap-4 text-sm text-[var(--color-text-muted)]">
              <span className="flex items-center gap-1">
                <Store size={14} /> {product.store}
              </span>
              <span className="flex items-center gap-1">
                <Package size={14} /> {product.category}
              </span>
            </div>

            {/* Description */}
            {product.description && (
              <div className="mt-2">
                <h3 className="text-sm font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
                  About this item
                </h3>
                <p className="mt-1 text-sm leading-relaxed text-[var(--color-text)]">
                  {product.description}
                </p>
              </div>
            )}

            {/* Features */}
            {product.features && product.features.length > 0 && (
              <div className="mt-2">
                <h3 className="text-sm font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
                  Features
                </h3>
                <ul className="mt-2 space-y-1">
                  {product.features.slice(0, 5).map((feat, i) => (
                    <li
                      key={i}
                      className="flex items-start gap-2 text-sm text-[var(--color-text)]"
                    >
                      <span className="mt-1 text-[var(--color-brand)]">•</span>
                      {feat}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Tags */}
            {product.tags && product.tags.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-2">
                {product.tags.map((tag) => (
                  <Link
                    key={tag}
                    to={`/search?q=${encodeURIComponent(tag)}`}
                    className="inline-flex items-center gap-1 rounded-full bg-gray-100 px-3 py-1 text-xs text-[var(--color-text-muted)] hover:bg-gray-200"
                  >
                    <Tag size={10} />
                    {tag}
                  </Link>
                ))}
              </div>
            )}

            {/* CTA */}
            <button className="mt-4 w-full rounded-full bg-[var(--color-brand)] py-3 text-sm font-semibold text-white transition hover:bg-[var(--color-brand-dark)]">
              Add to Cart
            </button>
          </div>
        </div>
      </div>

      <Footer />
    </div>
  );
}
