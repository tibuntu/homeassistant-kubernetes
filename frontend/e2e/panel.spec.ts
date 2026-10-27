import { expect, test, type Page } from "@playwright/test";

const HARNESS = "/e2e/harness.html";

const openTab = (page: Page, label: string) =>
  page.locator(".tab", { hasText: label }).click();

test("overview count card opens the workloads tab with its category preset", async ({
  page,
}) => {
  await page.goto(HARNESS);
  await page.locator('.count-card[title="Show Deployments"]').click();

  await expect(page.locator(".tab[active]")).toHaveText(/Workloads/);
  await expect(
    page
      .locator("select.filter-select")
      .filter({ has: page.locator('option[value="deployments"]') }),
  ).toHaveValue("deployments");
  await expect(page.locator(".workload-card", { hasText: "web" })).toBeVisible();
  await expect(page.locator(".workload-card", { hasText: "db" })).toHaveCount(0);
});

test("pods column visibility survives a reload", async ({ page }) => {
  await page.goto(HARNESS);
  await openTab(page, "Pods");
  await expect(page.locator("th", { hasText: "Node" })).toBeVisible();

  await page.locator(".column-toggle-btn").click();
  await page.locator(".column-option", { hasText: "Node" }).locator("input").uncheck();
  await expect(page.locator("th", { hasText: "Node" })).toHaveCount(0);

  await page.reload();
  await openTab(page, "Pods");
  await expect(page.locator("th", { hasText: "Phase" })).toBeVisible();
  await expect(page.locator("th", { hasText: "Node" })).toHaveCount(0);
});

test("Escape closes the scale dialog without calling the service", async ({ page }) => {
  await page.goto(HARNESS);
  await openTab(page, "Workloads");
  await page.locator(".replica-info.scalable").first().click();
  await expect(page.locator(".confirm-dialog")).toBeVisible();

  await page.keyboard.press("Escape");

  await expect(page.locator(".confirm-dialog")).toHaveCount(0);
  expect(await page.evaluate(() => window.__k8s.services)).toEqual([]);
});

test("scale dialog calls scale_workload with the new replica count", async ({
  page,
}) => {
  await page.goto(HARNESS);
  await openTab(page, "Workloads");
  await page
    .locator(".workload-card", { hasText: "web" })
    .locator(".replica-info.scalable")
    .click();
  await page.locator(".scale-input").fill("3");
  await page.locator("button.scale-action").click();

  await expect(page.locator(".confirm-dialog")).toHaveCount(0);
  expect(await page.evaluate(() => window.__k8s.services)).toEqual([
    {
      domain: "kubernetes",
      service: "scale_workload",
      data: {
        workload_name: "web",
        namespace: "default",
        entry_id: "entry_1",
        replicas: 3,
      },
    },
  ]);
});

test("HPA-managed workload shows a badge and only allows scaling to 0", async ({
  page,
}) => {
  await page.goto(HARNESS);
  await openTab(page, "Workloads");
  const db = page.locator(".workload-card", { hasText: "db" });
  await expect(db.locator(".badge-hpa")).toBeVisible();
  await expect(
    page.locator(".workload-card", { hasText: "web" }).locator(".badge-hpa"),
  ).toHaveCount(0);

  await db.locator(".replica-info.scalable").click();
  await expect(page.locator(".hpa-warning")).toContainText("db-hpa");
  await page.locator(".scale-input").fill("3");
  await expect(page.locator("button.scale-action")).toBeDisabled();
  await page.locator(".scale-input").fill("0");
  await expect(page.locator("button.scale-action")).toBeEnabled();
});

test("error card retry refetches after a failed load", async ({ page }) => {
  await page.goto(`${HARNESS}?fail=kubernetes/cluster/overview`);
  await expect(page.locator(".error-card")).toBeVisible();

  await page.evaluate(() => window.__k8s.fail.clear());
  await page.locator(".retry-btn").click();

  await expect(page.locator(".error-card")).toHaveCount(0);
  await expect(page.locator('.count-card[title="Show Pods"]')).toBeVisible();
});

test("coordinator push triggers one debounced refetch", async ({ page }) => {
  await page.goto(HARNESS);
  await expect(page.locator(".count-card").first()).toBeVisible();
  const before = await page.evaluate(() => window.__k8s.calls.length);

  await page.evaluate(() => {
    window.__k8s.push();
    window.__k8s.push();
  });

  await expect
    .poll(() => page.evaluate(() => window.__k8s.calls.length))
    .toBe(before + 1);
  await page.waitForTimeout(1500);
  expect(await page.evaluate(() => window.__k8s.calls.length)).toBe(before + 1);
});
