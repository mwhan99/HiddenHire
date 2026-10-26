// The site's public address, used for link previews, the sitemap, and
// robots.txt. Vercel sets VERCEL_PROJECT_PRODUCTION_URL automatically (it
// becomes the custom domain once one is added). SITE_URL overrides it.
export const SITE_URL = process.env.SITE_URL
  ? process.env.SITE_URL.replace(/\/$/, "")
  : process.env.VERCEL_PROJECT_PRODUCTION_URL
    ? `https://${process.env.VERCEL_PROJECT_PRODUCTION_URL}`
    : "http://localhost:3000";
