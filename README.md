# Scrap2Sync

[![Release verification](https://github.com/NoorRattan/Scrap2Sync/actions/workflows/ci.yml/badge.svg)](https://github.com/NoorRattan/Scrap2Sync/actions/workflows/ci.yml)

**Less noise. More signal.**

Turn rough developer notes into an editable standup draft. Organize Yesterday,
Today and Blockers, review the wording, move or edit items, then copy plain text
in your chosen format. English-dominant notes are the evaluated scope.

The local reference runs without credentials through `rules-fallback-v1`.
The optional OpenAI adapter is disabled by default. There are no accounts,
databases, saved notes, analytics, voice or automatic posting integrations.

**[Try the live demo](https://scrap2sync-web.onrender.com/)** ·
[Setup](#install) · [Deployment](#deploy) · [Contributing](CONTRIBUTING.md)

## What you can do

- Paste rough notes and organize them into Yesterday, Today, and Blockers.
- Choose concise bullets, a standard update, async detail, or a custom style.
- Review and edit the draft, move items between sections, and copy individual
  sections or the complete update as plain text.
- Use the app without signing up or supplying an API key. The default engine
  uses conservative rules; the optional OpenAI integration is off by default.
- Explore the animated green sculpture and optional interactive 3D view, with
  reduced-motion controls for a calmer experience.

Notes are not saved by the app and clear when you reload or leave. Keep a copy
of anything you need, and review every draft before sharing it. See the
[privacy guide](docs/PRIVACY.md) for processing details.

## Project structure

- `apps/web` — Next.js, React, and TypeScript frontend; Three.js / React Three
  Fiber power the optional 3D experience.
- `services/api` — FastAPI backend, validation, rules-based generation, and the
  optional provider adapter.
- `evaluation` — frozen evaluation examples, rubric, and evaluator.
- `docs` — architecture, API contract, privacy, and deployment guidance.
- `scripts` — local startup and verification helpers.

## Install

Use Node **24.20.0**, npm **11.19.0**, Python **3.14.7**, and uv **0.12.10**.
Versions and primary sources are recorded in [architecture](docs/ARCHITECTURE.md).
The initial builder's tools/caches are ignored and confined to this checkout.

```sh
cd services/api
uv sync --frozen
cd ../../apps/web
npm ci
npm run build
```

On this Windows checkout, `scripts/env.ps1` selects the already-provisioned local
Node runtime and repository-local caches. The API's Python environment is already
under `services/api/.venv`. For a fresh machine, install the pinned runtimes first
and use the locked commands above. Do not force incompatible peer dependencies.

## Run locally

Start the API and frontend in separate terminals from the repository root:

```powershell
.\scripts\start.ps1 -Service api
```

```powershell
.\scripts\start.ps1 -Service web
```

Open [Scrap2Sync](http://localhost:3000). Its API is at localhost:8000.
For macOS/Linux, run the equivalent API command from `services/api`:

```sh
uv run --frozen uvicorn app.main:app --host localhost --port 8000 --no-access-log --no-proxy-headers
```

Run `npm run start` from `apps/web` for the production frontend. This is the
tested local path with strict CSP. Environment defaults already enable fallback;
there is no need to create an `.env` file. The example environment lists available
settings. Set environment variables explicitly in each process if overriding.

## Verify

From `services/api`:

```sh
uv run --frozen ruff format --check app tests
uv run --frozen ruff check app tests
uv run --frozen mypy app
uv run --frozen python -m pytest --cov=app --cov-report=term-missing
uv run --frozen python -m app.export_openapi --check
uv run --frozen pip-audit
```

From `apps/web`:

```sh
npm run format:check
npm run lint
npm run typecheck
npm run contract:check
npm run test:coverage
npm run build
npx --no-install playwright install chromium
npm run test:e2e
npm audit --audit-level=high
```

Keep the no-key API running for browser integration scenarios. Playwright starts
the production frontend itself unless `PLAYWRIGHT_EXTERNAL_SERVER=true`.
On Windows, first dot-source `scripts/env.ps1` from the repository root so the
browser installer and tests share the repository-local browser path.

The frozen dataset and rubric are described in [evaluation](evaluation/README.md).
Run the evaluator with the API environment's Python from the repository root:

```sh
services/api/.venv/bin/python evaluation/evaluate.py
```

On Windows use `services/api/.venv/Scripts/python.exe`. The report distinguishes
automatic checks, semantic reviewer scores and unrun live-model quality.

`scripts/fetch_tools.py` provisions checksum-pinned source/workflow scanners.
CI includes explicit browser scenarios, dependency/secret/workflow checks, SBOMs
and non-root Linux container verification. Local evidence and unrun checks are
recorded in [build record](docs/BUILD_RECORD.md) and generated reports.

## Deploy

The public preview is hosted on Render:

- **Website:** [scrap2sync-web.onrender.com](https://scrap2sync-web.onrender.com/)
- **API readiness:** [scrap2sync-api.onrender.com/api/v1/health/ready](https://scrap2sync-api.onrender.com/api/v1/health/ready)

The free services can sleep when idle, so the first visit or generation request
may take longer while they wake up. This is a no-key preview with the OpenAI
adapter disabled, not a hardened production deployment. Its API currently uses
the development environment profile; follow the production guidance below
before using it for a production workload. Avoid submitting sensitive notes to
the public demo.

The frontend can run as a dynamic Next.js service or from its production
container. Build its image with the real public API origin baked into the client:

```sh
docker build --build-arg NEXT_PUBLIC_API_BASE_URL=https://api.example.com -t scrap2sync-web apps/web
docker build -t scrap2sync-api services/api
```

The web and API images run as non-root users and expose health checks at
`/api/health`, `/api/v1/health/live`, and `/api/v1/health/ready`. The frontend
must remain dynamically rendered because its CSP uses a per-request nonce.
Follow the [deployment guide](docs/DEPLOYMENT.md) for production variables,
origin policy, verification, and rollback.

## Contracts, privacy and operations

- [API contract](docs/API.md) and generated [OpenAPI](docs/openapi.json).
- [Privacy and external processing](docs/PRIVACY.md).
- [Deployment, enablement gates and rollback](docs/DEPLOYMENT.md).
- [Content and interaction guide](docs/CONTENT_GUIDE.md).
- [Contributing](CONTRIBUTING.md), [community conduct](CODE_OF_CONDUCT.md), and
  [security reporting](SECURITY.md).

Notes accept up to 10,000 Unicode code points without truncation. The approved
item-capacity correction allows a single item to preserve that entire input;
total draft text remains bounded at 20,000 code points. Style item counts are
preferences, so preserving facts takes precedence. Outputs remain drafts and
require review. Local benchmark or timing evidence does not establish independent
validation, live-provider quality, universal accessibility or deployed speed.

## License

No open-source license has been granted. Public availability of this repository
does not by itself grant permission to copy, modify, or redistribute the work.
The repository owner should add an explicit license before accepting reuse.
