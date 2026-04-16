/* ------------------------------------------------------------------ */
/* Types matching the FastAPI response models                          */
/* ------------------------------------------------------------------ */

export interface Product {
  id: string;
  title: string;
  price: number;
  category: string;
  seller_rating: number;
  store: string;
  description: string | null;
  tags: string[] | null;
  image_url: string | null;
  rating_number: number | null;
  features: string[] | null;
}

/** Module 3 query understanding info attached to search results */
export interface QueryUnderstandingInfo {
  keywords: [string, number][];
  inferred_category: string | null;
  confidence: number;
  corrected_query: string | null;
}

export interface SearchMetadata {
  strategy: string;
  total_scanned: number;
  elapsed_ms: number;
  count: number;
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  query_understanding?: QueryUnderstandingInfo | null;
  /** User asked for Module 4 LTR on this request */
  module4_ltr_requested?: boolean;
  /** LTR re-rank actually ran (needs query + fitted model) */
  module4_ltr_applied?: boolean;
  module4_trained_model?: string | null;
  /** CV ROC AUC mean for selected model at API startup (if model selection ran) */
  module4_training_cv_roc_auc?: number | null;
}

export interface SearchResponse {
  products: Product[];
  metadata: SearchMetadata;
}

export interface Category {
  name: string;
  count: number;
}

/** Query-string parameters accepted by GET /api/search */
export interface SearchParams {
  q?: string;
  category?: string;
  price_min?: number;
  price_max?: number;
  min_rating?: number;
  store?: string;
  sort_by?: string;
  strategy?: string;
  page?: number;
  page_size?: number;
  /** false → skip Module 4 LTR (compare with baseline ordering) */
  use_ltr?: boolean;
}

export interface DealProduct {
  product: Product;
  deal_score: number;
  deal_type: "hidden_gem" | "great_value";
  price_vs_avg: number;
  rating_vs_avg: number;
  category_avg_price: number;
}

export interface DealsResponse {
  deals: DealProduct[];
  count: number;
}

export interface DealInfo {
  deal_score: number;
  deal_type: "hidden_gem" | "great_value";
  price_vs_avg: number;
  rating_vs_avg: number;
  category_avg_price: number;
}

/** Single item in a re-ranked result */
export interface RerankItem {
  product: Product;
  score: number;
  rank: number;
}

/** Metadata about the re-ranking pass */
export interface RerankMetadata {
  strategy: string;
  iterations: number;
  objective_value: number;
  elapsed_ms: number;
  count: number;
}

/** Response from GET /api/rerank */
export interface RerankResponse {
  items: RerankItem[];
  metadata: RerankMetadata;
}

/** Params for rerank API */
export interface RerankParams {
  category?: string;
  price_min?: number;
  price_max?: number;
  min_rating?: number;
  store?: string;
  rerank_strategy?: string;
  max_results?: number;
  k?: number;
}

/** Single autocomplete suggestion */
export interface AutocompleteSuggestion {
  text: string;
  type: "category" | "product";
  id?: string;
}

/** Response from GET /api/autocomplete */
export interface AutocompleteResponse {
  suggestions: AutocompleteSuggestion[];
}

/** Response from GET /api/query-understand */
export interface QueryUnderstandResponse {
  query: string;
  keywords: [string, number][];
  embedding_shape: number[];
  embedding_norm: number;
  inferred_category: string | null;
  confidence: number;
}

/** Params accepted by GET /api/evaluate */
export interface EvaluateParams {
  q: string;
  category?: string;
  k?: number;
  use_ltr?: boolean;
  use_query_understanding?: boolean;
  compare?: boolean;
  rating_threshold?: number;
}

/** One ranked item inside an evaluation variant */
export interface EvaluateRankedItem {
  rank: number;
  product: Product;
  score: number;
  relevant: boolean;
}

/** One ablation variant (use_ltr × use_query_understanding) */
export interface EvaluateVariantResult {
  label: string;
  use_ltr: boolean;
  use_query_understanding: boolean;
  metrics: {
    precision_at_k: number;
    recall_at_k: number;
    f1_at_k: number;
    ndcg_at_k: number;
    reciprocal_rank: number;
    average_precision: number;
    [key: string]: number;
  };
  items: EvaluateRankedItem[];
}

/** Response from GET /api/evaluate */
export interface EvaluateResponse {
  query: string;
  category: string | null;
  k: number;
  rating_threshold: number;
  candidate_pool_size: number;
  relevant_count: number;
  variants: EvaluateVariantResult[];
}
