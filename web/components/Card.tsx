import type { ReactNode } from "react";

// The white rounded card used across the site.
export function Card({ className = "", children }: { className?: string; children: ReactNode }) {
  return (
    <div
      className={`rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_12px_40px_-20px_rgba(11,27,58,0.25)] ${className}`}
    >
      {children}
    </div>
  );
}
