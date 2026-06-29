/**
 * themeStore.ts — light/dark theme with persistence.
 *
 * Tailwind is configured with darkMode: "class", and index.css defines the
 * `.dark` CSS-variable palette, so toggling the `dark` class on <html> switches
 * the entire app. Preference is saved to localStorage and falls back to the
 * OS setting on first visit.
 */
import { create } from "zustand";

export type Theme = "light" | "dark";

function initialTheme(): Theme {
  if (typeof window === "undefined") return "light";
  const saved = localStorage.getItem("theme");
  if (saved === "light" || saved === "dark") return saved;
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function applyTheme(theme: Theme) {
  if (typeof document === "undefined") return;
  document.documentElement.classList.toggle("dark", theme === "dark");
  localStorage.setItem("theme", theme);
}

interface ThemeState {
  theme: Theme;
  setTheme: (t: Theme) => void;
  toggle: () => void;
}

export const useThemeStore = create<ThemeState>((set, get) => ({
  theme: initialTheme(),
  setTheme: (t) => { applyTheme(t); set({ theme: t }); },
  toggle: () => {
    const next: Theme = get().theme === "dark" ? "light" : "dark";
    applyTheme(next);
    set({ theme: next });
  },
}));

// Apply the persisted/OS theme immediately on first import (before render)
applyTheme(useThemeStore.getState().theme);
