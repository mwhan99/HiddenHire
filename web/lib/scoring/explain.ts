import { matchedIndustries } from "./fit";
import { FAMILY_LABELS, containsTerm, findRoleFamilies, isExcludedTitle, roleMatch, ROLE_FAMILIES } from "./match";
import type { RankedOpportunity, SearchProfile } from "./types";

// "Why this opportunity?", mirroring explain_opportunity in app.py. It only
// mentions signals the scores actually support.

export function joinPhrases(items: string[]) {
  const kept = items.filter(Boolean);
  if (kept.length === 0) return "";
  if (kept.length === 1) return kept[0];
  if (kept.length === 2) return `${kept[0]} and ${kept[1]}`;
  return `${kept.slice(0, -1).join(", ")}, and ${kept[kept.length - 1]}`;
}

function matchedFamilyLabels(title: string, targetRoles: string[]) {
  if (isExcludedTitle(title)) return [];
  return findRoleFamilies(targetRoles.map((role) => role.toLowerCase()))
    .filter((family) => ROLE_FAMILIES[family].some((phrase) => containsTerm(title, phrase)))
    .map((family) => FAMILY_LABELS[family]);
}

export function explainOpportunity(row: RankedOpportunity, profile: SearchProfile) {
  const title = row.job_title ?? "";
  const industryText = row.industry ?? "";
  const targetRoles = profile.target_roles ?? [];
  const preferredLocation = profile.location ?? "";

  let rolePhrase = "";
  const exactRoles = targetRoles.filter((role) => role && roleMatch(title, [role]) > 0);
  if (exactRoles.length) {
    rolePhrase = `your target ${joinPhrases(exactRoles)} ${exactRoles.length === 1 ? "role" : "roles"}`;
  } else {
    const familyLabels = matchedFamilyLabels(title, targetRoles);
    if (familyLabels.length) rolePhrase = `your target ${joinPhrases(familyLabels)} roles`;
    else if (row.family_match > 0) rolePhrase = "your target roles";
  }

  let industryPhrase = "";
  const industryHits = matchedIndustries(industryText, (profile.industries ?? []).filter(Boolean));
  if (row.industry_match > 0 && industryHits.length) {
    industryPhrase = `your preferred ${joinPhrases(industryHits)} ${industryHits.length === 1 ? "industry" : "industries"}`;
  }

  let skillPhrase = "";
  if (row.skill_match >= 100) skillPhrase = "your listed skills in the posting";
  else if (row.skill_match > 0) skillPhrase = "some of your listed skills in the posting";

  let locationPhrase = "";
  if (row.location_match >= 100 && preferredLocation) {
    locationPhrase = `a location that fits your ${preferredLocation} preference`;
  } else if (row.location_match >= 75) {
    locationPhrase = "a remote posting that may still fit your location preference";
  }

  const fitPoints = [rolePhrase, industryPhrase].filter(Boolean);
  let extraPoints = [skillPhrase, locationPhrase].filter(Boolean);
  // Keep the card to the strongest supported signals.
  if (fitPoints.length >= 2 && extraPoints.length > 1) extraPoints = extraPoints.slice(0, 1);

  let fitSentence =
    fitPoints.length >= 2
      ? `Strong match for ${joinPhrases(fitPoints)}`
      : fitPoints.length === 1
        ? `This role lines up with ${fitPoints[0]}`
        : "This opening matches part of your search";
  if (extraPoints.length) fitSentence += `, with ${joinPhrases(extraPoints)}`;
  fitSentence += ".";

  const momentum = row.hiring_momentum_score;
  const momentumSentence =
    momentum == null
      ? "Hiring activity for this company is not available in the current data."
      : momentum >= 60
        ? "The company's current hiring activity makes this an opportunity worth exploring now."
        : momentum >= 45
          ? "Hiring activity looks steady compared with the other companies in this search."
          : "Hiring activity is quieter than the other companies in this search.";

  return `${fitSentence} ${momentumSentence}`;
}

// The badge on a result card, using the same bands as the sentence.
export function momentumBand(score: number | null) {
  if (score == null) return { label: "Momentum n/a", tone: "neutral" as const };
  if (score >= 60) return { label: "Hiring fast", tone: "up" as const };
  if (score >= 45) return { label: "Steady hiring", tone: "neutral" as const };
  return { label: "Quieter hiring", tone: "down" as const };
}
