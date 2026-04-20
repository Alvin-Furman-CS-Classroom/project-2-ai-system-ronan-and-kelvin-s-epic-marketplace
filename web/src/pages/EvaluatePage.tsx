import { useEffect, useState } from "react";
import { Loader2, Target, CheckCircle2, XCircle, Play, Scale } from "lucide-react";
import { fetchCategories, fetchEvaluate } from "../api";
import type {
  Category,
  EvaluateResponse,
  EvaluateVariantResult,
  GroundTruthMode,
} from "../types";
import Navbar from "../components/Navbar";
import Footer from "../components/Footer";

const METRIC_KEYS = [
  { key: "precision_at_k", label: "P@k" },
  { key: "recall_at_k", label: "R@k" },
  { key: "f1_at_k", label: "F1@k" },
  { key: "ndcg_at_k", label: "NDCG@k" },
  { key: "reciprocal_rank", label: "MRR" },
  { key: "average_precision", label: "AP" },
] as const;

function MetricBadge({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-[var(--color-border)] bg-white px-3 py-2 text-center">
      <p className="text-[10px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
        {label}
      </p>
      <p className="text-lg font-bold text-[var(--color-text)]">
        {value.toFixed(3)}
      </p>
    </div>
  );
}

function queryTokens(q: string): string[] {
  return q
    .toLowerCase()
    .split(/\s+/)
    .map((t) => t.replace(/[^a-z0-9]/g, ""))
    .filter((t) => t.length >= 3);
}

function titleMatchesQuery(title: string, tokens: string[]): boolean {
  if (!tokens.length) return false;
  const t = title.toLowerCase();
  return tokens.some((tok) => t.includes(tok));
}

function RankedItemRow({
  item,
  tokens,
}: {
  item: EvaluateVariantResult["items"][number];
  tokens: string[];
}) {
  const { rank, product, score, relevant } = item;
  const isMatch = titleMatchesQuery(product.title, tokens);
  return (
    <div
      className={`flex items-center gap-3 rounded-lg border p-2.5 ${
        relevant
          ? "border-green-200 bg-green-50"
          : "border-[var(--color-border)] bg-white"
      }`}
    >
      <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-gray-100 text-xs font-bold text-gray-600">
        {rank}
      </span>
      <img
        src={
          product.image_url ||
          "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=80&h=80&fit=crop"
        }
        alt=""
        className="h-10 w-10 shrink-0 rounded object-contain bg-gray-50"
        loading="lazy"
      />
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium leading-tight">
          {product.title}
        </p>
        <p className="flex items-center gap-2 text-xs text-[var(--color-text-muted)]">
          <span>
            ${product.price.toFixed(2)} · {product.seller_rating.toFixed(1)}★
          </span>
          {isMatch ? (
            <span
              title="Product title contains a query keyword (semantic match)"
              className="rounded-full bg-blue-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-blue-700"
            >
              match
            </span>
          ) : (
            <span
              title="Product title does NOT contain the query — relevance here is review-driven only"
              className="rounded-full bg-gray-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-gray-500"
            >
              off-topic
            </span>
          )}
        </p>
      </div>
      <div className="shrink-0 text-right">
        <p className="text-xs font-semibold text-[var(--color-brand)]">
          {score.toFixed(3)}
        </p>
        {relevant ? (
          <CheckCircle2
            size={14}
            className="ml-auto mt-0.5 text-green-600"
          />
        ) : (
          <XCircle size={14} className="ml-auto mt-0.5 text-gray-300" />
        )}
      </div>
    </div>
  );
}

function VariantCard({
  variant,
  tokens,
}: {
  variant: EvaluateVariantResult;
  tokens: string[];
}) {
  const matchCount = variant.items.filter((it) =>
    titleMatchesQuery(it.product.title, tokens),
  ).length;
  const matchRate = variant.items.length
    ? matchCount / variant.items.length
    : 0;
  return (
    <div className="rounded-lg border border-[var(--color-border)] bg-white">
      <div className="border-b border-[var(--color-border)] bg-gray-50 px-4 py-3">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h3 className="text-sm font-bold text-[var(--color-text)]">
              {variant.label}
            </h3>
            <p className="text-xs text-[var(--color-text-muted)]">
              LTR: <b>{variant.use_ltr ? "on" : "off"}</b> · Query
              Understanding:{" "}
              <b>{variant.use_query_understanding ? "on" : "off"}</b>
            </p>
          </div>
          {tokens.length > 0 && (
            <div
              title="Share of top-k whose title actually contains a query keyword — semantic topicality, independent of review ratings."
              className={`shrink-0 rounded-md border px-2 py-1 text-center ${
                matchRate >= 0.7
                  ? "border-blue-200 bg-blue-50 text-blue-700"
                  : matchRate >= 0.3
                    ? "border-amber-200 bg-amber-50 text-amber-700"
                    : "border-gray-200 bg-gray-50 text-gray-500"
              }`}
            >
              <p className="text-[10px] font-semibold uppercase tracking-wider">
                On-topic
              </p>
              <p className="text-sm font-bold">
                {matchCount}/{variant.items.length}
              </p>
            </div>
          )}
        </div>
      </div>
      <div className="grid grid-cols-3 gap-2 p-3 sm:grid-cols-6">
        {METRIC_KEYS.map((m) => (
          <MetricBadge
            key={m.key}
            label={m.label}
            value={variant.metrics[m.key] ?? 0}
          />
        ))}
      </div>
      <div className="space-y-2 p-3 pt-0">
        {variant.items.map((item) => (
          <RankedItemRow
            key={`${item.product.id}-${item.rank}`}
            item={item}
            tokens={tokens}
          />
        ))}
        {variant.items.length === 0 && (
          <p className="py-6 text-center text-sm text-gray-400">
            No results returned for this variant.
          </p>
        )}
      </div>
    </div>
  );
}

