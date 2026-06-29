// MoveIn "gable house" mark. Roof + walls use --ink, the floor line uses
// --accent; both recolour automatically per theme.
export function Logo({ size = 26 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" aria-hidden="true" style={{ display: "block" }}>
      <path d="M4 27 L24 11 L44 27" fill="none" stroke="var(--ink)" strokeWidth="4.2" strokeLinejoin="miter" />
      <line x1="9" y1="27" x2="9" y2="41" stroke="var(--ink)" strokeWidth="4.2" />
      <line x1="39" y1="27" x2="39" y2="41" stroke="var(--ink)" strokeWidth="4.2" />
      <line x1="7" y1="41.5" x2="41" y2="41.5" stroke="var(--accent)" strokeWidth="4" />
    </svg>
  );
}
