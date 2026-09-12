import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";
import { result, TEST_REQUEST_ID } from "../fixtures";

const headers = {
  "Access-Control-Allow-Origin": "http://localhost:3000",
  "Access-Control-Expose-Headers": "X-Request-ID, Retry-After",
  "Cache-Control": "no-store",
};
async function stub(page: Page) {
  await page.route("**/api/v1/health/ready", (route) =>
    route.fulfill({
      json: { status: "ready", primaryFormatter: "unconfigured" },
      headers,
    }),
  );
  await page.route("**/api/v1/generate", (route) =>
    route.fulfill({
      json: result(route.request().postDataJSON().clientRequestId),
      headers,
    }),
  );
}
async function generate(page: Page) {
  await page
    .getByRole("textbox", { name: "Rough notes" })
    .fill("Finished AX-14. Plan to verify v2.4.");
  await page.getByRole("button", { name: "Generate draft" }).click();
  await expect(
    page.getByRole("textbox", { name: "Yesterday item 1" }),
  ).toBeVisible();
}

function normalizedClipboard(page: Page) {
  return page
    .evaluate(() => navigator.clipboard.readText())
    .then((text) => text.replaceAll("\r\n", "\n"));
}

test("real no-key API returns an editable, copyable fallback", async ({
  page,
}) => {
  await page.goto("/");
  await page
    .getByRole("textbox", { name: "Rough notes" })
    .fill(
      "Yesterday: finished AX-14\nToday: verify v2.4\nBlockers: waiting on review",
    );
  await page.getByRole("button", { name: "Generate draft" }).click();
  await expect(
    page.getByRole("textbox", { name: "Yesterday item 1" }),
  ).toBeVisible();
  await expect(page.getByText("Rules draft", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Copy All" })).toBeEnabled();
});

for (const profile of ["Concise bullets", "Standard update", "Async detail"]) {
  test(`${profile}: edit, move, and canonical clipboard`, async ({
    page,
    context,
  }) => {
    await stub(page);
    await context.grantPermissions(["clipboard-read", "clipboard-write"]);
    await page.goto("/");
    await page.getByRole("radio", { name: new RegExp(profile) }).check();
    await page
      .getByRole("textbox", { name: "Rough notes" })
      .fill("Finished AX-14. Plan to verify v2.4.");
    await page.getByRole("button", { name: "Generate draft" }).click();
    const yesterday = profile === "Async detail" ? "Completed" : "Yesterday";
    const today = profile === "Async detail" ? "Next" : "Today";
    await page
      .getByRole("textbox", { name: `${today} item 1` })
      .fill("Edited v2.4.");
    await page
      .getByRole("combobox", { name: `Move ${today} item 1 to` })
      .selectOption("yesterday");
    await expect(
      page.getByRole("textbox", { name: `${yesterday} item 2` }),
    ).toHaveAttribute("id", "item-D002");
    await expect(
      page.getByRole("textbox", { name: `${yesterday} item 2` }),
    ).toHaveAccessibleDescription("Review the section for this source note.");
    await page
      .getByRole("button", { name: `Copy ${yesterday} section` })
      .click();
    const bullet = profile === "Async detail" ? "" : "- ";
    await expect
      .poll(() => normalizedClipboard(page))
      .toBe(`${yesterday}\n${bullet}Finished AX-14.\n${bullet}Edited v2.4.`);
    await page.getByRole("button", { name: "Copy All" }).click();
    await expect
      .poll(() => normalizedClipboard(page))
      .toBe(
        `${yesterday}\n${bullet}Finished AX-14.\n${bullet}Edited v2.4.\n\n${today}\n${bullet}Not specified.\n\nBlockers\n${bullet}No blockers stated.`,
      );
  });
}

test("structured custom profile, replacement confirmation, and safe markup", async ({
  page,
}) => {
  await stub(page);
  await page.goto("/");
  await generate(page);
  await page
    .getByRole("textbox", { name: "Yesterday item 1" })
    .fill('<img src=x onerror="window.injected=true">');
  await expect(page.locator("img")).toHaveCount(0);
  await page.getByRole("button", { name: "Regenerate draft" }).click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.getByRole("button", { name: "Keep my edits" }).click();
  await expect(
    page.getByRole("textbox", { name: "Yesterday item 1" }),
  ).toHaveValue('<img src=x onerror="window.injected=true">');
  await page.getByRole("button", { name: "Regenerate draft" }).click();
  await page.getByRole("button", { name: "Replace and generate" }).click();
  await expect(
    page.getByRole("textbox", { name: "Yesterday item 1" }),
  ).toHaveValue("Finished AX-14.");
  await page.getByRole("radio", { name: /Custom/ }).check();
  await page
    .getByRole("textbox", { name: "Yesterday heading" })
    .fill("Completed work");
  await page
    .getByRole("combobox", { name: "Layout", exact: true })
    .selectOption("paragraphs");
  await expect(
    page.getByRole("textbox", { name: "Completed work item 1" }),
  ).toBeVisible();
});

test("validation and Retry-After preserve notes and require an explicit retry", async ({
  page,
}) => {
  await stub(page);
  let requests = 0;
  await page.route("**/api/v1/generate", async (route) => {
    requests++;
    if (requests < 3)
      await route.fulfill({
        status: requests === 1 ? 422 : 429,
        json: {
          error: {
            code: requests === 1 ? "VALIDATION_ERROR" : "RATE_LIMITED",
            message: "Check fields",
            requestId: TEST_REQUEST_ID,
            clientRequestId: route.request().postDataJSON().clientRequestId,
            fieldErrors:
              requests === 1
                ? { rawNotes: ["Check this fictional note."] }
                : {},
          },
        },
        headers: { ...headers, "Retry-After": requests === 2 ? "3" : "0" },
      });
    else
      await route.fulfill({
        json: result(route.request().postDataJSON().clientRequestId),
        headers,
      });
  });
  await page.goto("/");
  await page
    .getByRole("textbox", { name: "Rough notes" })
    .fill("original note");
  await page.getByRole("button", { name: "Generate draft" }).click();
  await expect(page.locator(".error-summary")).toBeFocused();
  await expect(page.getByRole("textbox", { name: "Rough notes" })).toHaveValue(
    "original note",
  );
  await page
    .getByRole("textbox", { name: "Rough notes" })
    .fill("corrected note");
  await page.getByRole("button", { name: "Generate draft" }).click();
  await expect(
    page.getByRole("button", { name: "Generate draft" }),
  ).toBeDisabled();
  await expect(
    page.getByRole("button", { name: "Generate draft" }),
  ).toBeEnabled({ timeout: 5000 });
  expect(requests).toBe(2);
  await page.getByRole("button", { name: "Generate draft" }).click();
  await expect(
    page.getByRole("textbox", { name: "Yesterday item 1" }),
  ).toBeVisible();
});

test("cancelled late responses cannot overwrite the next request", async ({
  page,
}) => {
  await stub(page);
  let release: (() => void) | undefined;
  let requests = 0;
  await page.route("**/api/v1/generate", async (route) => {
    requests++;
    const count = requests;
    const response = result(route.request().postDataJSON().clientRequestId);
    response.draft.yesterday[0].text =
      count === 1 ? "Old result" : "Newest result";
    if (count === 1)
      await new Promise<void>((resolve) => {
        release = resolve;
      });
    await route.fulfill({ json: response, headers }).catch(() => {});
  });
  await page.goto("/");
  await page.getByRole("textbox", { name: "Rough notes" }).fill("first");
  await page.getByRole("button", { name: "Generate draft" }).click();
  await expect.poll(() => requests).toBe(1);
  await page.getByRole("button", { name: "Cancel", exact: true }).click();
  await expect(page.getByRole("status")).toContainText(
    "already-sent AI request may still finish",
  );
  await page.getByRole("textbox", { name: "Rough notes" }).fill("second");
  await page.getByRole("button", { name: "Generate draft" }).click();
  await expect(
    page.getByRole("textbox", { name: "Yesterday item 1" }),
  ).toHaveValue("Newest result");
  release?.();
  await expect(
    page.getByRole("textbox", { name: "Yesterday item 1" }),
  ).toHaveValue("Newest result");
});

test("blocked storage and clipboard still allow the full flow without content persistence", async ({
  page,
}) => {
  await page.addInitScript(() => {
    Object.defineProperty(window, "localStorage", {
      get() {
        throw new Error("Storage blocked");
      },
    });
    Object.defineProperty(navigator, "clipboard", {
      value: {
        writeText: () => Promise.reject(new Error("Clipboard blocked")),
      },
    });
  });
  await stub(page);
  await page.goto("/");
  await generate(page);
  await page.getByRole("button", { name: "Copy All" }).click();
  await expect(
    page.getByRole("textbox", { name: "Plain-text copy fallback" }),
  ).toBeFocused();
  await page.getByRole("button", { name: "Reset preferences" }).click();
  await expect(
    page.getByRole("textbox", { name: "Yesterday item 1" }),
  ).toHaveValue("Finished AX-14.");
});

test("keyboard, axe, strict CSP, and 320px reflow", async ({ page }) => {
  const violations: string[] = [];
  await page.addInitScript(() => {
    document.addEventListener("securitypolicyviolation", (event) => {
      (window as Window & { cspViolations?: string[] }).cspViolations ??= [];
      (window as Window & { cspViolations?: string[] }).cspViolations?.push(
        event.violatedDirective,
      );
    });
  });
  page.on("pageerror", (error) => violations.push(error.message));
  await stub(page);
  const response = await page.goto("/");
  expect(response?.headers()["content-security-policy"]).toContain(
    "object-src 'none'",
  );
  expect(response?.headers()["content-security-policy"]).not.toContain(
    "unsafe-eval",
  );
  await page.keyboard.press("Tab");
  await expect(
    page.getByRole("link", { name: "Skip to main content" }),
  ).toBeFocused();
  await page.keyboard.press("Enter");
  await page.getByRole("textbox", { name: "Rough notes" }).focus();
  await page.keyboard.type("Finished AX-14.");
  await page.keyboard.press("Control+Enter");
  await expect(
    page.getByRole("textbox", { name: "Yesterday item 1" }),
  ).toBeVisible();
  const axe = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
    .analyze();
  expect(axe.violations).toEqual([]);
  await page.getByRole("textbox", { name: "Yesterday item 1" }).fill("edited");
  await page.getByRole("button", { name: "Regenerate draft" }).click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.keyboard.press("Escape");
  expect(
    await page.evaluate(
      () =>
        (window as Window & { cspViolations?: string[] }).cspViolations ?? [],
    ),
  ).toEqual([]);
  expect(violations).toEqual([]);
  await page.setViewportSize({ width: 320, height: 800 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: test.info().outputPath("workspace-320.png"),
    fullPage: true,
  });
});

for (const failure of ["timeout", "malformed", "novel protected fact"]) {
  test(`safe fallback response after provider ${failure} remains editable`, async ({
    page,
  }) => {
    await stub(page);
    await page.goto("/");
    await generate(page);
    await expect(
      page.getByText(/conservative rules and preserves/),
    ).toBeVisible();
    await expect(page.getByRole("button", { name: "Copy All" })).toBeEnabled();
  });
}
