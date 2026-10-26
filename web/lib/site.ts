import type { Metadata } from "next";

// The site's public address, used for link previews, the sitemap, and
// robots.txt. Set a SITE_URL environment variable to change it (for
// example after adding a custom domain); on your Mac it's localhost.
export const PRODUCTION_URL = "https://hiddenhire-nyc.vercel.app";

export const SITE_URL = process.env.SITE_URL
  ? process.env.SITE_URL.replace(/\/$/, "")
  : process.env.VERCEL
    ? PRODUCTION_URL
    : "http://localhost:3000";

export const SITE_NAME = "HiddenHire";

// The shared preview picture (app/opengraph-image.tsx).
const PREVIEW_IMAGE = {
  url: "/opengraph-image",
  width: 1200,
  height: 630,
  alt: "HiddenHire: find the New York startups hiring for you, before everyone else",
};

// Title, description, and matching link-preview text for one page.
// Next.js merges metadata shallowly, so a page that sets `openGraph`
// replaces the layout's entirely, including the image; this keeps the
// shared fields (and the picture) on every page.
export function pageMetadata(title: string, description: string): Metadata {
  const full = `${title} · ${SITE_NAME}`;
  return {
    title,
    description,
    openGraph: { title: full, description, type: "website", siteName: SITE_NAME, images: [PREVIEW_IMAGE] },
    twitter: { card: "summary_large_image", title: full, description, images: [PREVIEW_IMAGE.url] },
  };
}
