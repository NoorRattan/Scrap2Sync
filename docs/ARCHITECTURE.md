# Architecture

Scrap2Sync separates its Next.js App Router interface from an in-memory FastAPI
formatter service. The browser submits typed notes and a structured profile,
then receives editable source-mapped items. It persists only optional preferences.
The service validates before and after formatting. A disabled, unavailable, or
unsafe external formatter uses the conservative deterministic formatter.

## Selected toolchain

Versions resolved on 2026-09-05 using official compatibility documentation and
maintainer-published package registry metadata. Direct dependencies use exact
versions; package-lock.json and uv.lock resolve transitive dependencies.

| Component                                           | Selected version                 | Compatibility/source                                                                                                                              |
| --------------------------------------------------- | -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| Node.js / npm                                       | 24.20.0 / 11.19.0                | [Official release index](https://nodejs.org/dist/index.json), [LTS policy](https://nodejs.org/en/about/previous-releases)                         |
| Next.js                                             | 16.3.4                           | [Installation and Node minimum](https://nextjs.org/docs/app/getting-started/installation)                                                         |
| React / React DOM                                   | 19.2.8                           | [Published package](https://registry.npmjs.org/react/19.2.8)                                                                                      |
| React Three Fiber / Three.js                        | 9.7.0 / 0.185.1                  | [React 19 compatibility](https://r3f.docs.pmnd.rs/tutorials/v9-migration-guide)                                                                   |
| Drei / React Three postprocessing                   | 10.7.8 / 3.1.1                   | Runtime helpers, environment lighting, and GPU postprocessing for the opt-in 3D scene                                                             |
| Framer Motion / GSAP / Lenis                        | 13.2.0 / 3.15.0 / 1.3.26         | Interface motion, sequenced reveals, and accessible smooth scrolling                                                                              |
| Lucide React                                        | 1.45.0                           | Tree-shaken interface icon components                                                                                                             |
| Manrope Variable / Instrument Serif                 | 5.3.0 / 5.3.0                    | Self-hosted font packages; no third-party font request at runtime                                                                                 |
| TypeScript                                          | 5.9.3                            | [Official release documentation](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-9.html); openapi-typescript requires 5.x |
| Tailwind CSS / PostCSS integration                  | 4.3.3                            | [Next.js integration](https://tailwindcss.com/docs/installation/framework-guides/nextjs)                                                          |
| PostCSS                                             | 8.5.28                           | [Maintainer release metadata](https://registry.npmjs.org/postcss/8.5.28)                                                                          |
| Radix Dialog                                        | 1.1.23                           | [Maintainer release metadata](https://registry.npmjs.org/@radix-ui/react-dialog/1.1.23)                                                           |
| ESLint / Next configuration                         | 9.39.5 / 16.3.4                  | [React plugin peer compatibility](https://registry.npmjs.org/eslint-plugin-react); ESLint 10 is outside its peer range                            |
| Prettier                                            | 3.9.6                            | [Maintainer release metadata](https://registry.npmjs.org/prettier/3.9.6)                                                                          |
| Vitest / coverage-v8                                | 5.0.0                            | [Maintainer release metadata](https://registry.npmjs.org/vitest/5.0.0)                                                                            |
| Testing Library React / DOM / user-event / jest-dom | 16.3.3 / 10.4.1 / 14.6.7 / 7.0.1 | [Official project](https://testing-library.com/docs/react-testing-library/intro/)                                                                 |
| jsdom                                               | 30.0.1                           | [Maintainer release metadata](https://registry.npmjs.org/jsdom/30.0.1)                                                                            |
| Playwright / axe integration                        | 1.63.0 / 4.13.0                  | [Playwright tests](https://playwright.dev/docs/intro), [accessibility tests](https://playwright.dev/docs/accessibility-testing)                   |
| openapi-typescript                                  | 7.13.0                           | [Maintainer release metadata](https://registry.npmjs.org/openapi-typescript/7.13.0)                                                               |
| Python                                              | 3.14.7                           | [Official Python release](https://www.python.org/downloads/release/python-3147/)                                                                  |
| FastAPI / Pydantic                                  | 0.141.1 / 2.13.5                 | [FastAPI release notes](https://fastapi.tiangolo.com/release-notes/), [Pydantic metadata](https://pypi.org/pypi/pydantic/2.13.5/json)             |
| httpx / Uvicorn / uv                                | 0.28.1 / 0.52.4 / 0.12.10        | [HTTPX](https://www.python-httpx.org/), [uv locked sync](https://docs.astral.sh/uv/concepts/projects/sync/)                                       |

All remaining development and typing package versions are recorded in the locks.
Python 3.14 support is documented in FastAPI's release notes. The selected React
renderer belongs to the React 19 generation. No peer overrides are authorized.

## Browser security and rendering

Dynamic pages receive a fresh per-request CSP nonce. The proxy forwards that
nonce and CSP to Next.js so framework hydration scripts carry the same nonce.
Production requires no eval permission or external scripts. See the
[official nonce integration](https://nextjs.org/docs/app/guides/content-security-policy).
All input, output, labels and edits render as text or form values.

## Provider boundary

The adapter targets the fixed official HTTPS Responses endpoint with no tools,
strict JSON Schema output and `store: false`. No model alias is supplied by the
application. An operator must verify and configure an exact supported model,
privacy terms, region and cost controls before enabling it. See
[Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs)
and [data controls](https://developers.openai.com/api/docs/guides/your-data).
Schema checks do not prove semantic truth; users review drafts before copying.

## Local environment

Build host: Windows 11 Home Single Language 10.0.26200, AMD Ryzen AI 9 HX 370,
24 logical processors. Node 24.20.0 is provisioned inside the ignored local tools
directory; the preinstalled Node 24.19.0 is not modified. Python 3.14.7 is installed.
Docker, Podman and a working WSL distribution are unavailable. Linux image build
and runtime evidence must therefore come from the supplied CI or a later machine;
local static inspection is never represented as a successful container build.

Accessibility checks use the [W3C WCAG 2.2 reference](https://www.w3.org/WAI/WCAG22/quickref/):
text and control contrast, keyboard operation, names/roles/values, focus visibility,
status announcements, 200% resizing and 320 CSS-pixel reflow. Browser automation
does not replace manual assistive-technology evidence.
