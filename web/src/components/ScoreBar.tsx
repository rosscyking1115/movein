import { score as fmtScore } from "@/lib/format";

// A single neutral ledger bar. Deliberately one colour: we rank, we don't judge.
export function ScoreBar({
  value,
  width = "full",
}: {
  value: number | null | undefined;
  width?: "full" | "compact";
}) {
  const pct = value == null ? 0 : Math.max(0, Math.min(100, value));
  const known = value != null;
  return (
    <div className="flex items-center gap-3">
      <div
        className={`${width === "full" ? "w-full" : "w-24"} h-2 rounded-full bg-track`}
        role="img"
        aria-label={known ? `Score ${fmtScore(value)} out of 100` : "No score available"}
      >
        <div
          className="h-2 rounded-full bg-accent transition-[width]"
          style={{ width: `${pct}%`, opacity: known ? 1 : 0 }}
        />
      </div>
      <span className="tnum w-7 shrink-0 text-right text-sm tabular-nums">
        {fmtScore(value)}
      </span>
    </div>
  );
}
