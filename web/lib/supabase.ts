import { createClient } from "@supabase/supabase-js";

// Reads from Supabase with the publishable (read-only) key.
//
// The two settings come from web/.env.local on your Mac and from the
// project's Environment Variables on Vercel. They have no NEXT_PUBLIC_
// prefix, so Next.js keeps them on the server and never sends them to
// a visitor's browser. The tables are read-only for this key anyway
// (see supabase/schema.sql).
export function supabase() {
  const url = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_PUBLISHABLE_KEY;
  if (!url || !key) {
    throw new Error(
      "SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY are not set. " +
        "Add them to web/.env.local (or to Vercel's Environment Variables).",
    );
  }
  return createClient(url, key, {
    // The website never signs anyone in, so there is no session to keep.
    auth: { persistSession: false, autoRefreshToken: false },
  });
}
