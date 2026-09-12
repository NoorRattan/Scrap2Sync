import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTypescript from "eslint-config-next/typescript";

export default defineConfig([
  ...nextVitals,
  ...nextTypescript,
  globalIgnores([
    ".next/**",
    ".next-no-orb/**",
    "coverage/**",
    "playwright-report/**",
    "test-results/**",
    "lib/generated.ts",
    "next-env.d.ts",
  ]),
]);
