import { ApiError } from "@/lib/api";

// Shared error shaping for the BFF routes: forward the API's status + detail
// instead of leaking a 500 for every upstream 404/422.
export async function relay<T>(fn: () => Promise<T>): Promise<Response> {
  try {
    return Response.json(await fn());
  } catch (err) {
    if (err instanceof ApiError) {
      return Response.json({ detail: err.detail }, { status: err.status });
    }
    return Response.json({ detail: "Upstream API unavailable." }, { status: 502 });
  }
}
