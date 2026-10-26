import { cacheLife } from "next/cache";
import { ImageResponse } from "next/og";

// The picture shown when a HiddenHire link is shared (LinkedIn, Slack,
// iMessage, email). Pages without their own image use this one.

export const alt = "HiddenHire: find the New York startups hiring for you, before everyone else";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

const BRAND = "HiddenHire";
const EYEBROW = "Weekly hiring signals from emerging New York startups";
const LINE_1 = "Find the startups hiring for you,";
const LINE_2 = "before everyone else.";
const FOOTER = ["Candidate Fit", "Hiring Momentum", "Updated every Monday"];

// Fetch Inter from Google Fonts, limited to the letters this image uses
// (a few KB). If that fails, the image falls back to the built-in font.
// Cached, so the image is built once instead of on every request.
async function inter(weight: 400 | 700, text: string) {
  "use cache";
  cacheLife("max");
  try {
    const css = await (
      await fetch(`https://fonts.googleapis.com/css2?family=Inter:wght@${weight}&text=${encodeURIComponent(text)}`)
    ).text();
    const url = css.match(/src: url\((.+?)\) format\('(?:opentype|truetype)'\)/)?.[1];
    if (!url) return null;
    const response = await fetch(url);
    return response.ok ? { name: "Inter", data: await response.arrayBuffer(), weight, style: "normal" as const } : null;
  } catch {
    return null;
  }
}

export default async function OpenGraphImage() {
  const fonts = (
    await Promise.all([inter(700, BRAND + LINE_1 + LINE_2), inter(400, EYEBROW + FOOTER.join("·"))])
  ).filter((font) => font !== null);

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          padding: "72px 80px",
          color: "white",
          fontFamily: "Inter",
          backgroundColor: "#0b1b3a",
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.06) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.06) 1px, transparent 1px), linear-gradient(135deg, #0b1b3a 0%, #102a5c 100%)",
          backgroundSize: "48px 48px, 48px 48px, 100% 100%",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
          <svg width="56" height="56" viewBox="0 0 32 32">
            <rect width="32" height="32" rx="8" fill="#ffffff" />
            <circle cx="14.5" cy="14.5" r="6" fill="none" stroke="#2563eb" strokeWidth="2.6" />
            <path d="M19 19l5 5" stroke="#2563eb" strokeWidth="2.6" strokeLinecap="round" />
            <path d="M14.5 11.5v6M11.5 14.5h6" stroke="#2563eb" strokeWidth="1.8" strokeLinecap="round" />
          </svg>
          <div style={{ fontSize: 40, fontWeight: 700, letterSpacing: -1 }}>{BRAND}</div>
        </div>

        <div style={{ display: "flex", flexDirection: "column" }}>
          <div style={{ fontSize: 30, color: "#93c5fd", marginBottom: 22 }}>{EYEBROW}</div>
          <div style={{ fontSize: 70, fontWeight: 700, lineHeight: 1.1, letterSpacing: -2 }}>{LINE_1}</div>
          <div style={{ fontSize: 70, fontWeight: 700, lineHeight: 1.1, letterSpacing: -2, color: "#93c5fd" }}>{LINE_2}</div>
        </div>

        <div style={{ display: "flex", gap: 16, fontSize: 26, color: "#cbd5e1" }}>
          {FOOTER.map((item, index) => (
            <div key={item} style={{ display: "flex", gap: 16 }}>
              {index > 0 && <span style={{ color: "#64748b" }}>·</span>}
              <span>{item}</span>
            </div>
          ))}
        </div>
      </div>
    ),
    { ...size, fonts },
  );
}