export default function EvaluatePage() {
  const [query, setQuery] = useState("wireless headphones");
  const [category, setCategory] = useState("All Electronics");
  const [categories, setCategories] = useState<string[]>([]);
  const [k, setK] = useState(10);
  const [useLtr, setUseLtr] = useState(true);
  const [useQu, setUseQu] = useState(true);
  const [ratingThreshold, setRatingThreshold] = useState(4.0);
  const [groundTruth, setGroundTruth] = useState<GroundTruthMode>("hybrid");
  const [data, setData] = useState<EvaluateResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchCategories()
      .then((cats: Category[]) => setCategories(cats.map((c) => c.name)))
      .catch(console.error);
  }, []);

  async function runEvaluate(compare: boolean) {
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const response = await fetchEvaluate({
        q: query.trim(),
        category: category || undefined,
        k,
        use_ltr: useLtr,
        use_query_understanding: useQu,
        compare,
        rating_threshold: ratingThreshold,
        ground_truth: groundTruth,
      });
      setData(response);
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } }; message?: string };
      const detail =
        e?.response?.data?.detail ?? e?.message ?? "Evaluation failed";
      setError(String(detail));
      setData(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col bg-[var(--color-surface)]">
      <Navbar />

      <div className="mx-auto w-full max-w-6xl px-4 py-6">
        <div className="mb-4 flex items-center gap-2">
          <Target size={20} className="text-[var(--color-brand)]" />
          <h1 className="text-2xl font-bold text-[var(--color-text)]">
            Module 5 — Live Evaluation
          </h1>
        </div>
        <p className="mb-6 max-w-3xl text-sm text-[var(--color-text-muted)]">
          Run a query through the full pipeline and measure the ranking
          against ground-truth relevance. The <b>ground-truth</b> dropdown
          controls what "relevant" means: <i>reviews</i> counts any product
          with a review ≥ the threshold (quality only — intentionally loose,
          to show how review ratings saturate the metric), while <i>hybrid</i>
          also requires the product's title/description to actually contain
          a query keyword (quality AND topicality — the honest metric). Flip
          the toggles to run an ablation, and watch how the LTR + Query
          Understanding variant wins under hybrid ground truth.
        </p>

        {/* Controls */}
        <div className="mb-5 rounded-lg border border-[var(--color-border)] bg-white p-4">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
            <div className="md:col-span-2">
              <label className="mb-1 block text-xs font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
                Query
              </label>
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") runEvaluate(false);
                }}
                className="w-full rounded-md border border-[var(--color-border)] bg-white px-3 py-2 text-sm"
                placeholder="e.g. wireless headphones"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
                Category
              </label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full rounded-md border border-[var(--color-border)] bg-white px-3 py-2 text-sm"
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
                Top-k
              </label>
              <select
                value={k}
                onChange={(e) => setK(Number(e.target.value))}
                className="w-full rounded-md border border-[var(--color-border)] bg-white px-3 py-2 text-sm"
              >
                {[5, 10, 15, 20].map((v) => (
                  <option key={v} value={v}>
                    {v}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
            <div>
              <label className="mb-1 block text-xs font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
                Ground truth
              </label>
              <select
                value={groundTruth}
                onChange={(e) =>
                  setGroundTruth(e.target.value as GroundTruthMode)
                }
                className="w-full rounded-md border border-[var(--color-border)] bg-white px-3 py-2 text-sm"
              >
                <option value="hybrid">
                  hybrid — rating ≥ threshold AND on-topic (recommended)
                </option>
                <option value="reviews">
                  reviews — rating ≥ threshold only (loose / saturated)
                </option>
              </select>
              <p className="mt-1 text-xs text-[var(--color-text-muted)]">
                <b>hybrid</b> is the honest metric — it rewards pipelines that
                return the right <i>topic</i>, not just any highly-rated item.
              </p>
            </div>
            <div>
              <label className="mb-1 block text-xs font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
                Rating threshold (≥ …)
              </label>
              <div className="flex items-center gap-3">
                <input
                  type="range"
                  min={3}
                  max={5}
                  step={0.5}
                  value={ratingThreshold}
                  onChange={(e) =>
                    setRatingThreshold(Number(e.target.value))
                  }
                  className="flex-1 accent-[var(--color-brand)]"
                />
                <span className="w-10 text-center text-sm font-bold">
                  {ratingThreshold.toFixed(1)}
                </span>
              </div>
              <p className="mt-1 text-xs text-[var(--color-text-muted)]">
                Higher = stricter quality bar. 5.0 only counts products with a
                perfect-review as relevant.
              </p>
            </div>
          </div>

          <div className="mt-4 flex flex-wrap items-center gap-4">
            <label className="flex cursor-pointer items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={useLtr}
                onChange={(e) => setUseLtr(e.target.checked)}
                className="h-4 w-4 accent-[var(--color-brand)]"
              />
              Use LTR (Module 4)
            </label>
            <label className="flex cursor-pointer items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={useQu}
                onChange={(e) => setUseQu(e.target.checked)}
                className="h-4 w-4 accent-[var(--color-brand)]"
              />
              Use Query Understanding (Module 3)
            </label>

            <div className="ml-auto flex gap-2">
              <button
                onClick={() => runEvaluate(false)}
                disabled={loading || !query.trim()}
                className="inline-flex items-center gap-2 rounded-md bg-[var(--color-brand)] px-4 py-2 text-sm font-semibold text-white shadow-sm disabled:opacity-50"
              >
                {loading ? (
                  <Loader2 size={14} className="animate-spin" />
                ) : (
                  <Play size={14} />
                )}
                Run evaluation
              </button>
              <button
                onClick={() => runEvaluate(true)}
                disabled={loading || !query.trim()}
                title="Run all 4 ablation variants and compare side by side"
                className="inline-flex items-center gap-2 rounded-md border border-[var(--color-brand)] px-4 py-2 text-sm font-semibold text-[var(--color-brand)] hover:bg-red-50 disabled:opacity-50"
              >
                <Scale size={14} />
                Compare all variants
              </button>
            </div>
          </div>
        </div>

        {error && (
          <div className="mb-4 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {data && !error && (
          <>
            <div className="mb-4 flex flex-wrap items-center gap-4 rounded-lg border border-[var(--color-border)] bg-white px-4 py-3 text-xs text-[var(--color-text-muted)]">
              <span>
                Query:{" "}
                <b className="text-[var(--color-text)]">"{data.query}"</b>
              </span>
              <span>
                Ground truth:{" "}
                <b
                  className={
                    data.ground_truth === "hybrid"
                      ? "text-green-700"
                      : "text-amber-700"
                  }
                >
                  {data.ground_truth}
                </b>
                {data.ground_truth === "hybrid"
                  ? " (rating ≥ threshold AND on-topic)"
                  : " (rating ≥ threshold only)"}
              </span>
              <span>
                Candidate pool:{" "}
                <b className="text-[var(--color-text)]">
                  {data.candidate_pool_size.toLocaleString()}
                </b>
              </span>
              <span>
                Relevant in pool:{" "}
                <b className="text-[var(--color-text)]">
                  {data.relevant_count.toLocaleString()}
                </b>
              </span>
              <span>
                k = <b className="text-[var(--color-text)]">{data.k}</b>
              </span>
            </div>

            {data.variants.length > 1 && (
              <div className="mb-6 overflow-hidden rounded-lg border border-[var(--color-border)] bg-white">
                <div className="bg-gray-50 px-4 py-2 text-sm font-bold">
                  Ablation comparison
                </div>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-[var(--color-border)] text-left text-xs uppercase tracking-wider text-[var(--color-text-muted)]">
                      <th className="px-3 py-2">Variant</th>
                      {METRIC_KEYS.map((m) => (
                        <th key={m.key} className="px-3 py-2">
                          {m.label}
                        </th>
                      ))}
                      <th
                        className="px-3 py-2"
                        title="Share of top-k whose title actually contains a query keyword."
                      >
                        On-topic
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.variants.map((v) => {
                      const toks = queryTokens(data.query);
                      const mc = v.items.filter((it) =>
                        titleMatchesQuery(it.product.title, toks),
                      ).length;
                      return (
                        <tr
                          key={v.label}
                          className="border-b border-[var(--color-border)] last:border-0"
                        >
                          <td className="px-3 py-2 font-medium">{v.label}</td>
                          {METRIC_KEYS.map((m) => (
                            <td key={m.key} className="px-3 py-2">
                              {(v.metrics[m.key] ?? 0).toFixed(3)}
                            </td>
                          ))}
                          <td className="px-3 py-2 font-semibold">
                            {mc}/{v.items.length}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}

            <div
              className={`grid gap-4 ${
                data.variants.length === 1
                  ? "grid-cols-1"
                  : "grid-cols-1 md:grid-cols-2"
              }`}
            >
              {data.variants.map((v) => (
                <VariantCard
                  key={v.label}
                  variant={v}
                  tokens={queryTokens(data.query)}
                />
              ))}
            </div>
          </>
        )}

        {loading && !data && (
          <div className="flex items-center justify-center py-24">
            <Loader2 className="h-8 w-8 animate-spin text-[var(--color-brand)]" />
          </div>
        )}
      </div>

      <Footer />
    </div>
  );
}
