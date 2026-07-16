import type { Metadata } from "next";
import { Playfair_Display, IBM_Plex_Sans, IBM_Plex_Mono } from "next/font/google";
import "./globals.css";
import { SiteHeader } from "@/components/site/SiteHeader";
import { SiteFooter } from "@/components/site/SiteFooter";

const display = Playfair_Display({ subsets: ["latin"], weight: ["500", "600", "700", "800"], variable: "--ff-display" });
const sans = IBM_Plex_Sans({ subsets: ["latin"], weight: ["400", "500", "600", "700"], variable: "--ff-sans" });
const mono = IBM_Plex_Mono({ subsets: ["latin"], weight: ["400", "500", "600"], variable: "--ff-mono" });

const SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL?.replace(/\/$/, "") ?? "http://localhost:3000";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: "England & Wales Housing Decision Support — evidence beside every score",
    template: "%s · England & Wales Housing Decision Support",
  },
  description:
    "England and Wales neighbourhood decision support from official open data, with each indicator shown beside the fact behind it. Indicators, not verdicts.",
  openGraph: { type: "website", siteName: "England & Wales Housing Decision Support", locale: "en_GB" },
  robots: { index: true, follow: true },
};

// Apply the persisted theme before paint to avoid a flash of the wrong theme.
const themeScript = `(function(){try{var k='ew-housing-decision-support-theme',t=localStorage.getItem(k);if(t==='dark'||(!t&&window.matchMedia('(prefers-color-scheme: dark)').matches)){document.documentElement.classList.add('dark');}}catch(e){}})();`;

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="en-GB"
      suppressHydrationWarning
      className={`${display.variable} ${sans.variable} ${mono.variable} h-full`}
    >
      <body className="flex min-h-full flex-col bg-paper text-ink">
        <a href="#main-content" className="skip-link">
          Skip to main content
        </a>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
        <SiteHeader />
        <main id="main-content" className="flex-1">{children}</main>
        <SiteFooter />
      </body>
    </html>
  );
}
