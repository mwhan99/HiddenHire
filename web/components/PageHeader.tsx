import type { ReactNode } from "react";

import { SiteHeader } from "./SiteHeader";

// The navy band at the top of every inner page: menu, a small line above
// the title, the title, a short description, and optional extras below.
export function PageHeader({
  active,
  eyebrow,
  title,
  description,
  children,
}: {
  active?: string;
  eyebrow: ReactNode;
  title: ReactNode;
  description?: ReactNode;
  children?: ReactNode;
}) {
  return (
    <section className="relative overflow-hidden bg-gradient-to-br from-navy to-navy-2 text-white">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 opacity-[0.07]"
        style={{
          backgroundImage:
            "linear-gradient(#fff 1px, transparent 1px), linear-gradient(90deg, #fff 1px, transparent 1px)",
          backgroundSize: "48px 48px",
        }}
      />
      <SiteHeader active={active} />
      <div className="relative mx-auto max-w-6xl px-4 pb-12 pt-8 sm:pt-12">
        <div className="text-sm font-medium text-blue-300">{eyebrow}</div>
        <h1 className="mt-3 text-4xl font-bold tracking-tight sm:text-5xl">{title}</h1>
        {description && (
          <p className="mt-4 max-w-2xl text-lg leading-relaxed text-slate-300">{description}</p>
        )}
        {children}
      </div>
    </section>
  );
}
