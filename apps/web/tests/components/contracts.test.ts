import { describe, expect, it, vi } from "vitest";
import {
  ApiError,
  generateDraft,
  retryAfterDate,
  validResponse,
} from "@/lib/apiClient";
import { copyAll, copySection, draftEditError } from "@/lib/copyFormat";
import {
  DEFAULT_PREFERENCES,
  parsePreferences,
  PREFERENCE_KEY,
  resetPreferences,
  savePreferences,
} from "@/lib/localPreferences";
import {
  BUILTIN_PROFILES,
  CUSTOM_PROFILE,
  DEFAULT_PROFILE,
  notesError,
  validStoredProfile,
} from "@/lib/profiles";
import { result } from "../fixtures";

describe("canonical inputs, safe preferences, and clipboard contracts", () => {
  it("counts Unicode code points and preserves valid markup without silent truncation", () => {
    expect(notesError("😀".repeat(10_000))).toBeNull();
    expect(notesError("😀".repeat(10_001))).toContain("not been shortened");
    expect(notesError("\r\n \t ")).toContain("non-whitespace");
    expect(notesError("<Button disabled>\r\nAX-14")).toBeNull();
    expect(notesError("hidden\u202evalue")).toContain("control");
  });
  it("keeps all exact built-in profiles and rejects altered profiles or hidden preference data", () => {
    for (const profile of BUILTIN_PROFILES)
      expect(validStoredProfile(profile)).toBe(true);
    expect(validStoredProfile({ ...DEFAULT_PROFILE, label: "Changed" })).toBe(
      false,
    );
    expect(validStoredProfile({ ...CUSTOM_PROFILE, label: "<script>" })).toBe(
      false,
    );
    expect(parsePreferences('{"invalid":true}')).toBe(DEFAULT_PREFERENCES);
    expect(parsePreferences("broken")).toBe(DEFAULT_PREFERENCES);
    expect(
      parsePreferences(
        JSON.stringify({ ...DEFAULT_PREFERENCES, rawNotes: "PRIVATE-NOTES" }),
      ),
    ).toBe(DEFAULT_PREFERENCES);
    expect(parsePreferences(JSON.stringify(DEFAULT_PREFERENCES))).toEqual(
      DEFAULT_PREFERENCES,
    );
  });
  it("writes only approved preference keys and handles blocked or quota-full storage", () => {
    const write = vi.spyOn(Storage.prototype, "setItem");
    savePreferences(DEFAULT_PREFERENCES);
    expect(write).toHaveBeenCalledWith(
      PREFERENCE_KEY,
      JSON.stringify(DEFAULT_PREFERENCES),
    );
    expect(Object.keys(JSON.parse(write.mock.calls[0][1])).sort()).toEqual([
      "onboardingDismissed",
      "profile",
      "reducedMotion",
    ]);
    write.mockImplementation(() => {
      throw new DOMException("Quota exceeded");
    });
    expect(() => savePreferences(DEFAULT_PREFERENCES)).not.toThrow();
    vi.spyOn(Storage.prototype, "removeItem").mockImplementation(() => {
      throw new Error("blocked");
    });
    expect(() => resetPreferences()).not.toThrow();
  });
  it("serializes current edits, exact headers, LF paragraphs, and empty placeholders", () => {
    const draft = result().draft;
    expect(copyAll(draft, BUILTIN_PROFILES[0])).toBe(
      "Yesterday\n- Finished AX-14.\n\nToday\n- Plan to verify v2.4.\n\nBlockers\n- No blockers stated.",
    );
    expect(copySection(draft, BUILTIN_PROFILES[2], "yesterday")).toBe(
      "Completed\nFinished AX-14.",
    );
    draft.today[0].text = "Edited\r\nsecond line";
    expect(copyAll(draft, BUILTIN_PROFILES[2])).toContain(
      "Next\nEdited\nsecond line",
    );
    expect(
      copyAll({ yesterday: [], today: [], blockers: [] }, DEFAULT_PROFILE),
    ).toBe(
      "Yesterday\n- Not specified.\n\nToday\n- Not specified.\n\nBlockers\n- No blockers stated.",
    );
    expect(
      draftEditError({ ...draft, today: [{ ...draft.today[0], text: "" }] }),
    ).toContain("delete empty items");
  });
});

describe("untrusted response and retry handling", () => {
  it("validates complete responses, 10,000-character items, and warning references", () => {
    expect(validResponse(result())).toBe(true);
    const valid = result();
    valid.draft.yesterday[0].text = "😀".repeat(10_000);
    expect(validResponse(valid)).toBe(true);
    valid.draft.yesterday[0].text += "x";
    expect(validResponse(valid)).toBe(false);
    const malformed = result();
    malformed.warnings[1].itemId = "D999";
    expect(validResponse(malformed)).toBe(false);
    expect(validResponse({ ...result(), injected: "bad" })).toBe(false);
  });
  it("accepts delta seconds and dates for Retry-After", () => {
    expect(retryAfterDate("3", 1000)).toBe(4000);
    expect(retryAfterDate("Thu, 01 Jan 1970 00:00:05 GMT", 1000)).toBe(5000);
    expect(retryAfterDate("invalid", 1000)).toBeNull();
  });
  it("rejects unsafe responses and never retries failed requests automatically", async () => {
    const request = {
      rawNotes: "Finished AX-14.",
      styleProfile: DEFAULT_PROFILE,
      clientRequestId: result().clientRequestId,
    };
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          error: {
            code: "RATE_LIMITED",
            message: "PRIVATE-SERVER-PAYLOAD",
            requestId: result().requestId,
            fieldErrors: {},
          },
        }),
        { status: 429, headers: { "Retry-After": "2" } },
      ),
    );
    const failure = await generateDraft(
      request,
      new AbortController().signal,
    ).catch((error: unknown) => error);
    expect(failure).toBeInstanceOf(ApiError);
    expect((failure as ApiError).message).not.toContain("PRIVATE");
    expect((failure as ApiError).retryAt).toBeGreaterThan(Date.now());
    expect(fetchMock).toHaveBeenCalledTimes(1);
    fetchMock.mockResolvedValue(
      new Response(JSON.stringify({ draft: {} }), { status: 200 }),
    );
    await expect(
      generateDraft(request, new AbortController().signal),
    ).rejects.toThrow("safely read");
  });
});
