import { listingCheck } from "@/lib/api";
import type { ListingCheckRequest } from "@/lib/types";
import { relay } from "../_proxy";

export async function POST(request: Request) {
  const body = (await request.json()) as ListingCheckRequest;
  return relay(() => listingCheck(body));
}
