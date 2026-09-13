import { expect, test } from "@playwright/test";

test("the sculptural scene renders a stable reference frame", async ({
  page,
}) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  await page.getByRole("button", { name: "Explore in 3D" }).click();
  const canvas = page.locator(".sync-orb canvas");
  await expect(canvas).toBeVisible();
  await expect
    .poll(() =>
      canvas.evaluate((element) => (element as HTMLCanvasElement).width),
    )
    .toBeGreaterThan(500);
  await page
    .locator(
      ".scene-coordinate, .scene-note, .scene-cross, .scene-grid, .scene-orbit, .hero-baseline, .scene-toggle",
    )
    .evaluateAll((elements) =>
      elements.forEach((element) => {
        (element as HTMLElement).style.visibility = "hidden";
      }),
    );
  await page.locator(".sync-orb").screenshot({
    path: test.info().outputPath("sculpture-reference.png"),
    omitBackground: true,
  });
});

test("example notes generate through the real API without overwriting input", async ({
  page,
}) => {
  await page.goto("/");
  const example = page.getByRole("button", { name: "Try an example" });
  const notes = page.getByRole("textbox", { name: "Rough notes" });
  await example.click();
  await expect(notes).toBeFocused();
  await expect(notes).toHaveValue(/Yesterday: shipped the new onboarding flow/);
  await expect(example).toBeDisabled();
  await page.getByRole("button", { name: "Generate draft" }).click();
  await expect(
    page.getByRole("textbox", { name: "Yesterday item 1" }),
  ).toHaveValue("shipped the new onboarding flow");
  await expect(page.getByRole("textbox", { name: "Today item 1" })).toHaveValue(
    "connect the preferences API",
  );
  await expect(
    page.getByRole("textbox", { name: "Blockers item 1" }),
  ).toHaveValue("waiting on the final icon assets");
});

test("desktop and mobile layouts reflow with reduced motion", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  for (const width of [1440, 1024, 768, 390, 320]) {
    await page.setViewportSize({ width, height: 900 });
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await expect
      .poll(() =>
        page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
      )
      .toBe(true);
    await expect(page.getByRole("heading", { level: 1 })).toHaveCSS(
      "animation-name",
      "none",
    );
    await page.screenshot({
      path: test.info().outputPath(`experience-${width}.png`),
      fullPage: true,
    });
  }
});

test("workspace remains usable when WebGL is unavailable", async ({ page }) => {
  await page.addInitScript(() => {
    const original = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function (
      this: HTMLCanvasElement,
      ...args: Parameters<typeof original>
    ) {
      if (args[0] === "webgl2" || args[0] === "webgl") return null;
      return original.apply(this, args);
    } as typeof original;
  });
  await page.goto("/");
  await expect(page.locator(".sculpture-fallback")).toBeVisible();
  await page.getByRole("button", { name: "Explore in 3D" }).click();
  await expect(
    page.getByRole("button", { name: "3D unavailable on this device" }),
  ).toBeDisabled();
  await expect(page.locator(".sync-orb canvas")).toHaveCount(0);
  await page.getByRole("button", { name: "Try an example" }).click();
  await expect(
    page.getByRole("button", { name: "Generate draft" }),
  ).toBeEnabled();
});
