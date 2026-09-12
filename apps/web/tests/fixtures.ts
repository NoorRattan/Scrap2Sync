import type { GenerateResponse } from "@/lib/types";

export const TEST_REQUEST_ID = "aa000000-0000-4000-8000-000000000001";
export function result(clientRequestId = TEST_REQUEST_ID): GenerateResponse {
  return {
    draft: {
      yesterday: [
        {
          itemId: "D001",
          text: "Finished AX-14.",
          sourceFragmentIds: ["F001"],
        },
      ],
      today: [
        {
          itemId: "D002",
          text: "Plan to verify v2.4.",
          sourceFragmentIds: ["F002"],
        },
      ],
      blockers: [],
    },
    engineVersion: "rules-fallback-v1",
    warnings: [
      {
        warningId: "W001",
        code: "FALLBACK_USED",
        message:
          "The AI formatter is unavailable. This draft uses conservative rules and preserves your original wording. Review the sections before copying.",
        section: null,
        itemId: null,
        sourceFragmentIds: [],
      },
      {
        warningId: "W002",
        code: "UNCERTAIN_SECTION",
        message: "Review the section for this source note.",
        section: "today",
        itemId: "D002",
        sourceFragmentIds: ["F002"],
      },
    ],
    durationMs: 8,
    requestId: TEST_REQUEST_ID,
    clientRequestId,
  };
}
