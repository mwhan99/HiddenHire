import type { Metadata } from "next";
import type { CSSProperties, ReactNode } from "react";
import { Bricolage_Grotesque, Inter, Plus_Jakarta_Sans } from "next/font/google";

import { getLatestHeadline, getLatestMomentum } from "@/lib/data";

// A temporary page for migration step 7: three design directions for the
// HiddenHire home page, side by side, using real numbers. Meng picks one,
// then this page is deleted.

export const metadata: Metadata = {
  title: "Design options · HiddenHire",
  robots: { index: false },
};

const jakarta = Plus_Jakarta_Sans({ subsets: ["latin"] });
const bricolage = Bricolage_Grotesque({ subsets: ["latin"] });
const inter = Inter({ subsets: ["latin"] });

type Palette = {
  id: string;
  name: string;
  mood: string;
  fontName: string;
  fontClass: string;
  background: string;
  ink: string;
  muted: string;
  from: string;
  to: string;
  soft: string;
};

const PALETTES: Palette[] = [
  {
    id: "a",
    name: "A · Signal Green",
    mood: "Calm and trustworthy. Green reads as “growing”, which is what momentum means.",
    fontName: "Plus Jakarta Sans",
    fontClass: jakarta.className,
    background:
      "radial-gradient(60% 50% at 10% 10%, #c9f5e3 0%, transparent 70%)," +
      "radial-gradient(50% 45% at 90% 20%, #d7ecff 0%, transparent 70%)," +
      "radial-gradient(60% 50% at 50% 100%, #e9fbf3 0%, transparent 70%), #f8fcfa",
    ink: "#0b2a24",
    muted: "#4b635d",
    from: "#10b981",
    to: "#0d9488",
    soft: "#e6f8f1",
  },
  {
    id: "b",
    name: "B · Sunrise Amber",
    mood: "Warm and energetic. “Before everyone else”: early-morning New York light.",
    fontName: "Bricolage Grotesque",
    fontClass: bricolage.className,
    background:
      "radial-gradient(60% 50% at 8% 12%, #ffe3c8 0%, transparent 70%)," +
      "radial-gradient(50% 45% at 92% 18%, #fff1bf 0%, transparent 70%)," +
      "radial-gradient(60% 50% at 50% 100%, #ffeadb 0%, transparent 70%), #fffaf4",
    ink: "#1f1a17",
    muted: "#6b5d52",
    from: "#f59e0b",
    to: "#ea580c",
    soft: "#fff1e2",
  },
  {
    id: "c",
    name: "C · Cobalt Sky",
    mood: "Crisp and professional. Feels like a modern data product.",
    fontName: "Inter",
    fontClass: inter.className,
    background:
      "radial-gradient(60% 50% at 10% 10%, #d6e6ff 0%, transparent 70%)," +
      "radial-gradient(50% 45% at 90% 20%, #d4f4fb 0%, transparent 70%)," +
      "radial-gradient(60% 50% at 50% 100%, #e8eeff 0%, transparent 70%), #f7f9ff",
    ink: "#0b1b3a",
    muted: "#4a5878",
    from: "#2563eb",
    to: "#06b6d4",
    soft: "#e8f0ff",
  },
];

type HeroData = {
  companies: number;
  openRoles: number;
  weekChange: number | null;
  newRoles: number | null;
  closedRoles: number | null;
  jump: { name: string; change: number } | null;
  growing: string | null;
};

