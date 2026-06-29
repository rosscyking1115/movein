import Link from "next/link";
import { Logo } from "./Logo";

const EXPLORE: [string, string][] = [
  ["/search", "Search areas"],
  ["/compare", "Compare"],
  ["/check", "Check a listing"],
  ["/rankings", "Rankings"],
];

const SOURCES: [string, string][] = [
  ["/methodology", "Methodology"],
  ["/methodology#sources", "Data sources"],
];

export function SiteFooter() {
  return (
    <footer className="mt-auto border-t border-rule bg-card2">
      <div className="mx-auto max-w-[1140px] px-6 py-12">
        <div className="flex flex-wrap justify-between gap-10">
          <div className="max-w-[420px]">
            <div className="flex items-center gap-2.5">
              <Logo size={22} />
              <span className="font-display text-lg font-bold text-ink">MoveIn</span>
            </div>
            <p className="mt-3 text-sm text-ink2">
              Area-level indicators for England &amp; Wales, built from official open
              data. Every score is shown beside the figure behind it — we never
              label a place &ldquo;good&rdquo; or &ldquo;safe.&rdquo;
            </p>
          </div>
          <div className="flex gap-12">
            <FooterCol title="Explore" links={EXPLORE} />
            <FooterCol title="Sources" links={SOURCES} />
          </div>
        </div>
        <div className="mt-9 border-t border-rule pt-[18px] text-xs text-muted">
          Indicators only — not a property valuation, and never a safe/unsafe
          verdict. Official open data, used under the Open Government Licence.
        </div>
      </div>
    </footer>
  );
}

function FooterCol({ title, links }: { title: string; links: [string, string][] }) {
  return (
    <div>
      <div className="mb-3 font-mono text-[11px] uppercase tracking-wider text-muted">{title}</div>
      <ul className="space-y-2 text-sm">
        {links.map(([href, label]) => (
          <li key={href}>
            <Link href={href} className="text-ink2 hover:text-ink">{label}</Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
