# Contributing to Scrap2Sync

Thanks for helping improve Scrap2Sync. Contributions should preserve its core
promise: private-by-default note processing, source-faithful drafts, accessible
interaction, and an intentionally crafted interface.

## Before opening a change

1. Search existing issues and pull requests for related work.
2. Open an issue before making a large product, architecture, dependency, or
   visual-direction change.
3. Keep pull requests focused. Do not combine unrelated refactors or formatting.
4. Never commit real notes, API keys, credentials, production URLs, or private
   evaluation source material.

## Local setup

Use the exact runtime versions in `.nvmrc`, `.npmrc`, `.python-version`, and
`services/api/uv.lock`. Install with the locked commands in `README.md`; do not
force peer dependencies or regenerate lockfiles without explaining why.

Run the API and web application in separate terminals:

```powershell
.\scripts\start.ps1 -Service api
.\scripts\start.ps1 -Service web
```

## Required verification

Before submitting a pull request, run the relevant checks from `README.md`. A
frontend change must pass formatting, lint, type checking, component coverage,
the production build, and browser scenarios. A backend change must pass format,
lint, strict typing, tests with coverage, OpenAPI drift, and dependency audit.

Changes to the API contract must regenerate and commit `docs/openapi.json` and
the frontend client types. Changes to output behavior must also update the frozen
evaluation evidence when applicable.

## Product and security guardrails

- Preserve CSP nonces, strict origin validation, text-only rendering, request
  limits, output validation, and safe logging.
- Keep the external formatter disabled by default. Provider enablement requires
  the documented privacy, model, cost, and operational approvals.
- Maintain keyboard access, visible focus, reduced-motion behavior, 320-pixel
  reflow, and the text workflow when WebGL or clipboard access is unavailable.
- Do not add persistence, telemetry, accounts, automatic posting, or third-party
  processing without an explicit product and privacy decision.
- Visual changes should extend the existing typography, spacing, color, depth,
  and motion system instead of introducing generic component patterns.

## Pull requests

Explain the user outcome, risk, validation performed, screenshots for visual
changes, and any deployment or rollback impact. CI must pass. Reviewers may ask
for smaller commits or additional evidence when security, privacy, accessibility,
or source preservation could regress.
