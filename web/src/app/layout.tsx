import type { Metadata } from "next";
import Link from "next/link";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

const SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL?.replace(/\/$/, "") ?? "http://localhost:3000";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: "Where to live — explainable UK neighbourhood scores",
    template: "%s · UK Housing Decision Support",
  },
  description:
    "Compare England & Wales neighbourhoods on affordability, safety, energy, flood risk and convenience — every score shown beside the raw fact behind it. Indicators, not verdicts.",
  openGraph: {
    type: "website",
    siteName: "UK Housing Decision Support",
    locale: "en_GB",
  },
  robots: { index: true, follow: true },
};

function Nav() {
  return (
    <header className="border-b border-rule">
      <nav className="mx-auto flex max-w-5xl items-center gap-6 px-5 py-4 text-sm">
        <Link href="/" className="font-semibold tracking-tight">
          UK Housing<span className="text-accent">.</span>
        </Link>
        <div className="ml-auto flex items-center gap-5 text-ink-muted">
          <Link href="/search" className="hover:text-ink">Search</Link>
          <Link href="/compare" className="hover:text-ink">Compare</Link>
          <Link href="/check" className="hover:text-ink">Check a listing</Link>
          <Link href="/methodology" className="hover:text-ink">Methodology</Link>
        </div>
      </nav>
    </header>
  );
}

function Footer() {
  return (
    <footer className="mt-auto border-t border-rule">
      <div className="mx-auto max-w-5xl px-5 py-8 text-xs text-ink-muted">
        <p className="max-w-2xl">
          Area-level indicators for England &amp; Wales, built from official open
          data. We show the fact behind every score and never label an area
          &ldquo;safe&rdquo; or &ldquo;unsafe&rdquo;. Not a property valuation.
        </p>
        <div className="mt-4 flex flex-wrap gap-4">
          <Link href="/search" className="hover:text-ink">Search areas</Link>
          <Link href="/rankings" className="hover:text-ink">Rankings</Link>
          <Link href="/compare" className="hover:text-ink">Compare</Link>
          <Link href="/methodology" className="hover:text-ink">Methodology</Link>
          <Link href="/methodology#sources" className="hover:text-ink">Data sources</Link>
        </div>
      </div>
    </footer>
  );
}

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en-GB" className={`${geistSans.variable} ${geistMono.variable} h-full`}>
      <body className="flex min-h-full flex-col bg-paper text-ink">
        <Nav />
        <main className="flex-1">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
