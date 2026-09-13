# Build record

## Review and authority

The release baseline was an empty repository on `main`, with no tracked files,
commits, or remote heads. The full eleven-part REV-002 specification was read
in order and reviewed before creating project files. Source materials remain
private and are not part of this repository.

Reviewer: Codex, GPT-6 / OpenAI. Review completed 2026-09-05T13:53:38Z.
Exact deployed model revision is unavailable. This is a fresh-context review,
not independent validation; the reviewer subsequently becomes the builder.
The owner accepted this limitation and both architectural decisions.

One contract conflict was identified: an accepted indivisible protected token
could exceed the draft-item capacity. The owner then instructed the builder
to correct identified mistakes and proceed. The applied correction sets the
item text ceiling to 10,000 Unicode code points, retaining the 10,000-code-point
input and 20,000-code-point total draft ceilings. This allows exact preservation
of every valid input, including long URLs. No source documents were modified.

Review verdict: **PASS with the owner-authorized item-capacity correction**.
No remaining critical/high specification defect was identified. Runtime and
semantic correctness remain subjects of implementation verification.

## Evidence discipline

Checkpoint evidence is recorded as checks finish. No paid provider call, account
creation, secret insertion, repository visibility change, or public deployment
is claimed by this record. Dependencies, test tools, and caches are confined to
this repository.
The frozen benchmark must precede formatter implementation. Same-model dataset
authorship and semantic review are disclosed and cannot establish independence.

## Completion receipt — 2026-09-12

The REV-002 local release-candidate scope is implemented. This completion does
not claim a public deployment, live-provider quality, independent validation, or
production latency. Those activities remain operator-gated as documented in the
deployment and privacy guides.

Implemented completion work:

- The editable Next.js workspace covers note entry, built-in and custom styles,
  request cancellation, stale-result protection, regeneration confirmation,
  item editing/moving/adding/deleting, section and full-copy serialization,
  clipboard recovery, preference reset, privacy disclosure, and safe errors.
- The optional Sync Orb is lazy, client-only, WebGL-gated, reduced-motion aware,
  hidden from assistive technology, and unable to block the text workflow. Both
  enabled and disabled production builds were profiled.
- The FastAPI service provides strict request/response models, deterministic
  source-preserving fallback, the disabled-by-default structured provider
  boundary, common output validation, timeouts, bounded concurrency/queueing,
  circuit breaking, rate limiting, exact CORS, safe logging, and health probes.
- API, privacy, architecture, content, deployment, container, generated OpenAPI,
  evaluation, dependency-lock, and CI documentation/artifacts are present.

Local verification evidence:

- Backend format, lint, strict typing, OpenAPI drift, and **76 tests passed**;
  measured application coverage was **89%** on Windows/Python 3.14.7.
- Frontend formatting, lint, strict typing, contract drift, dependency audit, and
  production build passed. **12/12 Playwright scenarios passed** in Chromium,
  including axe, keyboard, CSP, 320-pixel reflow, and the real no-key API flow.
- Vitest could not execute on this Windows host because Application Control
  blocks Rolldown's native test binding. This is an environment limitation, not
  recorded as a pass; the Linux CI job remains the required component-test gate.
- The frozen evaluation ran 72 cases with zero automated failures. A fresh,
  explicitly non-independent semantic review covered all 69 valid outputs and
  passed the declared factuality/placement gates. The report conclusion is
  **demonstrated** for the local deterministic formatter only.
- Client-visible performance profiling recorded **240/240 successful runs** for
  250, 1,500, and 10,000-code-point inputs across warm/cold process conditions
  with the orb enabled and disabled. Observed p95 was 125–219 ms; failure rate
  was zero and fallback rate was 100%. This does not authorize a public speed
  claim.
- npm audit, pip-audit, source/workflow inspection, actionlint, gitleaks, and
  Trivy filesystem/misconfiguration scans passed with no unresolved high or
  critical finding. The gitleaks configuration narrowly excludes generated
  evaluation metadata files whose SHA-256 source map triggered the generic-key
  heuristic; source and all other artifacts remain scanned.

Deferred verification:

- This host has no usable Docker/Podman/WSL runtime, so the non-root Linux image
  build, runtime smoke test, and image scan are delegated to the committed CI.
- Live-provider calls, provider account/region/retention verification, public
  deployment, and deployed latency remain intentionally unrun and are not part
  of the no-credential local release acceptance boundary.

## Frontend and public-release hardening — 2026-09-14

The existing editorial layout, responsive behavior, and motion language were
preserved. Release work was limited to production packaging, health checks,
verification coverage, and public-contribution documentation.

- The production frontend build, formatting, lint, strict typing, contract check,
  and dependency audit passed on the pinned toolchain.
- **14/14 Vitest tests passed** locally. **16/16 Playwright scenarios passed**,
  including the real no-key API flow, axe, keyboard access, strict CSP, 320-pixel
  reflow, five responsive viewports, no-WebGL fallback, and opt-in interactive 3D.
- The final optimized desktop Lighthouse run scored **99 performance**, **100
  accessibility**, **100 best practices**, and **100 SEO**. Local synthetic audit
  scores are evidence for this build, not guarantees for a future public host.
- The web service now emits a standalone Next.js artifact and has a non-root
  multi-stage container plus an uncached `/api/health` endpoint. CI builds and
  smoke-tests both service images with read-only filesystems before image scans.
- Contribution, vulnerability-reporting, pull-request, and sanitized bug-report
  guidance are included. No open-source license or public visibility change was
  selected on the owner's behalf.
