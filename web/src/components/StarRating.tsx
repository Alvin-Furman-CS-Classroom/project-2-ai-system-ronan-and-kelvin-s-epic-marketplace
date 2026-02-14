import { Star } from "lucide-react";

interface Props {
  rating: number;   // 0–5 (can be fractional)
  max?: number;
  size?: number;
  showValue?: boolean;
  count?: number | null;
}

export default function StarRating({
  rating,
  max = 5,
  size = 16,
  showValue = false,
  count = null,
}: Props) {
  const stars = Array.from({ length: max }, (_, i) => {
    const fill = Math.min(1, Math.max(0, rating - i));
    return fill >= 0.75 ? "full" : fill >= 0.25 ? "half" : "empty";
  });

  return (
    <span className="inline-flex items-center gap-0.5">
      {stars.map((type, i) => (
        <Star
          key={i}
          size={size}
          className={
            type === "full"
              ? "text-[var(--color-star)] fill-[var(--color-star)]"
              : type === "half"
              ? "text-[var(--color-star)] fill-[var(--color-star)] opacity-50"
              : "text-gray-300"
          }
        />
      ))}
      {showValue && (
        <span className="ml-1 text-sm text-[var(--color-text-muted)]">
          {rating.toFixed(1)}
        </span>
      )}
      {count !== null && count !== undefined && (
        <span className="ml-1 text-xs text-[var(--color-text-muted)]">
          ({count.toLocaleString()})
        </span>
      )}
    </span>
  );
}
