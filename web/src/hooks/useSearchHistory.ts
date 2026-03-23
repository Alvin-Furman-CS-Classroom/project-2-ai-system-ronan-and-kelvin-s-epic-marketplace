import { useCallback, useSyncExternalStore } from "react";

const STORAGE_KEY = "epic_search_history";
const MAX_ITEMS = 8;

type Listener = () => void;
const listeners = new Set<Listener>();

let cachedRaw: string | null = null;
let cachedItems: string[] = [];

function emitChange() {
  cachedRaw = null;
  listeners.forEach((l) => l());
}

function getSnapshot(): string[] {
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
 * Stores and retrieves the last 8 search queries from localStorage.
 * Same pattern as useRecentlyViewed — cached snapshot to avoid
 * infinite re-render loops.
 */
export function useSearchHistory() {
  const history = useSyncExternalStore(subscribe, getSnapshot);

  const addQuery = useCallback((query: string) => {
    const trimmed = query.trim().toLowerCase();
    if (!trimmed) return;
    const current = getSnapshot();
    const filtered = current.filter((q) => q !== trimmed);
    const next = [trimmed, ...filtered].slice(0, MAX_ITEMS);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
    emitChange();
  }, []);

  const removeQuery = useCallback((query: string) => {
    const current = getSnapshot();
    const next = current.filter((q) => q !== query);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
    emitChange();
  }, []);

  const clearHistory = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    emitChange();
  }, []);

  return { history, addQuery, removeQuery, clearHistory };
}
