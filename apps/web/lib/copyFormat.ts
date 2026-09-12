import {
  SECTIONS,
  type LocalDraft,
  type Section,
  type StyleProfile,
} from "./types";

export const sectionPlaceholder = (section: Section) =>
  section === "blockers" ? "No blockers stated." : "Not specified.";

export function copySection(
  draft: LocalDraft,
  profile: StyleProfile,
  section: Section,
) {
  const texts = draft[section].length
    ? draft[section].map((item) => item.text.replace(/\r\n?/g, "\n").trim())
    : [sectionPlaceholder(section)];
  return `${profile.headers[section]}\n${texts.map((text) => (profile.layout === "bullets" ? `- ${text}` : text)).join("\n")}`;
}

export function copyAll(draft: LocalDraft, profile: StyleProfile) {
  return SECTIONS.map((section) => copySection(draft, profile, section)).join(
    "\n\n",
  );
}

export function draftEditError(draft: LocalDraft) {
  const items = SECTIONS.flatMap((section) => draft[section]);
  if (items.some((item) => !item.text.trim()))
    return "Write something in each item, or delete empty items, before copying.";
  if (items.some((item) => Array.from(item.text.trim()).length > 10_000))
    return "Keep each item within 10,000 characters before copying.";
  if (
    items.reduce(
      (total, item) => total + Array.from(item.text.trim()).length,
      0,
    ) > 20_000
  )
    return "Keep the complete draft within 20,000 characters before copying.";
  return null;
}
