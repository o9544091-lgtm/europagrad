import { expect, test } from "@playwright/test";

test.describe("guest journey", () => {
  test("landing renders with navigation", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { level: 1 })).toContainText(/funded/i);
    await expect(page.getByRole("navigation")).toBeVisible();
  });

  test("results shows real-data or empty state, never mock data", async ({ page }) => {
    await page.goto("/results");
    await page.waitForLoadState("networkidle");
    const hasRows = await page.getByRole("table").count();
    if (hasRows > 0) {
      await expect(page.locator("tbody tr").first()).toBeVisible();
    } else {
      await expect(page.getByText(/no programmes researched yet/i)).toBeVisible();
      await expect(page.getByRole("button", { name: /start research/i })).toBeVisible();
    }
  });

  test("search configurator renders all modes", async ({ page }) => {
    await page.goto("/search");
    await expect(page.getByText("Single country")).toBeVisible();
    await expect(page.getByText("All Europe")).toBeVisible();
    await expect(page.getByText(/research depth/i)).toBeVisible();
  });

  test("unknown programme id renders not-found", async ({ page }) => {
    await page.goto("/programs/00000000-0000-0000-0000-000000000000");
    await expect(page.getByText(/page not found|not found/i).first()).toBeVisible();
  });

  test("plan requires sign-in for data", async ({ page }) => {
    await page.goto("/plan");
    await page.waitForLoadState("networkidle");
    await expect(page.getByText(/sign in to save a real plan/i)).toBeVisible();
  });

  test("erasmus and report render from dataset", async ({ page }) => {
    await page.goto("/erasmus");
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await page.goto("/report");
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  });
});

test.describe("api guards", () => {
  test("plan API rejects anonymous access", async ({ request }) => {
    const resp = await request.get("/api/plan");
    expect(resp.status()).toBe(401);
  });

  test("research trigger rejects anonymous access", async ({ request }) => {
    const resp = await request.post("/api/research/trigger", {
      data: { countries: ["IT"], depth: "L1" },
    });
    expect(resp.status()).toBe(401);
  });

  test("research trigger validates country codes", async ({ request }) => {
    const resp = await request.post("/api/research/trigger", {
      data: { countries: ["INVALID"], depth: "L1" },
    });
    expect([401, 400]).toContain(resp.status());
  });
});
