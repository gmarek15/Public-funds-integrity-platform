import { expect, test } from "@playwright/test";

test("homepage renders county dashboard, zoom controls, and recipient popup", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Public Funds Integrity Platform" })).toBeVisible();
  await expect(page.getByText("Washington county spend heatmap")).toBeVisible();
  await expect(page.getByText("County Spend Ranking")).toBeVisible();
  await expect(page.getByText("Visible Program Mix")).toBeVisible();
  await expect(page.getByText("Featured Verified Recipients")).toBeVisible();
  await expect(
    page.locator(".analytics-panel").getByText("HOLISTIC BEHAVIORAL HEALTH | HOSPICE OF SPOKANE"),
  ).toBeVisible();

  const rankingSection = page.locator(".analytics-panel").getByText("County Spend Ranking").locator("..");
  await rankingSection.getByRole("button", { name: /King County/ }).click();
  await expect(page.getByRole("button", { name: "Reset statewide view" })).toBeVisible();
  const snapshotSection = page.locator(".analytics-panel").getByText("County Snapshot").locator("..");
  await expect(snapshotSection.getByText("King County")).toBeVisible();
  await expect(snapshotSection.getByText("16 sites")).toBeVisible();

  await page.getByRole("button", { name: /HARBORVIEW MEDICAL CENTER/ }).click();
  await expect(page.locator(".map-popup").getByText("Open recipient detail")).toBeVisible();
  await expect(page.locator(".map-popup").getByText("HARBORVIEW MEDICAL CENTER")).toBeVisible();
});

test("recipient detail page opens from the homepage", async ({ page }) => {
  await page.goto("/");

  await page.getByRole("link", { name: "View detail" }).first().click();

  await expect(page).toHaveURL(/\/entities\//);
  await expect(page.getByRole("heading", { name: "Molina Healthcare of Washington, Inc." })).toBeVisible();
  await expect(page.getByText("Recipient Detail")).toBeVisible();
  await expect(page.getByText("Source Records")).toBeVisible();
  const sourceLinks = page.getByRole("link", { name: "Open source" });
  await expect(sourceLinks).toHaveCount(5);
  await expect(sourceLinks.first()).toHaveAttribute(
    "href",
    "https://www.fiscal.wa.gov/Spending/Checkbook",
  );
  await expect(page.getByText("Apple Health managed care organizations")).toBeVisible();
});