export default async function DesignPage() {
  const [headline, momentum] = await Promise.all([
    getLatestHeadline(),
    getLatestMomentum(),
  ]);
  const jump = [...momentum]
    .filter((row) => (row.net_change ?? 0) > 0)
    .sort((a, b) => (b.net_change ?? 0) - (a.net_change ?? 0))[0];
  const data: HeroData = {
    companies: headline?.companies ?? 0,
    openRoles: headline?.open_roles ?? 0,
    weekChange:
      headline?.previous_open_roles != null
        ? headline.open_roles - headline.previous_open_roles
        : null,
    newRoles: headline?.new_roles ?? null,
    closedRoles: headline?.closed_roles ?? null,
    jump: jump ? { name: jump.company_name, change: jump.net_change ?? 0 } : null,
    growing: momentum.find((row) => row.momentum === "Growing")?.company_name ?? null,
  };

  return (
    <div className="bg-zinc-100">
      {PALETTES.map((palette) => (
        <section key={palette.id} id={`option-${palette.id}`} className="border-b-8 border-zinc-100">
          <div className="bg-zinc-900 px-4 py-3 text-sm text-zinc-100">
            <b>{palette.name}</b> · {palette.fontName} · {palette.mood}
          </div>
          <Hero palette={palette} data={data} />
        </section>
      ))}
    </div>
  );
}

function signed(value: number) {
  return `${value > 0 ? "+" : ""}${value.toLocaleString("en-US")}`;
}

function Hero({ palette, data }: { palette: Palette; data: HeroData }) {
  const vars = {
    "--ink": palette.ink,
    "--muted": palette.muted,
    "--from": palette.from,
    "--to": palette.to,
    "--soft": palette.soft,
    background: palette.background,
  } as CSSProperties;
  const gradient = `linear-gradient(100deg, ${palette.from}, ${palette.to})`;

  return (
    <div className={`${palette.fontClass} relative overflow-hidden text-[var(--ink)]`} style={vars}>
      {/* Faint dot grid, like Parrot's background texture. */}
      <div
        className="pointer-events-none absolute inset-0 opacity-50"
        style={{
          backgroundImage: "radial-gradient(rgba(15,23,42,0.08) 1px, transparent 1px)",
          backgroundSize: "22px 22px",
        }}
      />

      <div className="relative mx-auto max-w-6xl px-4 pb-20 pt-5">
        {/* Floating nav bar */}
        <nav className="flex items-center justify-between rounded-full border border-white/70 bg-white/75 px-4 py-2.5 shadow-[0_8px_30px_rgba(15,23,42,0.06)] backdrop-blur">
          <div className="flex items-center gap-2.5">
            <Logo from={palette.from} to={palette.to} />
            <span className="text-lg font-bold tracking-tight">HiddenHire</span>
          </div>
          <div className="hidden items-center gap-7 text-[15px] text-[var(--muted)] md:flex">
            <span>Find roles</span>
            <span>Company momentum</span>
            <span>Insights</span>
            <span>Methodology</span>
          </div>
          <span
            className="rounded-full px-4 py-2 text-sm font-semibold text-white shadow-[0_6px_20px_rgba(15,23,42,0.18)]"
            style={{ background: gradient }}
          >
            Find my matches
          </span>
        </nav>

        {/* Floating example chips with real numbers (hidden on phones) */}
        {data.jump && (
          <Chip className="left-0 top-44" >
            <b>{data.jump.name}</b> · {signed(data.jump.change)} roles this week
          </Chip>
        )}
        {data.newRoles != null && (
          <Chip className="right-0 top-32">
            <b>{data.newRoles.toLocaleString("en-US")}</b> new roles posted this week
          </Chip>
        )}
        {data.growing && (
          <Chip className="right-8 top-[25rem]">
            <span style={{ color: palette.from }}>▲</span> <b>{data.growing}</b> is growing fast
          </Chip>
        )}

        {/* Headline */}
        <div className="mx-auto mt-20 max-w-3xl text-center">
          <span className="inline-flex items-center gap-2 rounded-full border border-white/80 bg-white/70 px-3.5 py-1.5 text-sm font-medium shadow-sm" style={{ color: palette.to }}>
            <span className="h-2 w-2 rounded-full" style={{ background: gradient }} />
            Weekly hiring signals from {data.companies} NYC startups
          </span>
          <h1 className="mt-6 text-5xl font-extrabold leading-[1.02] tracking-tight sm:text-7xl">
            Find the startups hiring{" "}
            <span className="bg-clip-text text-transparent" style={{ backgroundImage: gradient }}>
              for you
            </span>
            , before everyone else.
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-[var(--muted)] sm:text-xl">
            HiddenHire tracks the career pages of emerging New York startups every
            week and ranks openings by your fit and each company&apos;s hiring momentum.
          </p>
        </div>

        {/* Search card */}
        <div className="mx-auto mt-10 max-w-3xl rounded-3xl border border-white/80 bg-white/85 p-4 shadow-[0_20px_60px_rgba(15,23,42,0.08)] backdrop-blur">
          <div className="flex items-center gap-3 px-2 py-2 text-lg text-[var(--muted)]">
            <SearchIcon color={palette.to} />
            What role are you looking for?
          </div>
          <div className="mt-3 flex flex-wrap items-center justify-between gap-3 border-t border-zinc-100 px-2 pt-3">
            <div className="flex flex-wrap gap-2">
              {["Business Analyst", "Strategy", "Product", "Data Science"].map((role) => (
                <span key={role} className="rounded-full bg-[var(--soft)] px-3 py-1 text-sm font-medium">
                  {role}
                </span>
              ))}
            </div>
            <span
              className="flex h-11 w-11 items-center justify-center rounded-full text-xl text-white"
              style={{ background: gradient }}
            >
              →
            </span>
          </div>
        </div>

        {/* Stats row */}
        <div className="mx-auto mt-8 grid max-w-4xl grid-cols-2 gap-3 sm:grid-cols-4">
          <Stat label="Companies tracked" value={String(data.companies)} note="Refreshed every Monday" />
          <Stat
            label="Open roles"
            value={data.openRoles.toLocaleString("en-US")}
            note={data.weekChange != null ? `${signed(data.weekChange)} vs last week` : "First week"}
            noteColor={palette.from}
          />
          <Stat
            label="New this week"
            value={data.newRoles != null ? data.newRoles.toLocaleString("en-US") : "—"}
            note={data.closedRoles != null ? `${data.closedRoles} closed` : ""}
          />
          <Stat
            label="Biggest jump"
            value={data.jump?.name ?? "—"}
            note={data.jump ? `${signed(data.jump.change)} open roles` : ""}
            noteColor={palette.from}
          />
        </div>
      </div>
    </div>
  );
}

