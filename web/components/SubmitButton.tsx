"use client";

import { useFormStatus } from "react-dom";

// The search button. It says "Finding matches…" from the moment the form
// is sent, even before the loading page appears.
export function SubmitButton() {
  const { pending } = useFormStatus();
  return (
    <button
      type="submit"
      disabled={pending}
      className="mt-6 inline-flex items-center gap-2 rounded-lg bg-brand px-5 py-3 font-semibold text-white transition-colors hover:bg-blue-500 disabled:cursor-wait disabled:opacity-80"
    >
      {pending && (
        <span aria-hidden="true" className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />
      )}
      {pending ? "Finding matches…" : "Find my matches →"}
    </button>
  );
}
