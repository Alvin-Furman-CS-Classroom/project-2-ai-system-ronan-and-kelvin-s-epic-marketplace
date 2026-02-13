/* ------------------------------------------------------------------ */
/* API client — talks to the FastAPI backend                           */
/* ------------------------------------------------------------------ */

import axios from "axios";
import type { Category, Product, SearchParams, SearchResponse } from "./types";

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
