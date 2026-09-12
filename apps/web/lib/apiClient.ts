import { codePointLength, hasProhibitedControls } from "./profiles";
import {
  SECTIONS,
  type GenerateRequest,
  type GenerateResponse,
  type PrimaryStatus,
} from "./types";

const API_ORIGIN =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const warningCodes = new Set([
  "FALLBACK_USED",
  "UNCERTAIN_SECTION",
  "POSSIBLE_FACT_OMISSION",
  "PROFILE_LIMIT_EXCEEDED",
  "LANGUAGE_NOT_EVALUATED",
]);
const messages: Record<string, string> = {
  VALIDATION_ERROR: "Check the highlighted fields and try again.",
  REQUEST_IN_PROGRESS:
    "This request is already being processed. Wait a moment before submitting again.",
  RATE_LIMITED: "There have been too many requests. Wait before trying again.",
  SERVICE_UNAVAILABLE: "A safe draft could not be created. Please try again.",
  PAYLOAD_TOO_LARGE:
    "This request is too large. Shorten your notes or style labels and try again.",
  MALFORMED_JSON: "The request could not be read. Please try again.",
  UNSUPPORTED_MEDIA_TYPE:
    "The request format could not be read. Please try again.",
  INTERNAL_ERROR:
    "Something went wrong while creating your draft. Please try again.",
};

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status = 0,
    public readonly requestId: string | null = null,
    public readonly fieldErrors: Record<string, string[]> = {},
    public readonly retryAt: number | null = null,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function record(value: unknown): value is Record<string, unknown> {
  return !!value && typeof value === "object" && !Array.isArray(value);
}
function exactKeys(value: Record<string, unknown>, keys: string[]) {
  return Object.keys(value).sort().join() === keys.sort().join();
}
function stringIds(value: unknown, minimum = 0): value is string[] {
  return (
    Array.isArray(value) &&
    value.length >= minimum &&
    value.length <= 256 &&
    value.every((id) => typeof id === "string" && /^F\d{3,6}$/.test(id))
  );
}

export function validResponse(value: unknown): value is GenerateResponse {
  if (
    !record(value) ||
    !exactKeys(value, [
      "draft",
      "engineVersion",
      "warnings",
      "durationMs",
      "requestId",
      "clientRequestId",
    ]) ||
    !record(value.draft) ||
    !exactKeys(value.draft, [...SECTIONS]) ||
    !["structured-llm-v1", "rules-fallback-v1"].includes(
      String(value.engineVersion),
    ) ||
    !Number.isInteger(value.durationMs) ||
    Number(value.durationMs) < 0 ||
    typeof value.requestId !== "string" ||
    !uuid.test(value.requestId) ||
    typeof value.clientRequestId !== "string" ||
    !uuid.test(value.clientRequestId) ||
    !Array.isArray(value.warnings) ||
    value.warnings.length > 512
  )
    return false;
  const items = new Set<string>();
  let characters = 0;
  for (const section of SECTIONS) {
    const sectionItems = value.draft[section];
    if (!Array.isArray(sectionItems) || sectionItems.length > 256) return false;
    for (const item of sectionItems) {
      if (
        !record(item) ||
        !exactKeys(item, ["itemId", "text", "sourceFragmentIds"]) ||
        typeof item.itemId !== "string" ||
        !/^D\d{3,6}$/.test(item.itemId) ||
        items.has(item.itemId) ||
        typeof item.text !== "string" ||
        !item.text.trim() ||
        item.text !== item.text.trim() ||
        hasProhibitedControls(item.text) ||
        codePointLength(item.text) > 10_000 ||
        ["Not specified.", "No blockers stated."].includes(item.text) ||
        !stringIds(item.sourceFragmentIds, 1)
      )
        return false;
      items.add(item.itemId);
      characters += codePointLength(item.text);
    }
  }
  if (characters > 20_000) return false;
  const warnings = new Set<string>();
  for (const warning of value.warnings) {
    if (
      !record(warning) ||
      !exactKeys(warning, [
        "warningId",
        "code",
        "message",
        "section",
        "itemId",
        "sourceFragmentIds",
      ]) ||
      typeof warning.warningId !== "string" ||
      !/^W\d{3,6}$/.test(warning.warningId) ||
      warnings.has(warning.warningId) ||
      !warningCodes.has(String(warning.code)) ||
      typeof warning.message !== "string" ||
      !warning.message.trim() ||
      codePointLength(warning.message) > 300 ||
      hasProhibitedControls(warning.message) ||
      (warning.section !== null &&
        !SECTIONS.includes(warning.section as never)) ||
      (warning.itemId !== null &&
        (typeof warning.itemId !== "string" || !items.has(warning.itemId))) ||
      !stringIds(warning.sourceFragmentIds)
    )
      return false;
    warnings.add(warning.warningId);
  }
  return true;
}

export function retryAfterDate(
  value: string | null,
  now = Date.now(),
): number | null {
  if (!value) return null;
  if (/^\d+$/.test(value)) return now + Number(value) * 1000;
  const time = Date.parse(value);
  return Number.isFinite(time) ? Math.max(now, time) : null;
}

export async function generateDraft(
  request: GenerateRequest,
  signal: AbortSignal,
): Promise<GenerateResponse> {
  const response = await fetch(`${API_ORIGIN}/api/v1/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
    signal,
    cache: "no-store",
    credentials: "omit",
  });
  const body: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const error = record(body) && record(body.error) ? body.error : {};
    const fields: Record<string, string[]> = {};
    if (record(error.fieldErrors)) {
      for (const [key, value] of Object.entries(error.fieldErrors)) {
        if (
          /^(rawNotes|styleProfile(?:\.(label|layout|verbosity|tone|preferredMaxItemsPerSection|headers\.(yesterday|today|blockers)))?)$/.test(
            key,
          ) &&
          Array.isArray(value)
        ) {
          fields[key] = value.filter(
            (message): message is string =>
              typeof message === "string" &&
              message.length < 300 &&
              !hasProhibitedControls(message),
          );
        }
      }
    }
    throw new ApiError(
      messages[String(error.code)] ??
        "The request could not finish. Please try again.",
      response.status,
      typeof error.requestId === "string" && uuid.test(error.requestId)
        ? error.requestId
        : null,
      fields,
      retryAfterDate(response.headers.get("Retry-After")),
    );
  }
  if (!validResponse(body) || body.clientRequestId !== request.clientRequestId)
    throw new ApiError(
      "The response could not be safely read. Your existing draft has been kept.",
    );
  return body;
}

export async function getPrimaryStatus(
  signal: AbortSignal,
): Promise<PrimaryStatus | "unknown"> {
  try {
    const response = await fetch(`${API_ORIGIN}/api/v1/health/ready`, {
      signal,
      cache: "no-store",
      credentials: "omit",
    });
    const body: unknown = await response.json();
    const statuses = [
      "unconfigured",
      "configured",
      "available",
      "degraded",
      "circuit_open",
    ];
    return response.ok &&
      record(body) &&
      statuses.includes(String(body.primaryFormatter))
      ? (body.primaryFormatter as PrimaryStatus)
      : "unknown";
  } catch {
    return "unknown";
  }
}