function Chip({ className, children }: { className: string; children: ReactNode }) {
  return (
    <div
      className={`absolute hidden rounded-2xl border border-white/80 bg-white/80 px-4 py-3 text-[15px] shadow-[0_10px_30px_rgba(15,23,42,0.07)] backdrop-blur lg:block ${className}`}
    >
      {children}
    </div>
  );
}

function Stat({
  label,
  value,
  note,
  noteColor,
}: {
  label: string;
  value: string;
  note: string;
  noteColor?: string;
}) {
  return (
    <div className="rounded-2xl border border-white/80 bg-white/70 p-4 shadow-sm backdrop-blur">
      <div className="text-xs font-semibold uppercase tracking-wider text-[var(--muted)]">{label}</div>
      <div className="mt-1 truncate text-2xl font-bold tracking-tight">{value}</div>
      <div className="mt-0.5 text-sm text-[var(--muted)]" style={noteColor ? { color: noteColor } : undefined}>
        {note}
      </div>
    </div>
  );
}

function Logo({ from, to }: { from: string; to: string }) {
  const id = `logo-${from.slice(1)}`;
  return (
    <svg width="30" height="30" viewBox="0 0 32 32" aria-hidden="true">
      <defs>
        <linearGradient id={id} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor={from} />
          <stop offset="1" stopColor={to} />
        </linearGradient>
      </defs>
      <rect width="32" height="32" rx="9" fill={`url(#${id})`} />
      <circle cx="14.5" cy="14.5" r="6" fill="none" stroke="white" strokeWidth="2.6" />
      <path d="M19 19l5 5" stroke="white" strokeWidth="2.6" strokeLinecap="round" />
      <path d="M14.5 11.5v6M11.5 14.5h6" stroke="white" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  );
}

function SearchIcon({ color }: { color: string }) {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="11" cy="11" r="7" stroke={color} strokeWidth="2" />
      <path d="M16.5 16.5L21 21" stroke={color} strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}
