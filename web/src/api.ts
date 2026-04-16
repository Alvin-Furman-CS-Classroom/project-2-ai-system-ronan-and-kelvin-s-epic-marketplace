/* ------------------------------------------------------------------ */
/* API client — talks to the FastAPI backend                           */
/* ------------------------------------------------------------------ */

import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";
import type { Category, Product, SearchParams, SearchResponse, DealsResponse, DealInfo, RerankParams, RerankResponse, QueryUnderstandResponse, AutocompleteResponse, EvaluateParams, EvaluateResponse } from "./types";

const api = axios.create({ baseURL: "/api" });

/** FastAPI trains Word2Vec + LTR on startup (~30–90s); Vite proxy errors until then — retry GETs. */
const RETRYABLE_STATUS = new Set([502, 503, 504]);
const MAX_STARTUP_RETRIES = 25;
const RETRY_DELAY_MS = 2000;

type RetryConfig = InternalAxiosRequestConfig & { __retryCount?: number };

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const config = error.config as RetryConfig | undefined;
    if (!config || config.method?.toLowerCase() !== "get") {
      return Promise.reject(error);
    }
    const status = error.response?.status;
    const retryable =
      !error.response ||
      RETRYABLE_STATUS.has(status ?? 0) ||
      error.code === "ERR_NETWORK";
    if (!retryable) {
      return Promise.reject(error);
    }
    const count = config.__retryCount ?? 0;
    if (count >= MAX_STARTUP_RETRIES) {
      return Promise.reject(error);
    }
    config.__retryCount = count + 1;
    await new Promise((r) => setTimeout(r, RETRY_DELAY_MS));
    return api.request(config);
  },
);

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
  const clean: Record<string, string | number | boolean> = {};
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null || v === "") continue;
    if (k === "use_ltr" && v === true) continue;
    clean[k] = v as string | number | boolean;
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

/** Fetch products similar to the given product (embedding similarity) */
export async function fetchSimilarProducts(productId: string, limit = 8): Promise<Product[]> {
  const { data } = await api.get<Product[]>(`/products/${productId}/similar`, {
    params: { limit },
  });
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

/** Autocomplete suggestions for the search bar */
export async function fetchAutocomplete(q: string): Promise<AutocompleteResponse> {
  const { data } = await api.get<AutocompleteResponse>("/autocomplete", {
    params: { q },
  });
  return data;
}

/** Module 3: analyze a query and return NLP pipeline results */
export async function fetchQueryUnderstand(q: string): Promise<QueryUnderstandResponse> {
  const { data } = await api.get<QueryUnderstandResponse>("/query-understand", {
    params: { q },
  });
  return data;
}

/** Module 5: run evaluation against review-derived ground truth */
export async function fetchEvaluate(params: EvaluateParams): Promise<EvaluateResponse> {
  const clean: Record<string, string | number | boolean> = {};
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null || v === "") continue;
    clean[k] = v as string | number | boolean;
  }
  const { data } = await api.get<EvaluateResponse>("/evaluate", {
    params: clean,
    timeout: 60000,
  });
  return data;
}
