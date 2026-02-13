import { Link } from "react-router-dom";
import { ShoppingCart, User } from "lucide-react";
import SearchBar from "./SearchBar";

interface Props {
  query?: string;
}

export default function Navbar({ query }: Props) {
  return (
    <nav className="sticky top-0 z-50 border-b border-[var(--color-border)] bg-white shadow-sm">
      <div className="mx-auto flex max-w-7xl items-center gap-6 px-4 py-3">
        {/* Logo */}
        <Link
          to="/"
          className="flex items-center gap-2 shrink-0 no-underline"
        >
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[var(--color-brand)] text-white font-bold text-sm">
            EM
          </div>
          <span className="hidden sm:block text-lg font-bold text-[var(--color-text)]">
            Epic Marketplace
          </span>
        </Link>

        {/* Search */}
        <div className="flex-1">
          <SearchBar initialQuery={query} compact />
        </div>

        {/* Right icons */}
        <div className="flex items-center gap-4 shrink-0">
          <button className="text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition">
            <User size={22} />
          </button>
          <button className="relative text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition">
            <ShoppingCart size={22} />
            <span className="absolute -right-1 -top-1 flex h-4 w-4 items-center justify-center rounded-full bg-[var(--color-brand)] text-[10px] font-bold text-white">
              0
            </span>
          </button>
        </div>
      </div>
    </nav>
  );
}
