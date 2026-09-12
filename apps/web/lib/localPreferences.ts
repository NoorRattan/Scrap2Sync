import { DEFAULT_PROFILE, validStoredProfile } from "./profiles";
import type { StyleProfile } from "./types";

export const PREFERENCE_KEY = "scrap2sync.preferences.v1";
export type Preferences = {
  profile: StyleProfile;
  reducedMotion: boolean;
  onboardingDismissed: boolean;
};
export const DEFAULT_PREFERENCES: Preferences = {
  profile: DEFAULT_PROFILE,
  reducedMotion: false,
  onboardingDismissed: false,
};
let current = DEFAULT_PREFERENCES;
let initialized = false;
const listeners = new Set<() => void>();

export function parsePreferences(raw: string | null): Preferences {
  try {
    const value: unknown = raw ? JSON.parse(raw) : null;
    if (!value || typeof value !== "object" || Array.isArray(value))
      return DEFAULT_PREFERENCES;
    const p = value as Record<string, unknown>;
    if (
      Object.keys(p).sort().join() !==
        ["profile", "reducedMotion", "onboardingDismissed"].sort().join() ||
      !validStoredProfile(p.profile) ||
      typeof p.reducedMotion !== "boolean" ||
      typeof p.onboardingDismissed !== "boolean"
    )
      return DEFAULT_PREFERENCES;
    return {
      profile: p.profile,
      reducedMotion: p.reducedMotion,
      onboardingDismissed: p.onboardingDismissed,
    };
  } catch {
    return DEFAULT_PREFERENCES;
  }
}

export function getPreferences(): Preferences {
  if (!initialized && typeof window !== "undefined") {
    initialized = true;
    try {
      current = parsePreferences(window.localStorage.getItem(PREFERENCE_KEY));
    } catch {
      current = DEFAULT_PREFERENCES;
    }
  }
  return current;
}
export const getServerPreferences = () => DEFAULT_PREFERENCES;
export function subscribePreferences(listener: () => void) {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}
export function savePreferences(preferences: Preferences) {
  if (!validStoredProfile(preferences.profile)) return;
  current = {
    profile: preferences.profile,
    reducedMotion: preferences.reducedMotion,
    onboardingDismissed: preferences.onboardingDismissed,
  };
  initialized = true;
  try {
    window.localStorage.setItem(PREFERENCE_KEY, JSON.stringify(current));
  } catch {
    /* Preferences remain usable in page memory. */
  }
  listeners.forEach((listener) => listener());
}
export function resetPreferences() {
  current = DEFAULT_PREFERENCES;
  initialized = true;
  try {
    window.localStorage.removeItem(PREFERENCE_KEY);
  } catch {
    /* Storage may be unavailable. */
  }
  listeners.forEach((listener) => listener());
}
