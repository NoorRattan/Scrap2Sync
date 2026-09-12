import type { components } from "./generated";

export type StyleProfile = components["schemas"]["StyleProfile"];
export type DraftItem = components["schemas"]["DraftItem"];
export type StandupDraft = components["schemas"]["StandupDraft"];
export type GenerationWarning = components["schemas"]["GenerationWarning"];
export type GenerateRequest = components["schemas"]["GenerateRequest"];
export type GenerateResponse = components["schemas"]["GenerateResponse"];
export type Section = "yesterday" | "today" | "blockers";
export const SECTIONS: readonly Section[] = ["yesterday", "today", "blockers"];
export type LocalItem = DraftItem & { userEdited?: boolean };
export type LocalDraft = Record<Section, LocalItem[]>;
export type PrimaryStatus =
  "unconfigured" | "configured" | "available" | "degraded" | "circuit_open";
