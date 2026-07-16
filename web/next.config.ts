import type { NextConfig } from "next";
import path from "node:path";

// Baseline security headers, set in next.config so they apply on any host
// (Vercel, behind Cloudflare, or self-hosted) rather than a vendor config file.
const securityHeaders = [
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "X-Frame-Options", value: "SAMEORIGIN" },
  { key: "Strict-Transport-Security", value: "max-age=63072000; includeSubDomains; preload" },
  { key: "Permissions-Policy", value: "geolocation=(), microphone=(), camera=()" },
];

const nextConfig: NextConfig = {
  poweredByHeader: false,
  // The versioned scoring contract lives at repository root and is consumed by
  // SQL, Python, and this client bundle. Keep Turbopack rooted at the repository
  // so the web implementation does not duplicate scoring constants.
  turbopack: {
    root: path.join(process.cwd(), ".."),
  },
  async headers() {
    return [{ source: "/:path*", headers: securityHeaders }];
  },
};

export default nextConfig;
