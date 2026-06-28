import { search } from "@/lib/api";
import type { SearchRequest } from "@/lib/types";
import { relay } from "../_proxy";

export async function POST(request: Request) {
  const body = (await request.json()) as SearchRequest;
  return relay(() => search(body));
}
