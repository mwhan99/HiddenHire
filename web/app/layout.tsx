import type { Metadata } from "next";
import { Inter } from "next/font/google";

import { SiteFooter } from "@/components/SiteFooter";

import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const DESCRIPTION =
  "HiddenHire tracks the career pages of emerging New York startups every week " +
  "and ranks openings by your fit and each company's hiring momentum.";

export const metadata: Metadata = {
  title: {
    default: "HiddenHire · NYC startup hiring signals",
    template: "%s · HiddenHire",
  },
  description: DESCRIPTION,
  openGraph: {
    title: "HiddenHire · NYC startup hiring signals",
    description: DESCRIPTION,
    type: "website",
  },
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${inter.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col font-sans">
        <div className="flex-1">{children}</div>
        <SiteFooter />
      </body>
    </html>
  );
}
