// Server-side client for the Phase 1 FastAPI service (api/).
// The website is a pure HTTP client of the API — no direct DuckDB access.
// Client components never import this; they call the same-origin BFF routes
// under /api/* which proxy here (hides the API origin, sidesteps CORS).

import { cache } from "react";
import type {
  Area,
  ListingCheckRequest,
  ListingCheckResponse,
  Meta,
  ResolveResponse,
  SearchRequest,
  SearchResponse,
} from "./types";

const API_BASE_URL =
  process.env.API_BASE_URL?.replace(/\/$/, "") ?? "http://127.0.0.1:8000";

// Revalidate cached GETs daily; the dataset is static between refreshes.
const DAY = 60 * 60 * 24;

class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
  ) {
    super(`API ${status}: ${detail}`);
    this.name = "ApiError";
  }
}

async function readDetail(res: Response): Promise<string> {
  try {
    const body = await res.json();
    return typeof body?.detail === "string" ? body.detail : res.statusText;
  } catch {
    return res.statusText;
  }
}

async function getJson<T>(path: string, revalidate: number = DAY): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    next: { revalidate },
    headers: { accept: "application/json" },
  });
  if (!res.ok) throw new ApiError(res.status, await readDetail(res));
  return res.json() as Promise<T>;
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "content-type": "application/json", accept: "application/json" },
    body: JSON.stringify(body),
    // POST is not cached by Next; results vary by weights/filters.
    cache: "no-store",
  });
  if (!res.ok) throw new ApiError(res.status, await readDetail(res));
  return res.json() as Promise<T>;
}

export const getMeta = cache((): Promise<Meta> => getJson<Meta>("/v1/meta"));

// Deduped per-request so a page + its generateMetadata share one fetch.
export const getArea = cache(
  (msoa: string): Promise<Area> =>
    getJson<Area>(`/v1/areas/${encodeURIComponent(msoa)}`),
);

/** getArea, but a clean null for unknown codes instead of throwing. */
export async function getAreaOrNull(msoa: string): Promise<Area | null> {
  try {
    return await getArea(msoa);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) return null;
    throw err;
  }
}

// The whole dataset, paginated out of /v1/search. Hubs and the link mesh group
// over this until a slim /v1/areas/index endpoint exists. Because /v1/search is
// POST (never fetch-cached), we memo at module scope with a TTL so every hub
// render in a server process shares one ~37-request load, not its own.
const ALL_TTL_MS = 60 * 60 * 1000;
let allAreasCache: { at: number; promise: Promise<Area[]> } | null = null;

async function fetchAllAreas(): Promise<Area[]> {
  const PAGE = 200;
  const out: Area[] = [];
  for (let offset = 0; ; offset += PAGE) {
    const res = await search({ limit: PAGE, offset });
    out.push(...res.results);
    if (res.offset + res.limit >= res.total) break;
  }
  return out;
}

export function getAllAreas(): Promise<Area[]> {
  const now = Date.now();
  if (!allAreasCache || now - allAreasCache.at > ALL_TTL_MS) {
    const promise = fetchAllAreas().catch((err) => {
      allAreasCache = null; // don't cache a failed load
      throw err;
    });
    allAreasCache = { at: now, promise };
  }
  return allAreasCache.promise;
}

export function resolvePostcode(postcode: string): Promise<ResolveResponse> {
  return getJson<ResolveResponse>(
    `/v1/areas/resolve?postcode=${encodeURIComponent(postcode)}`,
    0, // resolve is user-driven; don't cache stale postcode lookups
  );
}

export function search(req: SearchRequest): Promise<SearchResponse> {
  return postJson<SearchResponse>("/v1/search", req);
}

export function listingCheck(
  req: ListingCheckRequest,
): Promise<ListingCheckResponse> {
  return postJson<ListingCheckResponse>("/v1/listing-check", req);
}

export { ApiError };
