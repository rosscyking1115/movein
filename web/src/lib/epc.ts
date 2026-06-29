// Official EPC A–G band colours — the ONLY colours allowed to imply good/bad in
// the product. Score bars stay neutral (--bar). Both themes use these fixed hexes.
const EPC_COLORS: Record<string, string> = {
  A: "#008054",
  B: "#19b459",
  C: "#8dce46",
  D: "#ffd500",
  E: "#fcaa65",
  F: "#f18a31",
  G: "#e9153b",
};

export function epcColor(band: string | null | undefined): string | null {
  if (!band) return null;
  return EPC_COLORS[band.trim().toUpperCase()] ?? null;
}

// Readable text colour over the band chip: dark on the light-green/yellow bands.
export function epcText(band: string | null | undefined): string {
  const b = band?.trim().toUpperCase();
  return b === "C" || b === "D" ? "#1a1a1a" : "#ffffff";
}
