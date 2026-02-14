export default function Footer() {
  return (
    <footer className="border-t border-[var(--color-border)] bg-white mt-auto">
      <div className="mx-auto max-w-7xl px-4 py-8">
        <div className="grid grid-cols-1 gap-8 sm:grid-cols-3">
          {/* Brand */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[var(--color-brand)] text-white font-bold text-xs">
                EM
              </div>
              <span className="text-lg font-bold">Epic Marketplace</span>
            </div>
            <p className="text-sm text-[var(--color-text-muted)]">
              AI-powered product search — CSC-343 Spring 2026
            </p>
          </div>

          {/* AI Modules */}
          <div>
            <h4 className="mb-3 text-sm font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
              AI Modules
            </h4>
            <ul className="space-y-1 text-sm text-[var(--color-text-muted)]">
              <li>Module 1: Candidate Retrieval ✓</li>
              <li className="opacity-50">Module 2: Heuristic Re-ranking</li>
              <li className="opacity-50">Module 3: Query Understanding</li>
              <li className="opacity-50">Module 4: Learning-to-Rank</li>
              <li className="opacity-50">Module 5: Evaluation & Output</li>
            </ul>
          </div>

          {/* Data */}
          <div>
            <h4 className="mb-3 text-sm font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
              Data Source
            </h4>
            <p className="text-sm text-[var(--color-text-muted)]">
              Amazon Reviews &apos;23 — Electronics subset
            </p>
            <p className="mt-2 text-sm text-[var(--color-text-muted)]">
              Team: Kelvin Bonsu &amp; Ronan
            </p>
          </div>
        </div>

        <div className="mt-8 border-t border-[var(--color-border)] pt-4 text-center text-xs text-[var(--color-text-muted)]">
          © 2026 Epic Marketplace. Built for CSC-343 AI Systems.
        </div>
      </div>
    </footer>
  );
}
