import { Link } from "react-router-dom";
import type { Product } from "../types";
import StarRating from "./StarRating";
import Badge from "./Badge";

interface Props {
  product: Product;
}

/** Placeholder when product has no image */
const PLACEHOLDER =
  "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&h=400&fit=crop";

function getBadge(product: Product) {
  if (product.seller_rating >= 4.7)
    return <Badge label="Top Rated" variant="top-rated" />;
  if (product.rating_number && product.rating_number >= 5000)
    return <Badge label="Bestseller" variant="bestseller" />;
  return null;
}

export default function ProductCard({ product }: Props) {
  const badge = getBadge(product);

  return (
    <Link
      to={`/product/${product.id}`}
      className="group flex flex-col rounded-lg bg-white shadow-sm border border-[var(--color-border)] overflow-hidden transition hover:shadow-md"
    >
      {/* Image */}
      <div className="relative aspect-square bg-gray-50 overflow-hidden">
        <img
          src={product.image_url || PLACEHOLDER}
          alt={product.title}
          className="h-full w-full object-contain p-4 transition-transform group-hover:scale-105"
          loading="lazy"
        />
        {badge && (
          <div className="absolute top-2 left-2">{badge}</div>
        )}
      </div>

      {/* Info */}
      <div className="flex flex-1 flex-col gap-1 p-3">
        <p className="text-sm text-[var(--color-text-muted)] line-clamp-1">
          {product.store}
        </p>
        <h3 className="text-sm font-medium leading-snug line-clamp-2 group-hover:text-[var(--color-brand)]">
          {product.title}
        </h3>
        <div className="mt-auto pt-2">
          <p className="text-lg font-bold text-[var(--color-text)]">
            ${product.price.toFixed(2)}
          </p>
          <StarRating
            rating={product.seller_rating}
            size={14}
            count={product.rating_number}
          />
        </div>
      </div>
    </Link>
  );
}
