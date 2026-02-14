interface Props {
  label: string;
  variant: "bestseller" | "top-rated" | "new" | "deal";
}

const VARIANT_STYLES: Record<Props["variant"], string> = {
  bestseller: "bg-[var(--color-badge-best)] text-white",
  "top-rated": "bg-[var(--color-badge-top)] text-white",
  new: "bg-purple-600 text-white",
  deal: "bg-orange-500 text-white",
};

export default function Badge({ label, variant }: Props) {
  return (
    <span
      className={`inline-block rounded-sm px-2 py-0.5 text-xs font-semibold uppercase tracking-wide ${VARIANT_STYLES[variant]}`}
    >
      {label}
    </span>
  );
}
