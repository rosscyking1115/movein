import { resolvePostcode } from "@/lib/api";
import { relay } from "../_proxy";

export async function GET(request: Request) {
  const postcode = new URL(request.url).searchParams.get("postcode") ?? "";
  if (postcode.trim().length < 5) {
    return Response.json({ detail: "Enter a full UK postcode." }, { status: 400 });
  }
  return relay(() => resolvePostcode(postcode));
}
