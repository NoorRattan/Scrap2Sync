import type { NextConfig } from "next";

const configuredOrigin =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const api = new URL(configuredOrigin);
const loopback = ["localhost", "127.0.0.1", "[::1]"].includes(api.hostname);
if (
  api.origin !== configuredOrigin ||
  api.username ||
  api.password ||
  (api.protocol !== "https:" && !(api.protocol === "http:" && loopback))
) {
  throw new Error(
    "NEXT_PUBLIC_API_BASE_URL must be an exact HTTPS or local loopback origin.",
  );
}

const nextConfig: NextConfig = {
  output: "standalone",
  distDir:
    process.env.BUILD_OUTPUT_DIR === ".next-no-orb" ? ".next-no-orb" : ".next",
  poweredByHeader: false,
  generateEtags: false,
  reactStrictMode: true,
  productionBrowserSourceMaps: false,
  env: {
    NEXT_PUBLIC_API_BASE_URL: configuredOrigin,
    NEXT_PUBLIC_ENABLE_SYNC_ORB:
      process.env.NEXT_PUBLIC_ENABLE_SYNC_ORB ?? "true",
  },
};

export default nextConfig;
