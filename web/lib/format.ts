// Small display helpers shared by every page.

export function fmt(value: number) {
  return value.toLocaleString("en-US");
}

// "+17", "−3" (a real minus sign), or "0".
export function signed(value: number) {
  return `${value > 0 ? "+" : value < 0 ? "−" : ""}${fmt(Math.abs(value))}`;
}

// Snapshot dates arrive as "2026-10-19" or "2026-10-19T00:00:00". Only the
// day matters, so read it at noon UTC to avoid time-zone shifts.
function toDate(value: string) {
  return new Date(`${value.slice(0, 10)}T12:00:00Z`);
}

// "Oct 19"
export function shortDate(value: string) {
  return toDate(value).toLocaleDateString("en-US", { month: "short", day: "numeric", timeZone: "UTC" });
}

// "Oct 19, 2026"
export function longDate(value: string) {
  return toDate(value).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC",
  });
}

// The Monday after a snapshot date, when the next weekly update runs.
export function nextMonday(value: string) {
  const date = toDate(value);
  const daysAhead = ((8 - date.getUTCDay()) % 7) || 7;
  date.setUTCDate(date.getUTCDate() + daysAhead);
  return date.toISOString().slice(0, 10);
}

// "AI / FinTech / SaaS" -> "AI · FinTech" (the first two industry tags).
export function shortIndustry(industry: string | null) {
  if (!industry) return "";
  return industry
    .split("/")
    .map((tag) => tag.trim())
    .filter(Boolean)
    .slice(0, 2)
    .join(" · ");
}
