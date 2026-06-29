"use client";

import { useEffect, useState } from "react";

// Flips the `.dark` class on <html> and persists to localStorage. A blocking
// inline script in the layout applies the stored theme before paint (no flash);
// this only handles the toggle + label. Label shows the theme you'd switch to.
export function ThemeToggle() {
  // {mounted, dark}: read once on mount from the class the no-flash script set.
  const [state, setState] = useState({ mounted: false, dark: false });
  const { mounted, dark } = state;

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- mount-time DOM read
    setState({ mounted: true, dark: document.documentElement.classList.contains("dark") });
  }, []);

  function toggle() {
    const next = !dark;
    setState({ mounted: true, dark: next });
    document.documentElement.classList.toggle("dark", next);
    try {
      localStorage.setItem("movein-theme", next ? "dark" : "light");
    } catch {
      /* private mode — ignore */
    }
  }

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label="Toggle colour theme"
      className="ml-auto inline-flex min-h-[34px] items-center gap-2 rounded-full border border-rule bg-card2 px-3.5 py-[7px] font-mono text-[11px] uppercase tracking-wider text-ink2 hover:text-ink"
      suppressHydrationWarning
    >
      {mounted ? (dark ? "Light" : "Dark") : "Dark"}
    </button>
  );
}
