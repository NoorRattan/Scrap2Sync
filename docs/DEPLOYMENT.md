# Deployment and rollback

This repository is prepared for two deployment units: a dynamic Next.js server
and one CPU-only FastAPI instance. Both have production containers, non-root
runtime users, internal health checks, locked dependencies, and CI build gates.
No host, account, paid service or public deployment was created. Live provider
and deployed performance are unverified.

## Local reference

Use Node 24.20.0, npm 11.19.0, Python 3.14.7 and uv 0.12.10. The UI binds to
localhost:3000 and the API to localhost:8000. Run the production frontend build
for the tested CSP/hydration path. `FORMATTER_PROVIDER=disabled` is the default.
Follow README for install, run and verification commands.

## Host requirements and configuration

1. Select a Node host supporting dynamic requests and a non-root CPU Linux
   container host for the API. Do not use static export: nonce-bearing pages
   require per-request rendering. Keep the two units close to reduce latency.
2. Terminate verified HTTPS at trusted gateways. Configure exact HTTPS frontend
   origins, the public API origin, minimal methods/headers and no credentials.
   HTTP is allowed only for local loopback development.
3. Set production mode and explicitly choose trusted proxy count/topology. Strip
   incoming forwarding headers at the public edge; append only trusted proxy
   addresses. Start Uvicorn without automatic forwarded-header trust.
4. Choose rate, active concurrency and queue limits from measured capacity. The
   local defaults are not a capacity claim. Deploy one worker and one instance;
   scaling requires shared atomic admission controls and a new operational design.
5. Keep the provider disabled unless its exact model and privacy controls are
   verified and published. Use the backend secret manager only for its API key.
   No key or model default belongs in client configuration.
6. Record an owner-approved monthly provider ceiling, provider-side quotas,
   alerts, budget approver and emergency disable procedure. Set verification
   flags only after completing the underlying checks. Do not deploy with an
   unresolved applicable critical/high supply-chain finding.

## Deployment sequence

1. Deploy the API from `services/api/Dockerfile`. Set `ENVIRONMENT=production`,
   `FORMATTER_PROVIDER=disabled`, the exact HTTPS `ALLOWED_ORIGINS`, and an
   explicitly reviewed `TRUSTED_PROXY_COUNT`. Leave every verification flag false
   until its named check is complete.
2. Verify API liveness and readiness through the public HTTPS route. Confirm an
   untrusted origin is rejected and request bodies do not appear in platform logs.
3. Deploy the frontend from `apps/web/Dockerfile`, passing the exact public API
   origin as the `NEXT_PUBLIC_API_BASE_URL` build argument. That value is baked
   into the browser bundle and must not contain credentials or a path.
4. Route HTTPS traffic to frontend port 3000 and API port 8000. Do not rewrite the
   frontend into a static site; dynamic requests create the CSP nonce.
5. Exercise `/api/health`, the no-key generation flow, editing, section movement,
   copy fallback, keyboard navigation, mobile reflow, reduced motion, and the
   opt-in 3D scene from the deployed origin before enabling public traffic.

A platform-native Next.js deployment may use `apps/web` as its project root and
the same public build-time variable. A container host should build each Dockerfile
with its service directory as context. Keep preview and production origins
separate and list each exact frontend origin in the corresponding API environment.

## Security policy and health

The selected browser policy uses a new cryptographic nonce per dynamic request.
Verify hydration, API calls and lazy orb loading under that policy on the actual
host. No broad script origins or eval permission are needed for production.
The HTTPS gateway adds HSTS only after HTTPS verification. Preserve nosniff,
Referrer-Policy, frame denial and the restrictive Permissions Policy.

Liveness is `/api/v1/health/live`; readiness is `/api/v1/health/ready`. Readiness
may remain healthy while the primary formatter is unconfigured or degraded,
because deterministic fallback is available. Neither probe calls a paid model.
Rate/concurrency rejections use 429 and Retry-After; inability to produce any safe
draft uses 503. Never cache generation responses or log their bodies.

## Container verification

From the repository root, build each Dockerfile with its service folder as
context. The API's Python and build-tool images are digest-pinned; the frontend
uses an exact Node patch and Alpine release. Inspect each final image user and
health check, generate SBOMs, and scan for vulnerabilities. Start with read-only
filesystems, a small writable `/tmp`, dropped capabilities, no-new-privileges and
bounded CPU/RAM. Exercise web health plus API liveness, readiness, and no-key
generation against those containers.

This Windows build host lacks Docker/Podman and a working WSL distribution.
The supplied CI performs both Linux container builds, non-root/read-only runtime
smoke checks, and image scans. A local static Dockerfile review is not a container
runtime pass; observe the hosted CI result before promoting a revision.

## Disable, release and rollback

The emergency provider switch is `FORMATTER_PROVIDER=disabled`; restart the API
and verify readiness and deterministic generation. Rotate a compromised backend
key using the secret manager, never a frontend variable or Git change.

Publish immutable image digests and the matching frontend build together with
the generated API contract and evaluation report. Keep the preceding tested
pair. On failure, stop new traffic, restore that pair and its non-secret
configuration, re-run health and no-key smoke checks, and reopen traffic only
after evidence is recorded. There is no database migration or saved content to
restore. Avoid dumping request bodies during incident diagnosis.

## Post-deployment evidence

Test exact origins, TLS, proxy spoof rejection, CSP, log redaction, limits,
clipboard flow and no browser content persistence. Run credentialed provider
smoke only with owner authorization. Deployed latency claims require at least
100 representative successful requests with client region/network, exact model,
host cold starts, concurrency and cost; local/stub timings cannot support a
public three-second claim. Record monitoring access and bounded-log retention.
