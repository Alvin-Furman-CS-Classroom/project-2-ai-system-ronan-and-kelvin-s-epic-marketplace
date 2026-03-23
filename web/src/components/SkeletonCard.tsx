export default function SkeletonCard() {
  return (
    <div className="flex flex-col rounded-lg bg-white shadow-sm border border-[var(--color-border)] overflow-hidden animate-pulse">
      {/* Image placeholder */}
      <div className="aspect-square bg-gray-200" />

      {/* Info placeholder */}
      <div className="flex flex-1 flex-col gap-2 p-3">
        <div className="h-3 w-16 rounded bg-gray-200" />
        <div className="h-4 w-full rounded bg-gray-200" />
        <div className="h-4 w-3/4 rounded bg-gray-200" />

        <div className="mt-auto pt-2 space-y-1.5">
          <div className="h-5 w-20 rounded bg-gray-200" />
          <div className="h-3 w-24 rounded bg-gray-200" />
        </div>
      </div>
    </div>
  );
}
