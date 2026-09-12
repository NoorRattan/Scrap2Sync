import { spawn } from "node:child_process";
import { once } from "node:events";
import { readFile, readdir, mkdir, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { gzipSync } from "node:zlib";
import { chromium } from "@playwright/test";

const web = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const root = path.resolve(web, "../..");
const python = path.join(
  root,
  "services/api/.venv",
  process.platform === "win32" ? "Scripts/python.exe" : "bin/python",
);
const cli = path.join(web, "node_modules/next/dist/bin/next");
const reports = path.join(root, "docs/reports");
const warmRuns = 30;
const coldRuns = 10;
const samples = [];
const children = new Set();
const env = {
  ...process.env,
  NEXT_TELEMETRY_DISABLED: "1",
  FORMATTER_PROVIDER: "disabled",
  FORMATTER_API_KEY: "",
  FORMATTER_MODEL: "",
  RATE_LIMIT_PER_MINUTE: "10000",
  PYTHONDONTWRITEBYTECODE: "1",
};

const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
async function waitReady(url, processChild) {
  for (let attempt = 0; attempt < 120; attempt++) {
    if (processChild.exitCode !== null)
      throw new Error("A profiling server exited before readiness.");
    try {
      const response = await fetch(url, { signal: AbortSignal.timeout(1000) });
      if (response.ok) return;
    } catch {
      /* Server startup is checked against a bounded deadline. */
    }
    await delay(100);
  }
  throw new Error("Profiling server readiness timed out.");
}
function launch(executable, args, cwd, extras = {}) {
  const child = spawn(executable, args, {
    cwd,
    env: { ...env, ...extras },
    windowsHide: true,
    stdio: "ignore",
  });
  children.add(child);
  child.once("exit", () => children.delete(child));
  return child;
}
async function stop(child) {
  if (child.exitCode !== null) return;
  const exited = once(child, "exit");
  child.kill();
  await Promise.race([exited, delay(5000)]);
  if (child.exitCode === null) child.kill("SIGKILL");
}
async function startServers(orb) {
  for (const url of [
    "http://localhost:3000",
    "http://localhost:8000/api/v1/health/live",
  ]) {
    try {
      const existing = await fetch(url, { signal: AbortSignal.timeout(300) });
      if (existing)
        throw new Error(`Profiling requires unused local ports: ${url}`);
    } catch (error) {
      if (String(error).includes("requires unused")) throw error;
    }
  }
  const api = launch(
    python,
    [
      "-m",
      "uvicorn",
      "app.main:app",
      "--host",
      "localhost",
      "--port",
      "8000",
      "--no-access-log",
      "--no-proxy-headers",
    ],
    path.join(root, "services/api"),
  );
  const ui = launch(
    process.execPath,
    [cli, "start", "--hostname", "localhost", "--port", "3000"],
    web,
    {
      BUILD_OUTPUT_DIR: orb ? ".next" : ".next-no-orb",
      NEXT_PUBLIC_ENABLE_SYNC_ORB: String(orb),
    },
  );
  await Promise.all([
    waitReady("http://localhost:8000/api/v1/health/ready", api),
    waitReady("http://localhost:3000", ui),
  ]);
  return async () => {
    await Promise.all([stop(api), stop(ui)]);
  };
}

function inputOfLength(length) {
  const seed =
    "Plan to review the fictional compass layout and document the lantern component. ";
  return (
    seed.repeat(Math.ceil(length / seed.length)).slice(0, length - 1) + "."
  );
}
async function sample(browser, orb, mode, size, iteration) {
  const context = await browser.newContext({
    viewport: { width: 1440, height: 1000 },
  });
  const page = await context.newPage();
  await page.addInitScript(() => {
    window.__profileLcp = 0;
    new PerformanceObserver((list) => {
      const entry = list.getEntries().at(-1);
      if (entry) window.__profileLcp = entry.startTime;
    }).observe({ type: "largest-contentful-paint", buffered: true });
  });
  const session = await context.newCDPSession(page);
  await session.send("Performance.enable");
  const record = {
    orb,
    mode,
    inputCodePoints: size,
    iteration,
    result: "fail",
  };
  try {
    await page.goto("http://localhost:3000", { waitUntil: "networkidle" });
    await page.locator("#raw-notes").fill(inputOfLength(size));
    const before = await session.send("Performance.getMetrics");
    await page.evaluate(() => {
      window.__profileStart = performance.now();
    });
    await page
      .getByRole("button", { name: "Generate draft", exact: true })
      .click();
    await page
      .locator("[data-item-id] textarea")
      .first()
      .waitFor({ timeout: 15000 });
    await page.evaluate(
      () =>
        new Promise((resolve) =>
          requestAnimationFrame(() => requestAnimationFrame(resolve)),
        ),
    );
    const timing = await page.evaluate(() => ({
      elapsedMs: performance.now() - window.__profileStart,
      firstPaintMs:
        performance.getEntriesByName("first-paint")[0]?.startTime ?? null,
      fcpMs:
        performance.getEntriesByName("first-contentful-paint")[0]?.startTime ??
        null,
      lcpMs: window.__profileLcp,
      scripts: performance
        .getEntriesByType("resource")
        .filter((entry) => entry.name.includes(".js"))
        .map((entry) => ({
          name: new URL(entry.name).pathname,
          encodedBytes: entry.encodedBodySize,
        })),
    }));
    const after = await session.send("Performance.getMetrics");
    const metric = (set, name) =>
      set.metrics.find((item) => item.name === name)?.value ?? 0;
    Object.assign(record, timing, {
      result: "pass",
      fallback: await page
        .getByText("Rules draft", { exact: true })
        .isVisible(),
      mainThreadTaskMs:
        (metric(after, "TaskDuration") - metric(before, "TaskDuration")) * 1000,
      rendererJsHeapBytes: metric(after, "JSHeapUsedSize"),
    });
  } catch (error) {
    record.failure =
      error instanceof Error
        ? error.message.split("\n")[0]
        : "Browser check failed";
  } finally {
    await context.close();
  }
  samples.push(record);
  await writeFile(
    path.join(reports, "latency-samples.json"),
    JSON.stringify(samples, null, 2) + "\n",
  );
  return record;
}
function stats(values) {
  const sorted = values
    .filter((value) => typeof value === "number")
    .sort((a, b) => a - b);
  const percentile = (p) =>
    sorted[Math.max(0, Math.ceil(sorted.length * p) - 1)] ?? null;
  return {
    p50: percentile(0.5),
    p95: percentile(0.95),
    maximum: sorted.at(-1) ?? null,
  };
}
async function bundle(dir) {
  let raw = 0,
    gzip = 0,
    count = 0;
  async function visit(folder) {
    for (const entry of await readdir(folder, { withFileTypes: true })) {
      const target = path.join(folder, entry.name);
      if (entry.isDirectory()) await visit(target);
      else if (entry.name.endsWith(".js")) {
        const data = await readFile(target);
        raw += data.byteLength;
        gzip += gzipSync(data).byteLength;
        count++;
      }
    }
  }
  await visit(path.join(web, dir, "static"));
  return { chunks: count, rawBytes: raw, gzipBytes: gzip };
}

await mkdir(reports, { recursive: true });
const browser = await chromium.launch();
try {
  for (const orb of [true, false]) {
    const shutdown = await startServers(orb);
    try {
      for (const size of [250, 1500, 10000]) {
        for (let index = 0; index < warmRuns; index++) {
          const result = await sample(
            browser,
            orb,
            "warm-server",
            size,
            index + 1,
          );
          if (result.result !== "pass")
            throw new Error(`Warm profile failed: ${result.failure}`);
        }
        console.log(
          `Warm profile: orb=${orb}, size=${size}, ${warmRuns} runs completed.`,
        );
      }
    } finally {
      await shutdown();
    }
    for (const size of [250, 1500, 10000]) {
      for (let index = 0; index < coldRuns; index++) {
        const shutdownCold = await startServers(orb);
        try {
          const result = await sample(
            browser,
            orb,
            "cold-api-and-web-process",
            size,
            index + 1,
          );
          if (result.result !== "pass")
            throw new Error(`Cold profile failed: ${result.failure}`);
        } finally {
          await shutdownCold();
        }
      }
      console.log(
        `Cold profile: orb=${orb}, size=${size}, ${coldRuns} runs completed.`,
      );
    }
  }
  const profiles = [];
  for (const orb of [true, false])
    for (const mode of ["warm-server", "cold-api-and-web-process"])
      for (const size of [250, 1500, 10000]) {
        const group = samples.filter(
          (item) =>
            item.orb === orb &&
            item.mode === mode &&
            item.inputCodePoints === size,
        );
        profiles.push({
          orb,
          mode,
          inputCodePoints: size,
          count: group.length,
          latencyMs: stats(group.map((item) => item.elapsedMs)),
          firstPaintMs: stats(group.map((item) => item.firstPaintMs)),
          lcpMs: stats(group.map((item) => item.lcpMs)),
          mainThreadTaskMs: stats(group.map((item) => item.mainThreadTaskMs)),
          rendererJsHeapBytes: stats(
            group.map((item) => item.rendererJsHeapBytes),
          ),
          failureRate:
            group.filter((item) => item.result !== "pass").length /
            group.length,
          fallbackRate:
            group.filter((item) => item.fallback).length / group.length,
        });
      }
  const enabled = await bundle(".next"),
    disabled = await bundle(".next-no-orb");
  const report = {
    measuredAt: new Date().toISOString(),
    environment: {
      os: `${os.type()} ${os.release()}`,
      cpu: os.cpus()[0]?.model,
      logicalProcessors: os.cpus().length,
      ramBytes: os.totalmem(),
      node: process.version,
      browser: browser.version(),
      mode: "production",
      api: "disabled provider, one instance, loopback, rate limit raised to 10000/minute for profiling",
      warmRuns,
      coldRuns,
    },
    sampleCount: samples.length,
    profiles,
    bundle: {
      enabled,
      disabled,
      differenceGzipBytes: enabled.gzipBytes - disabled.gzipBytes,
    },
    limitations: [
      "Local loopback fallback profile; no live provider, network or deployment claim.",
      "Cold means both application processes restart; OS filesystem cache and browser executable remain warm. Readiness probes precede first user interaction.",
      "Renderer memory is Chromium-reported JavaScript heap, not total process or GPU memory.",
      "Input classes are fictional controlled preservation workloads, not commercial usage distribution.",
      "Timing begins before the automated Generate activation and ends after two rendering frames; includes automation dispatch overhead.",
    ],
    publicThreeSecondClaimAuthorized: false,
  };
  await writeFile(
    path.join(reports, "latency-report.json"),
    JSON.stringify(report, null, 2) + "\n",
  );
  console.log(`Recorded ${samples.length} successful client-visible runs.`);
} finally {
  await browser.close();
  await Promise.all([...children].map(stop));
}
