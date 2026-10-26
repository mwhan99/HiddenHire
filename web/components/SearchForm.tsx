import Form from "next/form";

import { FAMILY_LABELS, FAMILY_ORDER, ROLE_FAMILIES } from "@/lib/scoring/match";
import type { SearchProfile } from "@/lib/scoring/types";

import { SubmitButton } from "./SubmitButton";

// The search form. It submits to /search as ordinary URL values
// (?role=...&level=...), so every search has its own shareable link, and
// it works without JavaScript. Role chips are real checkboxes styled as
// buttons.

const LEVELS = [
  { value: "entry", label: "Entry level / internship" },
  { value: "mid", label: "Mid level" },
  { value: "senior", label: "Senior" },
];

const ROLE_LABEL_WORDS: Record<string, string> = { "fp&a": "FP&A", ml: "ML", ai: "AI" };

const SMALL_WORDS = new Set(["and", "of", "&"]);

// "fp&a" -> "FP&A", "strategy and operations" -> "Strategy and Operations".
export function roleLabel(role: string) {
  return role
    .split(" ")
    .map((word, index) =>
      ROLE_LABEL_WORDS[word] ?? (index > 0 && SMALL_WORDS.has(word) ? word : word.charAt(0).toUpperCase() + word.slice(1)),
    )
    .join(" ");
}

// "marketing and growth" -> "Marketing and growth".
function sentenceCase(text: string) {
  return text.charAt(0).toUpperCase() + text.slice(1);
}

export function levelLabel(level: string) {
  return LEVELS.find((option) => option.value === level)?.label ?? LEVELS[0].label;
}

export function SearchForm({ profile, open }: { profile: SearchProfile; open: boolean }) {
  const chosen = new Set(profile.target_roles);
  // A role can sit in two families (e.g. product operations); show it once.
  const shown = new Set<string>();

  return (
    <details open={open} className="group rounded-2xl border border-slate-200 bg-white shadow-[0_12px_40px_-20px_rgba(11,27,58,0.25)]">
      <summary className="flex cursor-pointer list-none flex-wrap items-center justify-between gap-3 p-5">
        <div className="min-w-0">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-500">Your search</div>
          <div className="mt-1 font-medium">
            {profile.target_roles.length ? profile.target_roles.map(roleLabel).join(", ") : "No roles chosen"}
          </div>
          <div className="mt-0.5 text-sm text-slate-500">
            {[levelLabel(profile.experience_level), profile.location || "Any location", profile.skills.length ? `${profile.skills.length} skills` : null]
              .filter(Boolean)
              .join(" · ")}
          </div>
        </div>
        <span className="rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white">
          <span className="group-open:hidden">Edit search</span>
          <span className="hidden group-open:inline">Close</span>
        </span>
      </summary>

      <Form action="/search" className="border-t border-slate-100 p-5">
        <fieldset>
          <legend className="font-semibold">Target roles</legend>
          <p className="text-sm text-slate-500">
            Pick one or more. Similar titles in the same family are included automatically.
          </p>
          <div className="mt-4 space-y-4">
            {FAMILY_ORDER.map((family) => {
              const roles = ROLE_FAMILIES[family].filter((role) => !shown.has(role));
              roles.forEach((role) => shown.add(role));
              if (roles.length === 0) return null;
              return (
                <div key={family} className="grid gap-2 sm:grid-cols-[170px_1fr] sm:gap-4">
                  <div className="pt-1.5 text-sm font-medium text-slate-600">{sentenceCase(FAMILY_LABELS[family])}</div>
                  <div className="flex flex-wrap gap-2">
                    {roles.map((role) => (
                      <label key={role} className="cursor-pointer">
                        <input type="checkbox" name="role" value={role} defaultChecked={chosen.has(role)} className="peer sr-only" />
                        <span className="inline-block rounded-full border border-slate-200 px-3 py-1.5 text-sm text-slate-700 transition-colors peer-checked:border-brand peer-checked:bg-brand peer-checked:text-white peer-focus-visible:ring-2 peer-focus-visible:ring-blue-300 hover:border-slate-300">
                          {roleLabel(role)}
                        </span>
                      </label>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </fieldset>

        <div className="mt-6 grid gap-5 border-t border-slate-100 pt-6 md:grid-cols-2">
          <fieldset>
            <legend className="text-sm font-semibold">Experience level</legend>
            <div className="mt-2 flex flex-wrap gap-2">
              {LEVELS.map((level) => (
                <label key={level.value} className="cursor-pointer">
                  <input type="radio" name="level" value={level.value} defaultChecked={profile.experience_level === level.value} className="peer sr-only" />
                  <span className="inline-block rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 transition-colors peer-checked:border-brand peer-checked:bg-blue-50 peer-checked:font-semibold peer-checked:text-brand peer-focus-visible:ring-2 peer-focus-visible:ring-blue-300">
                    {level.label}
                  </span>
                </label>
              ))}
            </div>
          </fieldset>
          <Field name="location" label="Preferred location" defaultValue={profile.location} placeholder="New York" />
          <Field name="skills" label="Skills" hint="Separate with commas" defaultValue={profile.skills.join(", ")} placeholder="SQL, Excel, Tableau, Python" />
          <Field name="industries" label="Preferred industries" hint="Separate with commas" defaultValue={profile.industries.join(", ")} placeholder="fintech, AI, enterprise software" />
        </div>

        <SubmitButton />
      </Form>
    </details>
  );
}

function Field({
  name,
  label,
  hint,
  defaultValue,
  placeholder,
}: {
  name: string;
  label: string;
  hint?: string;
  defaultValue: string;
  placeholder: string;
}) {
  return (
    <label className="block">
      <span className="text-sm font-semibold">{label}</span>
      {hint && <span className="ml-2 text-xs text-slate-500">{hint}</span>}
      <input
        name={name}
        defaultValue={defaultValue}
        placeholder={placeholder}
        className="mt-2 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-ink placeholder:text-slate-400 focus:border-brand focus:outline-none focus:ring-2 focus:ring-blue-200"
      />
    </label>
  );
}
