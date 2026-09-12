# Deployment and rollback

This repository is prepared for two deployment units: a dynamic Next.js server
and one CPU-only FastAPI instance. No host, account, paid service or public
deployment was created. Live provider and deployed performance are unverified.

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

From the repository root, build `services/api/Dockerfile` with its service folder
as context. Both Python and build-tool images are digest-pinned. Inspect the final
image user, health check and SBOM, scan for vulnerabilities, then start it with
read-only filesystem, dropped capabilities, no-new-privileges and bounded CPU/RAM.
Exercise liveness, readiness and no-key generation against that container.

This Windows build host lacks Docker/Podman and a working WSL distribution.
The supplied CI performs the Linux container build and checks; a local static
Dockerfile review is not a container runtime pass. No CI execution is claimed
until the owner pushes and observes its results.

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
