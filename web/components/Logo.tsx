import Link from "next/link";

// The HiddenHire mark: a magnifying glass with a plus, for "discover
// roles you would otherwise miss". `dark` is for navy backgrounds.
export function Logo({ dark = false }: { dark?: boolean }) {
  const tile = dark ? "#ffffff" : "#2563eb";
  const mark = dark ? "#2563eb" : "#ffffff";
  return (
    <Link href="/" className="flex items-center gap-2" aria-label="HiddenHire home">
      <svg width="28" height="28" viewBox="0 0 32 32" aria-hidden="true">
        <rect width="32" height="32" rx="8" fill={tile} />
        <circle cx="14.5" cy="14.5" r="6" fill="none" stroke={mark} strokeWidth="2.6" />
        <path d="M19 19l5 5" stroke={mark} strokeWidth="2.6" strokeLinecap="round" />
        <path d="M14.5 11.5v6M11.5 14.5h6" stroke={mark} strokeWidth="1.8" strokeLinecap="round" />
      </svg>
      <span className={`text-[17px] font-semibold tracking-tight ${dark ? "text-white" : "text-ink"}`}>
        HiddenHire
      </span>
    </Link>
  );
}
