# API contract

Scrap2Sync exposes a small JSON API. The generated, authoritative schema is
[`openapi.json`](openapi.json); this guide summarizes the public behavior.

## Generate a draft

`POST /api/v1/generate`

Send `Content-Type: application/json` with:

- `rawNotes`: 1–10,000 normalized Unicode code points.
- `styleProfile`: a built-in or custom structured profile containing its ID,
  label, layout, verbosity, tone, three headings and preferred item count.
- `clientRequestId`: a caller-generated UUID used to reject duplicate active
  requests and discard stale browser responses.

A successful `200` response contains three arrays under `draft` (`yesterday`,
`today`, and `blockers`), the formatter engine version, review warnings, bounded
duration in milliseconds, a server request ID, and the echoed client request ID.
Each draft item has a stable item ID, text, and one or more source-fragment IDs.

The service never returns placeholder items for empty sections. The web client
adds `Not specified.` and `No blockers stated.` only when serializing text for
copying.

## Errors

Errors use one safe envelope:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Check the highlighted fields and try again.",
    "requestId": "00000000-0000-4000-8000-000000000000",
    "clientRequestId": null,
    "fieldErrors": {}
  }
}
```

Possible statuses are `400`, `409`, `413`, `415`, `422`, `429`, `500`, and
`503`. A `429` response includes `Retry-After`. Error messages and operational
logs never include submitted notes, generated drafts, provider responses,
credentials, or client identifiers.

## Health

- `GET /api/v1/health/live` reports process liveness.
- `GET /api/v1/health/ready` reports whether safe generation is available and
  whether the optional primary formatter is unconfigured, configured, available,
  degraded, or circuit-open.

Readiness can remain healthy when the external provider is unavailable because
the deterministic formatter is the safe fallback.

## Transport and storage

Generation responses use `Cache-Control: no-store`. Browser credentials are not
accepted, allowed origins are exact, and the default installation permits only
the local frontend origin. The API processes content in memory and has no account,
database, history, analytics, or automatic posting integration.
