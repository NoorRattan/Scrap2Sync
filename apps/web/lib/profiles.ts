import { SECTIONS, type StyleProfile } from "./types";

export const MAX_NOTES = 10_000;
export const codePointLength = (value: string) => Array.from(value).length;
export const normalizeNotes = (value: string) =>
  value.replace(/\r\n?/g, "\n").trim();
const commonHeaders = {
  yesterday: "Yesterday",
  today: "Today",
  blockers: "Blockers",
};
export const BUILTIN_PROFILES: readonly StyleProfile[] = [
  {
    id: "concise-bullets",
    label: "Concise bullets",
    layout: "bullets",
    verbosity: "brief",
    tone: "direct",
    headers: commonHeaders,
    preferredMaxItemsPerSection: 5,
  },
  {
    id: "standard-update",
    label: "Standard update",
    layout: "bullets",
    verbosity: "standard",
    tone: "neutral-professional",
    headers: commonHeaders,
    preferredMaxItemsPerSection: 8,
  },
  {
    id: "async-detail",
    label: "Async detail",
    layout: "paragraphs",
    verbosity: "standard",
    tone: "neutral-professional",
    headers: { yesterday: "Completed", today: "Next", blockers: "Blockers" },
    preferredMaxItemsPerSection: 8,
  },
];
export const DEFAULT_PROFILE = BUILTIN_PROFILES[1];
export const CUSTOM_PROFILE: StyleProfile = {
  ...DEFAULT_PROFILE,
  id: "custom",
  label: "Custom",
};

export function hasProhibitedControls(value: string, multiline = true) {
  return Array.from(value).some(
    (char) =>
      (/\p{Cc}|\p{Cs}/u.test(char) &&
        !(multiline && (char === "\n" || char === "\t"))) ||
      /[\u202a-\u202e\u2066-\u2069]/u.test(char),
  );
}

export function notesError(value: string): string | null {
  const normalized = normalizeNotes(value);
  if (!normalized) return "Enter at least one non-whitespace character.";
  if (codePointLength(normalized) > MAX_NOTES)
    return "Use no more than 10,000 characters. Your notes have not been shortened.";
  if (hasProhibitedControls(normalized))
    return "Remove unsupported control characters from your notes.";
  return null;
}

export function plainLabelError(value: string, maximum: number) {
  if (
    !value.trim() ||
    value !== value.trim() ||
    codePointLength(value) > maximum
  )
    return `Use 1–${maximum} characters, without spaces at the beginning or end.`;
  if (hasProhibitedControls(value, false) || /[<>]|\{\{|\}\}|\$\{/u.test(value))
    return "Use a plain-text label without markup or template expressions.";
  return null;
}

export function profileErrors(profile: StyleProfile): Record<string, string[]> {
  const errors: Record<string, string[]> = {};
  const label = plainLabelError(profile.label, 40);
  if (label) errors["styleProfile.label"] = [label];
  for (const section of SECTIONS) {
    const message = plainLabelError(profile.headers[section], 30);
    if (message) errors[`styleProfile.headers.${section}`] = [message];
  }
  return errors;
}

export function validStoredProfile(value: unknown): value is StyleProfile {
  if (!value || typeof value !== "object" || Array.isArray(value)) return false;
  const p = value as Record<string, unknown>;
  if (
    Object.keys(p).sort().join() !==
    [
      "id",
      "label",
      "layout",
      "verbosity",
      "tone",
      "headers",
      "preferredMaxItemsPerSection",
    ]
      .sort()
      .join()
  )
    return false;
  if (
    !["concise-bullets", "standard-update", "async-detail", "custom"].includes(
      String(p.id),
    ) ||
    typeof p.label !== "string" ||
    !["bullets", "paragraphs"].includes(String(p.layout)) ||
    !["brief", "standard"].includes(String(p.verbosity)) ||
    !["direct", "neutral-professional"].includes(String(p.tone)) ||
    !Number.isInteger(p.preferredMaxItemsPerSection) ||
    Number(p.preferredMaxItemsPerSection) < 1 ||
    Number(p.preferredMaxItemsPerSection) > 10
  )
    return false;
  if (!p.headers || typeof p.headers !== "object" || Array.isArray(p.headers))
    return false;
  const headers = p.headers as Record<string, unknown>;
  if (
    Object.keys(headers).sort().join() !== [...SECTIONS].sort().join() ||
    SECTIONS.some((section) => typeof headers[section] !== "string")
  )
    return false;
  const profile = value as StyleProfile;
  if (Object.keys(profileErrors(profile)).length) return false;
  if (profile.id === "custom") return true;
  const builtIn = BUILTIN_PROFILES.find((item) => item.id === profile.id);
  return (
    !!builtIn &&
    profile.label === builtIn.label &&
    profile.layout === builtIn.layout &&
    profile.verbosity === builtIn.verbosity &&
    profile.tone === builtIn.tone &&
    profile.preferredMaxItemsPerSection ===
      builtIn.preferredMaxItemsPerSection &&
    SECTIONS.every(
      (section) => profile.headers[section] === builtIn.headers[section],
    )
  );
}
