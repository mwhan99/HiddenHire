import config from "./config.json";

// Whole-word matching and role families, mirroring candidate_fit.py.
// config.json is generated from the Python code by scripts/export_golden.py.

export type Family = keyof typeof config.role_families;
export const ROLE_FAMILIES = config.role_families as Record<Family, string[]>;
export const FAMILY_ORDER = Object.keys(ROLE_FAMILIES) as Family[];
export const ROLE_EXCLUSIONS: string[] = config.role_exclusions;
export const SUPPORTED_ROLES: string[] = config.supported_roles;
export const FAMILY_LABELS = config.family_labels as Record<Family, string>;

function escapeRegExp(text: string) {
  return text.replace(/[.*+?^${}()|[\]\\-]/g, "\\$&");
}

const patterns = new Map<string, RegExp>();

// True when `term` appears in `text` as a whole word or phrase: "excel"
// does not match "excellent", "ai" does not match "supply chain". Terms
// may contain spaces or symbols ("fp&a", "c++"). Case is ignored.
export function containsTerm(text: string | null | undefined, term: string | null | undefined): boolean {
  if (text == null || term == null) return false;
  const needle = String(term).trim().toLowerCase();
  if (!needle) return false;
  let pattern = patterns.get(needle);
  if (!pattern) {
    pattern = new RegExp(`(?<![a-z0-9])${escapeRegExp(needle)}(?![a-z0-9])`);
    patterns.set(needle, pattern);
  }
  return pattern.test(String(text).toLowerCase());
}

// The role families a list of target roles belongs to, in family order
// for each role (candidate_fit.find_role_families).
export function findRoleFamilies(targetRoles: string[]): Family[] {
  const families: Family[] = [];
  for (const role of targetRoles) {
    const lower = role.toLowerCase();
    for (const family of FAMILY_ORDER) {
      if (ROLE_FAMILIES[family].includes(lower) && !families.includes(family)) {
        families.push(family);
      }
    }
  }
  return families;
}

export function isExcludedTitle(title: string | null | undefined): boolean {
  return ROLE_EXCLUSIONS.some((exclusion) => containsTerm(title, exclusion));
}

// 100 when one of the target roles appears in the title as a whole phrase.
export function roleMatch(title: string | null | undefined, targetRoles: string[]): number {
  if (title == null) return 0;
  if (isExcludedTitle(title)) return 0;
  return targetRoles.some((role) => containsTerm(title, role)) ? 100 : 0;
}

// 75 when the title belongs to one of the given families.
export function familyMatch(title: string | null | undefined, families: Family[]): number {
  if (title == null) return 0;
  if (isExcludedTitle(title)) return 0;
  return families.some((family) => ROLE_FAMILIES[family].some((phrase) => containsTerm(title, phrase))) ? 75 : 0;
}
