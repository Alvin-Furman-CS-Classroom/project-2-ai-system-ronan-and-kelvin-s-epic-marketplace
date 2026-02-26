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

export interface SearchMetadata {
  strategy: string;
  total_scanned: number;
  elapsed_ms: number;
  count: number;
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
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
