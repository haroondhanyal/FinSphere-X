import { expect, test } from "@playwright/test";

test("login page exposes required credentials and registration link", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/login");

  await expect(page.getByRole("heading", { name: "Sign in to your account" })).toBeVisible();
  await expect(page.getByLabel("Email address")).toHaveAttribute("required", "");
  await expect(page.getByLabel("Password")).toHaveAttribute("required", "");
  await expect(page.getByRole("link", { name: "Create an account" })).toBeVisible();
  const documentWidth = await page.locator("html").evaluate((element) => element.scrollWidth);
  expect(documentWidth).toBeLessThanOrEqual(390);
});

test("successful API response stores the session tokens", async ({ page }) => {
  await page.route("**/api/v1/auth/login", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ access_token: "test-access", refresh_token: "test-refresh" }),
    });
  });
  await page.goto("/login");
  await page.getByLabel("Email address").fill("customer@example.com");
  await page.getByLabel("Password").fill("Example-Password-123!");
  await page.getByRole("button", { name: "Sign in securely" }).click();

  await expect.poll(() => page.evaluate(() => localStorage.getItem("fsx_token"))).toBe("test-access");
  await expect.poll(() => page.evaluate(() => localStorage.getItem("fsx_refresh"))).toBe("test-refresh");
});
