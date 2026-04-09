import type { SearchMetadata } from "../types";

interface Props {
  metadata: SearchMetadata;
}

export default function SearchMeta({ metadata }: Props) {
  const start = (metadata.page - 1) * metadata.page_size + 1;
  const end = Math.min(start + metadata.count - 1, metadata.total);

  return (
    <div className="flex flex-wrap items-center gap-3 rounded-md bg-gray-100 px-4 py-2 text-xs text-[var(--color-text-muted)]">
      <span>
        Showing{" "}
        <strong className="text-[var(--color-text)]">
          {metadata.total > 0 ? `${start}–${end}` : "0"}
        </strong>{" "}
        of{" "}
        <strong className="text-[var(--color-text)]">
          {metadata.total.toLocaleString()}
        </strong>{" "}
        results
      </span>
      <span className="text-gray-300">|</span>
      <span>
        Strategy:{" "}
        <strong className="text-[var(--color-text)]">{metadata.strategy}</strong>
      </span>
      <span className="text-gray-300">|</span>
      <span>
        Scanned:{" "}
        <strong className="text-[var(--color-text)]">
          {metadata.total_scanned.toLocaleString()}
        </strong>
      </span>
      <span className="text-gray-300">|</span>
      <span>
        Time:{" "}
        <strong className="text-[var(--color-text)]">
          {metadata.elapsed_ms.toFixed(2)}ms
        </strong>
      </span>
      {(metadata.module4_ltr_requested !== undefined ||
        metadata.module4_trained_model) && (
        <>
          <span className="text-gray-300">|</span>
          <span>
            Module 4 LTR:{" "}
            <strong
              className={
                metadata.module4_ltr_applied
                  ? "text-emerald-700"
                  : "text-[var(--color-text)]"
              }
            >
              {metadata.module4_ltr_applied
                ? "applied to order"
                : metadata.module4_ltr_requested === false
                  ? "disabled (baseline order)"
                  : "not applied (no text query or model unavailable)"}
            </strong>
            {metadata.module4_trained_model && (
              <span className="ml-1 text-[var(--color-text-muted)]">
                ({metadata.module4_trained_model}
                {metadata.module4_training_cv_roc_auc != null &&
                metadata.module4_training_cv_roc_auc !== undefined
                  ? ` · CV ROC AUC ${metadata.module4_training_cv_roc_auc.toFixed(3)}`
                  : ""}
                )
              </span>
            )}
          </span>
        </>
      )}
    </div>
  );
}
