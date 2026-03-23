/* ------------------------------------------------------------------ */
/* API client — talks to the FastAPI backend                           */
/* ------------------------------------------------------------------ */

import axios from "axios";
import type { Category, Product, SearchParams, SearchResponse, DealsResponse, DealInfo, RerankParams, RerankResponse, QueryUnderstandResponse } from "./types";

const api = axios.create({ baseURL: "/api" });

/** Healthcheck */
export async function fetchHealth(): Promise<{ status: string; products: number }> {
  const { data } = await api.get("/health");
  return data;
}

/** List all categories with counts */
export async function fetchCategories(): Promise<Category[]> {
  const { data } = await api.get<Category[]>("/categories");
  return data;
}

/** Search for products */
export async function searchProducts(params: SearchParams): Promise<SearchResponse> {
  // Strip undefined keys so they don't appear as "undefined" in the URL
  const clean: Record<string, string | number> = {};
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== "") {
      clean[k] = v;
    }
  }
  const { data } = await api.get<SearchResponse>("/search", { params: clean });
  return data;
}

/** Get a single product */
export async function fetchProduct(id: string): Promise<Product> {
  const { data } = await api.get<Product>(`/products/${id}`);
  return data;
}

/** List products with pagination */
export async function fetchProducts(limit = 20, offset = 0): Promise<Product[]> {
  const { data } = await api.get<Product[]>("/products", {
    params: { limit, offset },
  });
  return data;
}

/** Fetch top deals, optionally filtered by category */
export async function fetchDeals(category?: string, limit = 20): Promise<DealsResponse> {
  const params: Record<string, string | number> = { limit };
  if (category) params.category = category;
  const { data } = await api.get<DealsResponse>("/deals", { params });
  return data;
}

/** Re-rank search results using Module 2 heuristic strategies */
export async function fetchRerank(params: RerankParams): Promise<RerankResponse> {
  const clean: Record<string, string | number> = {};
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== "") {
      clean[k] = v;
    }
  }
  const { data } = await api.get<RerankResponse>("/rerank", { params: clean });
  return data;
}

/** Fetch deal info for a single product (returns null if not a deal) */
export async function fetchProductDeal(productId: string): Promise<DealInfo | null> {
  try {
    const { data } = await api.get<DealInfo>(`/products/${productId}/deal`);
    return data;
  } catch {
    return null;
  }
}

/** Module 3: analyze a query and return NLP pipeline results */
export async function fetchQueryUnderstand(q: string): Promise<QueryUnderstandResponse> {
  const { data } = await api.get<QueryUnderstandResponse>("/query-understand", {
    params: { q },
  });
  return data;
}
