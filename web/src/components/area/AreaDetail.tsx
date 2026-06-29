"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import type { ComponentKey } from "@/lib/types";
import type { ReceiptRow } from "@/lib/indicators";

// The two-column hero: the indicator schedule (receipt) + a "what this means"
// rail whose priority chips reorder the schedule. Server-rendered for SEO; the
// reordering hydrates on the client. Indicators, never verdicts.

type FactRow = { label: string; value: string };

export function AreaDetail({
  rows,
  summary,
  rentRows,
  factRows,
  sources,
  areaId,
}: {
  rows: ReceiptRow[];
  summary: string;
  rentRows: FactRow[];
  factRows: FactRow[];
  sources: { no: number; text: string }[];
  areaId: string;
}) {
  const [priorities, setPriorities] = useState<Set<ComponentKey>>(new Set());

  const ordered = useMemo(() => {
    const chosen = rows.filter((r) => priorities.has(r.key));
    const rest = rows.filter((r) => !priorities.has(r.key));
    return [...chosen, ...rest];
  }, [rows, priorities]);

  const chosenRows = rows.filter((r) => priorities.has(r.key));

  function toggle(key: ComponentKey) {
    setPriorities((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  return (
    <div className="mt-8 grid items-start gap-[26px] lg:grid-cols-[minmax(0,1.55fr)_minmax(0,1fr)]">
      {/* RECEIPT */}
      <div className="overflow-hidden rounded-[16px] border border-rule2 bg-card shadow-[0_2px_5px_rgba(20,30,40,.05)]">
        <div className="perforation" />
        <div className="flex flex-wrap items-baseline justify-between gap-2 px-[26px] pt-[22px] pb-2">
          <div className="font-mono text-xs uppercase tracking-[.14em] text-ink">Indicator schedule</div>
          <div className="font-mono text-[11px] text-muted">score · 0–100 · neutral scale</div>
        </div>
        <div className="px-[26px] pb-2">
          {ordered.map((r) => {
            const chosen = priorities.has(r.key);
            return (
              <div
                key={r.key}
                className={`border-t border-rule py-[18px] ${chosen ? "bg-accent-wash" : ""}`}
              >
                <div className="flex flex-wrap items-start justify-between gap-[18px]">
                  <div className="min-w-[180px] flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-base font-semibold text-ink">{r.name}</span>
                      {chosen && (
                        <span className="rounded border border-accent px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wider text-accent">
                          Your priority
                        </span>
                      )}
                    </div>
                    <div className="mt-[3px] text-[13px] text-muted">
                      {r.measure}
                      <sup className="ml-0.5 font-mono text-[10px] text-accent">{r.footnote}</sup>
                    </div>
                    <p className="mt-[9px] max-w-[340px] text-[13.5px] leading-[1.5] text-ink2">{r.plain}</p>
                  </div>
                  <div className="w-[200px] shrink-0">
                    {r.hasData ? (
                      <>
                        <div className="flex items-baseline justify-end gap-[3px]">
                          <span className="font-mono text-[26px] font-medium text-ink">{r.scoreText}</span>
                          <span className="font-mono text-[13px] text-muted">/100</span>
                        </div>
                        <div className="relative mt-[9px] h-[7px] rounded bg-bar-track">
                          <div className="h-full rounded bg-bar" style={{ width: r.barWidth }} />
                          <span
                            title="median area = 50"
                            className="absolute top-[-3px] left-1/2 h-[13px] w-px bg-rule2"
                          />
                        </div>
                        <div className="mt-[7px] text-right font-mono text-[11px] text-muted">{r.percentileTick}</div>
                      </>
                    ) : (
                      <div className="text-right">
                        <span className="font-mono text-[26px] text-muted">—</span>
                        <div className="mt-1.5 inline-block rounded-md border border-dashed border-rule2 px-2 py-1 text-xs text-muted">
                          No data · not scored as zero
                        </div>
                      </div>
                    )}
                  </div>
                </div>
                <div className="mt-[14px] flex flex-wrap items-center justify-between gap-3 rounded-[9px] border border-rule bg-card2 px-[14px] py-[11px]">
                  <div className="text-xs text-muted">{r.factLabel}</div>
                  {r.isEpc && r.epcColor ? (
                    <span
                      className="rounded-[5px] px-2.5 py-[3px] font-mono text-sm font-semibold"
                      style={{ background: r.epcColor, color: r.epcText }}
                    >
                      {r.factValue}
                    </span>
                  ) : (
                    <span className="font-mono text-[15px] font-semibold text-ink">{r.factValue}</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
        <div className="border-t border-rule2 bg-card2 px-[26px] py-4">
          <div className="mb-[9px] font-mono text-[10px] uppercase tracking-[.1em] text-muted">Sources</div>
          {sources.map((s) => (
            <div key={s.no} className="text-xs leading-[1.7] text-ink2">
              <sup className="font-mono text-accent">{s.no}</sup> {s.text}
            </div>
          ))}
        </div>
      </div>

      {/* RAIL */}
      <div className="flex flex-col gap-5 lg:sticky lg:top-[78px]">
        <div className="rounded-[16px] border border-accent-line bg-accent-wash p-[22px]">
          <div className="mb-3 font-mono text-[11px] uppercase tracking-[.12em] text-accent">
            What this means for you
          </div>
          <p className="mb-4 text-[15.5px] leading-[1.6] text-ink">{summary}</p>
          <div className="mb-2.5 text-[13px] text-ink2">Tell us what matters and we&rsquo;ll reorder the schedule:</div>
          <div className="flex flex-wrap gap-[7px]">
            {rows.map((r) => {
              const active = priorities.has(r.key);
              return (
                <button
                  key={r.key}
                  type="button"
                  onClick={() => toggle(r.key)}
                  aria-pressed={active}
                  className={`rounded-full border px-3 py-1.5 text-[13px] ${
                    active
                      ? "border-accent bg-accent text-white"
                      : "border-rule2 bg-card text-ink2 hover:text-ink"
                  }`}
                >
                  {r.priorityLabel}
                </button>
              );
            })}
          </div>

          {chosenRows.length > 0 && (
            <div className="mt-4 border-t border-accent-line pt-3.5">
              <div className="mb-2.5 text-[13px] text-ink2">Your priorities here:</div>
              {chosenRows.map((r) => (
                <div key={r.key} className="mb-2.5 flex items-start gap-2.5">
                  <span className="w-[30px] shrink-0 font-mono text-[13px] font-semibold text-accent">{r.scoreText}</span>
                  <span className="text-[13.5px] leading-[1.5] text-ink">{r.plain}</span>
                </div>
              ))}
            </div>
          )}

          <div className="mt-4 border-t border-accent-line pt-3 text-[11.5px] leading-[1.55] text-muted">
            These are indicators, not a verdict. We never label an area &ldquo;good,&rdquo;
            &ldquo;bad,&rdquo; &ldquo;safe&rdquo; or &ldquo;unsafe&rdquo; — only higher or lower than
            other areas, with the figure shown.
          </div>
        </div>

        <div className="flex gap-2.5">
          <Link
            href={`/compare?areas=${areaId}`}
            className="flex min-h-[46px] flex-1 items-center justify-center rounded-[10px] bg-accent px-3 text-sm font-semibold text-white"
          >
            Compare
          </Link>
          <Link
            href="/search"
            className="flex min-h-[46px] flex-1 items-center justify-center rounded-[10px] border border-rule2 bg-card px-3 text-sm font-semibold text-ink"
          >
            Rank by my priorities
          </Link>
        </div>

        <div className="rounded-[16px] border border-rule2 bg-card p-[22px]">
          <div className="mb-4 font-mono text-[11px] uppercase tracking-[.12em] text-ink">Full schedule of facts</div>
          <FactList title="Rent by bedrooms" rows={rentRows} />
          <div className="mt-[18px]">
            <FactList title="Area facts" rows={factRows} />
          </div>
        </div>
      </div>
    </div>
  );
}

function FactList({ title, rows }: { title: string; rows: FactRow[] }) {
  return (
    <div>
      <div className="mb-[9px] text-xs uppercase tracking-[.06em] text-muted">{title}</div>
      <dl className="m-0">
        {rows.map((r) => (
          <div key={r.label} className="flex justify-between gap-3 border-t border-rule py-2">
            <dt className="text-[13.5px] text-ink2">{r.label}</dt>
            <dd className="m-0 text-right font-mono text-sm text-ink">{r.value}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
