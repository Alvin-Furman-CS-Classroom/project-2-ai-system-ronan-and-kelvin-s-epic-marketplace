import { useCallback, useSyncExternalStore } from "react";
import type { Product } from "../types";

const STORAGE_KEY = "epic_recently_viewed";
const MAX_ITEMS = 10;

type Listener = () => void;
const listeners = new Set<Listener>();

let cachedRaw: string | null = null;
let cachedItems: Product[] = [];

function emitChange() {
  cachedRaw = null;
  listeners.forEach((l) => l());
}

function getSnapshot(): Product[] {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (raw === cachedRaw) return cachedItems;
  cachedRaw = raw;
  try {
    cachedItems = raw ? JSON.parse(raw) : [];
  } catch {
    cachedItems = [];
  }
  return cachedItems;
}

function subscribe(listener: Listener) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

/**
 * Stores and retrieves the last 10 viewed products from localStorage.
 * Uses useSyncExternalStore so every component that calls this hook
 * re-renders instantly when a new product is viewed.
 */
export function useRecentlyViewed() {
  const items = useSyncExternalStore(subscribe, getSnapshot);

  const addProduct = useCallback((product: Product) => {
    const current = getSnapshot();
    const filtered = current.filter((p) => p.id !== product.id);
    const next = [product, ...filtered].slice(0, MAX_ITEMS);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
    emitChange();
  }, []);

  return { items, addProduct };
}
