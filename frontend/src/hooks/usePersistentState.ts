import { useEffect, useState } from "react";

/**
 * Like useState, but mirrors the value into sessionStorage so a page's result
 * survives navigating away and back (within the browser session). Cleared on a
 * full refresh or when set to null/undefined. Drop-in replacement for useState.
 */
export function usePersistentState<T>(key: string, initial: T) {
  const storageKey = `acc:${key}`;
  const [value, setValue] = useState<T>(() => {
    try {
      const raw = sessionStorage.getItem(storageKey);
      return raw != null ? (JSON.parse(raw) as T) : initial;
    } catch {
      return initial;
    }
  });

  useEffect(() => {
    try {
      if (value === null || value === undefined) sessionStorage.removeItem(storageKey);
      else sessionStorage.setItem(storageKey, JSON.stringify(value));
    } catch {
      /* ignore quota / serialization errors */
    }
  }, [storageKey, value]);

  return [value, setValue] as const;
}
