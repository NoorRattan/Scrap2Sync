# Scrap2Sync

Turn rough developer notes into an editable standup draft. Organize Yesterday,
Today and Blockers, review the wording, move or edit items, then copy plain text
in your chosen format. English-dominant notes are the evaluated scope.

The local reference runs without credentials through `rules-fallback-v1`.
The optional OpenAI adapter is disabled by default. There are no accounts,
databases, saved notes, analytics, voice or automatic posting integrations.

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
uv run --frozen pytest --cov=app --cov-report=term-missing
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
recorded in [build record](docs/BUILD_RECORD.md) and generated reports. Nothing is
committed or deployed automatically.

## Contracts, privacy and operations

- [API contract](docs/API.md) and generated [OpenAPI](docs/openapi.json).
- [Privacy and external processing](docs/PRIVACY.md).
- [Deployment, enablement gates and rollback](docs/DEPLOYMENT.md).
- [Content and interaction guide](docs/CONTENT_GUIDE.md).

Notes accept up to 10,000 Unicode code points without truncation. The approved
item-capacity correction allows a single item to preserve that entire input;
total draft text remains bounded at 20,000 code points. Style item counts are
preferences, so preserving facts takes precedence. Outputs remain drafts and
require review. Local benchmark or timing evidence does not establish independent
validation, live-provider quality, universal accessibility or deployed speed.
