// Mobile API client. Unlike the website (which proxies through same-origin BFF
// routes), the app calls the deployed FastAPI service directly. Override the
// base URL with EXPO_PUBLIC_API_URL (e.g. a local `uvicorn` during development).

import type {
  Area,
  ListingCheckRequest,
  ListingCheckResponse,
  Meta,
  ResolveResponse,
  SearchRequest,
  SearchResponse,
} from "./types";

const API_BASE_URL = (
  process.env.EXPO_PUBLIC_API_URL ?? "https://uk-housing-decision-support-api.fly.dev"
).replace(/\/$/, "");

export class ApiError extends Error {
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

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
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
  });
  if (!res.ok) throw new ApiError(res.status, await readDetail(res));
  return res.json() as Promise<T>;
}

export const getMeta = (): Promise<Meta> => getJson<Meta>("/v2/meta");

export const getArea = (msoa: string): Promise<Area> =>
  getJson<Area>(`/v2/areas/${encodeURIComponent(msoa)}`);

export const resolvePostcode = (postcode: string): Promise<ResolveResponse> =>
  getJson<ResolveResponse>(`/v2/areas/resolve?postcode=${encodeURIComponent(postcode)}`);

export const search = (req: SearchRequest): Promise<SearchResponse> =>
  postJson<SearchResponse>("/v2/search", req);

export const listingCheck = (
  req: ListingCheckRequest,
): Promise<ListingCheckResponse> =>
  postJson<ListingCheckResponse>("/v2/listing-check", req);
