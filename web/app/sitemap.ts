import type { MetadataRoute } from "next";

import { getLatestMomentum } from "@/lib/data";
import { SITE_URL } from "@/lib/site";

// Lists every page for search engines, including one per company.
export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const companies = await getLatestMomentum();
  const pages = ["", "/search", "/companies", "/insights", "/methodology"].map((path) => ({
    url: `${SITE_URL}${path}`,
    changeFrequency: "weekly" as const,
    priority: path === "" ? 1 : 0.8,
  }));
  return [
    ...pages,
    ...companies.map((company) => ({
      url: `${SITE_URL}/companies/${company.company_id}`,
      changeFrequency: "weekly" as const,
      priority: 0.5,
    })),
  ];
}
