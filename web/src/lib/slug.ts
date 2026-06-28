// Human-readable area URLs: /area/e02000984-clapham-north-lambeth
// The MSOA code (no hyphens) is the stable leading token; the name is decorative
// but indexable. Mismatched name parts canonicalise back to the computed slug.

export function slugify(text: string): string {
  return text
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[^\w\s-]/g, "")
    .trim()
    .replace(/[\s_]+/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "");
}

export function areaSlug(areaId: string, areaName: string): string {
  const name = slugify(areaName);
  return name ? `${areaId.toLowerCase()}-${name}` : areaId.toLowerCase();
}

/** Pull the MSOA code from a slug's leading token (before the first hyphen). */
export function msoaFromSlug(slug: string): string {
  const head = slug.split("-", 1)[0] ?? slug;
  return head.toUpperCase();
}
