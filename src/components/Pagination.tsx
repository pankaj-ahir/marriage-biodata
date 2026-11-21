"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";

/** Templates shown per page (4 rows x 3 columns on desktop). */
export const PAGE_SIZE = 12;

/** Page numbers to show: always first/last, the current page and its neighbours, "…" in the gaps. */
function pageList(page: number, total: number): (number | "gap-l" | "gap-r")[] {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);
  const out: (number | "gap-l" | "gap-r")[] = [1];
  const from = Math.max(2, page - 1);
  const to = Math.min(total - 1, page + 1);
  if (from > 2) out.push("gap-l");
  for (let i = from; i <= to; i++) out.push(i);
  if (to < total - 1) out.push("gap-r");
  out.push(total);
  return out;
}

/**
 * Page state for a list. `reset()` goes back to page 1 (call it when the filter changes);
 * the page is always clamped, so a shrinking list can never leave you on an empty page.
 */
export function usePagination<T>(items: T[], pageSize = PAGE_SIZE) {
  const [rawPage, setPage] = useState(1);
  const totalPages = Math.max(1, Math.ceil(items.length / pageSize));
  const page = Math.min(Math.max(1, rawPage), totalPages);
  const start = (page - 1) * pageSize;
  return {
    page,
    totalPages,
    setPage,
    reset: () => setPage(1),
    start,
    pageItems: items.slice(start, start + pageSize),
  };
}

export default function Pagination({
  page,
  totalPages,
  total,
  pageSize = PAGE_SIZE,
  onChange,
  compact = false,
  controls,
  label = "Template pages",
}: {
  page: number;
  totalPages: number;
  total: number;
  pageSize?: number;
  onChange: (page: number) => void;
  compact?: boolean;
  /** id of the element this pager controls (for screen readers) */
  controls?: string;
  label?: string;
}) {
  if (totalPages <= 1) return null;

  const first = (page - 1) * pageSize + 1;
  const last = Math.min(total, page * pageSize);
  const size = compact ? "h-9 min-w-9 px-2 text-xs" : "h-11 min-w-11 px-3 text-sm";
  const base = cn(
    "inline-flex items-center justify-center rounded-full border font-semibold transition touch-manipulation",
    "disabled:cursor-not-allowed disabled:opacity-40",
    size
  );
  const idle = "border-stone-300 bg-white text-stone-700 hover:border-[#7a5c14] hover:text-[#7a5c14]";

  return (
    <nav aria-label={label} className={cn("flex flex-col items-center gap-2", compact ? "mt-2" : "mt-8")}>
      <ul className="flex flex-wrap items-center justify-center gap-1.5 sm:gap-2">
        <li>
          <button
            type="button"
            className={cn(base, idle)}
            onClick={() => onChange(page - 1)}
            disabled={page <= 1}
            aria-label="Previous page"
            aria-controls={controls}
          >
            <span aria-hidden>‹</span>
            {!compact && <span className="ml-1 hidden sm:inline">Prev</span>}
          </button>
        </li>

        {pageList(page, totalPages).map((p) =>
          typeof p === "string" ? (
            <li key={p} aria-hidden className={cn("px-1 text-stone-400", compact ? "text-xs" : "text-sm")}>
              …
            </li>
          ) : (
            <li key={p}>
              <button
                type="button"
                className={cn(
                  base,
                  p === page ? "border-[#1c1917] bg-[#1c1917] text-[#e8d5a3] shadow" : idle
                )}
                onClick={() => onChange(p)}
                aria-label={`Page ${p}`}
                aria-current={p === page ? "page" : undefined}
                aria-controls={controls}
              >
                {p}
              </button>
            </li>
          )
        )}

        <li>
          <button
            type="button"
            className={cn(base, idle)}
            onClick={() => onChange(page + 1)}
            disabled={page >= totalPages}
            aria-label="Next page"
            aria-controls={controls}
          >
            {!compact && <span className="mr-1 hidden sm:inline">Next</span>}
            <span aria-hidden>›</span>
          </button>
        </li>
      </ul>
      <p className={cn("text-stone-500", compact ? "text-[11px]" : "text-xs")} aria-live="polite">
        Showing {first}–{last} of {total} templates
      </p>
    </nav>
  );
}
