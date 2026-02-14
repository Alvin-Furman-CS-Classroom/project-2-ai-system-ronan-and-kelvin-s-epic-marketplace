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
