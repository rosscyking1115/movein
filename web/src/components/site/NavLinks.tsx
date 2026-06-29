"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const ITEMS: [string, string][] = [
  ["/search", "Search"],
  ["/compare", "Compare"],
  ["/check", "Check"],
  ["/rankings", "Rankings"],
  ["/methodology", "Methodology"],
];

export function NavLinks() {
  const pathname = usePathname();
  return (
    <nav className="flex flex-wrap gap-0.5">
      {ITEMS.map(([href, label]) => {
        const active = pathname === href || pathname.startsWith(`${href}/`);
        return (
          <Link
            key={href}
            href={href}
            aria-current={active ? "page" : undefined}
            className={`inline-flex min-h-[38px] items-center rounded-lg px-3 py-2 text-sm ${
              active ? "bg-card2 font-semibold text-ink" : "font-medium text-muted hover:text-ink"
            }`}
          >
            {label}
          </Link>
        );
      })}
    </nav>
  );
}
