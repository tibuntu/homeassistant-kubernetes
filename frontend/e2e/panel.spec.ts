import { expect, test, type Page } from "@playwright/test";

const HARNESS = "/e2e/harness.html";

// The harness has no router: deep links live under /e2e/harness.html/<tab>, which
// Vite would 404 on a reload, so serve the harness page for those paths.
test.beforeEach(async ({ page }) => {
  await page.route(/\/e2e\/harness\.html\/./, async (route) => {
    const url = new URL("/e2e/harness.html", route.request().url()).href;
    await route.fulfill({ response: await route.fetch({ url }) });
  });
});

const pathAndQuery = (page: Page) =>
  page.evaluate(() => location.pathname + location.search);

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
  expect(await pathAndQuery(page)).toBe(
    "/e2e/harness.html/workloads?category=deployments",
  );
  await expect(page.locator(".workload-card", { hasText: "web" })).toBeVisible();
  await expect(page.locator(".workload-card", { hasText: "db" })).toHaveCount(0);
});

test("nodes show CPU and memory usage bars when metrics exist", async ({ page }) => {
  await page.goto(`${HARNESS}/nodes`);
  const node = page.locator(".node-card", { hasText: "node-1" });
  await expect(node.locator(".resource-bar-fill").first()).toBeVisible();
  await expect(
    node.locator(".resource-bar-container", { hasText: "30%" }).first(),
  ).toBeVisible();
});

test("overview lists restarting pods with their last termination", async ({ page }) => {
  await page.goto(HARNESS);
  const card = page.locator(".alert-card", { hasText: "default/worker-abc" });
  await expect(card).toContainText("5 restarts, last: OOMKilled (exit 137)");
});

test("overview lists failed jobs with reason and owning CronJob", async ({ page }) => {
  await page.goto(HARNESS);
  const card = page.locator(".alert-card", { hasText: "default/backup-29000000" });
  await expect(card).toContainText("Failed (BackoffLimitExceeded), CronJob backup");
});

test("pods tab shows the problem reason and the Problems chip filters to it", async ({
  page,
}) => {
  await page.goto(HARNESS);
  await openTab(page, "Pods");
  const badge = page.locator("tr", { hasText: "crash-5c8d7-xyz99" }).locator(".badge");
  await expect(badge).toHaveText("CrashLoopBackOff");
  await expect(badge).toHaveClass(/badge-failed/);
  await expect(page.locator("tr", { hasText: "db-0" })).toBeVisible();

  await page.locator(".filter-chip", { hasText: "Problems (1)" }).click();
  await expect(page.locator("tbody tr")).toHaveCount(1);
  await expect(page.locator("tbody tr")).toContainText("crash-5c8d7-xyz99");
});

test("overview pod alert shows the reason and opens the pods tab with a search", async ({
  page,
}) => {
  await page.goto(HARNESS);
  const card = page.locator(".alert-card", { hasText: "default/crash-5c8d7-xyz99" });
  await expect(card).toContainText("CrashLoopBackOff");
  await card.click();
  await expect(page.locator(".tab[active]")).toHaveText(/Pods/);
  await expect(page.locator(".search-input")).toHaveValue("crash-5c8d7-xyz99");
  await expect(page.locator("tbody tr")).toHaveCount(1);
  expect(await pathAndQuery(page)).toBe(
    "/e2e/harness.html/pods?search=crash-5c8d7-xyz99",
  );
});

test("overview alerts are keyboard operable and reach Workloads Jobs", async ({
  page,
}) => {
  await page.goto(HARNESS);
  const card = page.locator(".alert-card", { hasText: "default/backup-29000000" });
  await card.focus();
  await page.keyboard.press("Enter");
  await expect(page.locator(".tab[active]")).toHaveText(/Workloads/);
  await expect(page.locator(".search-input")).toHaveValue("backup-29000000");
  await expect(
    page
      .locator("select.filter-select")
      .filter({ has: page.locator('option[value="jobs"]') }),
  ).toHaveValue("jobs");
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
  await expect(page.locator("th", { hasText: "Status" })).toBeVisible();
  await expect(page.locator("th", { hasText: "Node" })).toHaveCount(0);
});

test("pods sort headers expose aria-sort and work from the keyboard", async ({
  page,
}) => {
  await page.goto(HARNESS);
  await openTab(page, "Pods");
  const th = (name: string) =>
    page.locator("th", { has: page.getByRole("button", { name, exact: true }) });

  await page.getByRole("button", { name: "Restarts" }).focus();
  await page.keyboard.press("Enter");
  await expect(th("Restarts")).toHaveAttribute("aria-sort", "ascending");
  await page.keyboard.press("Enter");
  await expect(th("Restarts")).toHaveAttribute("aria-sort", "descending");
  for (const name of ["Name", "Namespace", "Status", "CPU", "Memory", "Node", "Age"]) {
    await expect(th(name)).toHaveAttribute("aria-sort", "none");
  }
  expect(await pathAndQuery(page)).toBe(
    "/e2e/harness.html/pods?sort=restarts&dir=desc",
  );
});

test("pods table shows usage and sorts by CPU and memory", async ({ page }) => {
  await page.goto(HARNESS);
  await openTab(page, "Pods");
  const firstName = () => page.locator("tbody tr .pod-name").first();

  await expect(page.locator("tbody tr", { hasText: "web-7d9f8b-abc12" })).toContainText(
    "120m",
  );
  await expect(page.locator("tbody tr", { hasText: "web-7d9f8b-abc12" })).toContainText(
    "256 Mi",
  );

  await page.getByRole("button", { name: "CPU" }).click();
  await expect(firstName()).toHaveText("db-0");
  await page.getByRole("button", { name: "CPU" }).click();
  await expect(firstName()).toHaveText("web-7d9f8b-abc12");

  await page.getByRole("button", { name: "Memory" }).click();
  await expect(firstName()).toHaveText("web-7d9f8b-abc12");
  await page.getByRole("button", { name: "Memory" }).click();
  await expect(firstName()).toHaveText("db-0");
});

test("a stored column selection gains the usage columns once", async ({ page }) => {
  await page.addInitScript(() => {
    if (!localStorage.getItem("k8s-pods-columns")) {
      localStorage.setItem("k8s-pods-columns", JSON.stringify(["ready", "node"]));
    }
  });
  await page.goto(HARNESS);
  await openTab(page, "Pods");
  await expect(page.locator("th", { hasText: "CPU" })).toBeVisible();
  await expect(page.locator("th", { hasText: "Restarts" })).toHaveCount(0);

  // The migrated selection is stored: a plain reload keeps the columns.
  await page.reload();
  await openTab(page, "Pods");
  await expect(page.locator("th", { hasText: "CPU" })).toBeVisible();

  // The user can hide them again and the choice sticks across reloads.
  await page.locator(".column-toggle-btn").click();
  await page.locator(".column-option", { hasText: "CPU" }).locator("input").uncheck();
  await page.reload();
  await openTab(page, "Pods");
  await expect(page.locator("th", { hasText: "CPU" })).toHaveCount(0);
  await expect(page.locator("th", { hasText: "Memory" })).toBeVisible();
});

test("workload cards show usage", async ({ page }) => {
  await page.goto(HARNESS);
  await openTab(page, "Workloads");
  await expect(
    page.locator(".workload-card", { hasText: "web" }).first(),
  ).toContainText("340m · 512 Mi");
  await expect(page.locator(".workload-card", { hasText: "log-agent" })).toContainText(
    "5m · 32 Mi",
  );
});

test("usage is hidden when the cluster has no metrics", async ({ page }) => {
  await page.goto(`${HARNESS}?metrics=0`);
  await openTab(page, "Workloads");
  await expect(page.locator(".workload-card").first()).toBeVisible();
  await expect(page.locator(".replica-info.usage")).toHaveCount(0);

  await openTab(page, "Pods");
  const row = page.locator("tbody tr", { hasText: "web-7d9f8b-abc12" });
  await expect(row).not.toContainText("120m");
  await expect(row).not.toContainText("256 Mi");
  await expect(row.locator("td").nth(5)).toHaveText("-");
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
        workload_type: "Deployment",
        entry_id: "entry_1",
        replicas: 3,
      },
    },
  ]);
});

test("CronJob trigger sends workload_type CronJob", async ({ page }) => {
  await page.goto(HARNESS);
  await openTab(page, "Workloads");
  await page
    .locator(".workload-card", { hasText: "backup" })
    .locator("button[title='Trigger now']")
    .click();

  expect(await page.evaluate(() => window.__k8s.services)).toEqual([
    {
      domain: "kubernetes",
      service: "start_workload",
      data: {
        workload_name: "backup",
        namespace: "default",
        workload_type: "CronJob",
        entry_id: "entry_1",
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

test("stalled rollout reads Degraded with a badge despite all replicas ready", async ({
  page,
}) => {
  await page.goto(HARNESS);
  await expect(
    page.locator(".alert-detail", { hasText: "Rollout stalled" }),
  ).toContainText("ProgressDeadlineExceeded");

  await openTab(page, "Workloads");
  const api = page.locator(".workload-card", { hasText: "api" });
  await expect(api.locator(".badge-degraded")).toHaveText("Degraded");
  await expect(api.locator(".badge-rollout-stalled")).toHaveAttribute(
    "title",
    /ProgressDeadlineExceeded/,
  );
  const web = page.locator(".workload-card", { hasText: "web" });
  await expect(web.locator(".badge-healthy")).toBeVisible();
  await expect(web.locator(".badge-rollout-stalled")).toHaveCount(0);
});

test("job cards show the backend-derived state badge", async ({ page }) => {
  await page.goto(HARNESS);
  await openTab(page, "Workloads");
  const migrate = page.locator(".workload-card", { hasText: "migrate" });
  await expect(migrate.locator(".badge-complete")).toHaveText("Complete");
  const nightly = page.locator(".workload-card", { hasText: "nightly-report" });
  await expect(
    nightly.locator(".badge-failed").filter({ hasText: /^Failed$/ }),
  ).toBeVisible();
  await expect(nightly.locator(".badge-complete")).toHaveCount(0);
});

/** Number of mutation controls on the Workloads, Pods and Nodes tabs. */
async function countMutationControls(page: Page): Promise<number[]> {
  await openTab(page, "Workloads");
  await expect(page.locator(".workload-card").first()).toBeVisible();
  const workloads = await page
    .locator(".workload-card .action-btn, .replica-info.scalable")
    .count();

  await openTab(page, "Pods");
  await expect(page.locator("tbody tr").first()).toBeVisible();
  const pods = await page.locator('button[title="Delete pod"]').count();

  await openTab(page, "Nodes");
  await expect(page.locator(".node-card").first()).toBeVisible();
  const nodes = await page.locator(".node-card .action-btn").count();

  return [workloads, pods, nodes];
}

test("mutation controls are shown to admins", async ({ page }) => {
  await page.goto(HARNESS);
  for (const n of await countMutationControls(page)) expect(n).toBeGreaterThan(0);
});

test("mutation controls are hidden from non-admins", async ({ page }) => {
  await page.goto(`${HARNESS}?admin=0`);
  expect(await countMutationControls(page)).toEqual([0, 0, 0]);
});

test("error card retry refetches after a failed load", async ({ page }) => {
  await page.goto(`${HARNESS}?fail=kubernetes/cluster/overview`);
  await expect(page.locator(".error-card")).toBeVisible();

  await page.evaluate(() => window.__k8s.fail.clear());
  await page.locator(".retry-btn").click();

  await expect(page.locator(".error-card")).toHaveCount(0);
  await expect(page.locator('.count-card[title="Show Pods"]')).toBeVisible();
});

test("a failed refresh keeps the loaded view instead of the error card", async ({
  page,
}) => {
  await page.goto(HARNESS);
  await expect(page.locator('.count-card[title="Show Pods"]')).toBeVisible();
  const before = await page.evaluate(() => window.__k8s.calls.length);

  await page.evaluate(() => {
    window.__k8s.fail.add("kubernetes/cluster/overview");
    window.__k8s.push();
  });
  await expect
    .poll(() => page.evaluate(() => window.__k8s.calls.length))
    .toBe(before + 1);

  await expect(page.locator(".error-card")).toHaveCount(0);
  await expect(page.locator('.count-card[title="Show Pods"]')).toBeVisible();
  await expect(page.locator(".stale-hint")).toContainText("Last refresh failed");

  await page.evaluate(() => {
    window.__k8s.fail.clear();
    window.__k8s.push();
  });
  await expect(page.locator(".stale-hint")).toHaveCount(0);
});

test("a re-attached view subscribes once and refetches on push", async ({ page }) => {
  await page.goto(HARNESS);
  await expect(page.locator(".count-card").first()).toBeVisible();

  await page.evaluate(() => {
    const view = document
      .querySelector("kubernetes-panel")!
      .shadowRoot!.querySelector("k8s-overview")!;
    const parent = view.parentNode!;
    view.remove();
    parent.appendChild(view);
  });
  await expect.poll(() => page.evaluate(() => window.__k8s.subscribers.length)).toBe(1);

  const before = await page.evaluate(() => window.__k8s.calls.length);
  await page.evaluate(() => window.__k8s.push());
  await expect
    .poll(() => page.evaluate(() => window.__k8s.calls.length))
    .toBe(before + 1);
  const last = await page.evaluate(() => window.__k8s.calls.at(-1)!.type);
  expect(last).toBe("kubernetes/cluster/overview");
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

test("pod logs dialog shows logs, refetches per container and closes on Escape", async ({
  page,
}) => {
  await page.goto(HARNESS);
  await openTab(page, "Pods");
  await page
    .locator("tr", { hasText: "db-0" })
    .locator('button[title="Show logs"]')
    .click();

  await expect(page.locator(".logs-output")).toContainText("listening on :8080");
  await page
    .locator(".logs-dialog select.filter-select")
    .selectOption("metrics-exporter");
  await page.locator(".logs-dialog .filter-chip", { hasText: "2000" }).click();
  await expect(page.locator(".logs-output")).toBeVisible();

  const logCalls = await page.evaluate(() =>
    window.__k8s.calls.filter((c) => c.type === "kubernetes/pods/logs"),
  );
  expect(logCalls.at(-1)).toEqual({
    type: "kubernetes/pods/logs",
    entry_id: "entry_1",
    pod_name: "db-0",
    namespace: "default",
    container: "metrics-exporter",
    tail_lines: 2000,
    previous: false,
  });

  await page.keyboard.press("Escape");
  await expect(page.locator(".logs-dialog")).toHaveCount(0);
});

test("pod logs wrap by default, the choice persists and can be turned off", async ({
  page,
}) => {
  await page.goto(HARNESS);
  await openTab(page, "Pods");
  const open = async () => {
    await page
      .locator("tr", { hasText: "db-0" })
      .locator('button[title="Show logs"]')
      .click();
    await expect(page.locator(".logs-output")).toBeVisible();
  };
  const metrics = () =>
    page.locator(".logs-output").evaluate((el) => ({
      ws: getComputedStyle(el).whiteSpace,
      overflows: el.scrollWidth > el.clientWidth,
    }));
  await open();
  expect(await metrics()).toEqual({ ws: "pre-wrap", overflows: false });

  await page.locator(".logs-wrap-toggle").uncheck();
  expect(await metrics()).toEqual({ ws: "pre", overflows: true });

  await page.keyboard.press("Escape");
  await open();
  await expect(page.locator(".logs-wrap-toggle")).not.toBeChecked();
  expect((await metrics()).ws).toBe("pre");

  await page.reload();
  await openTab(page, "Pods");
  await open();
  await expect(page.locator(".logs-wrap-toggle")).not.toBeChecked();
});

test("pod logs auto-refresh polls every 5 s and stops on close", async ({ page }) => {
  await page.clock.install();
  await page.goto(HARNESS);
  await openTab(page, "Pods");
  await page
    .locator("tr", { hasText: "db-0" })
    .locator('button[title="Show logs"]')
    .click();
  await expect(page.locator(".logs-output")).toBeVisible();
  const count = () =>
    page.evaluate(
      () => window.__k8s.calls.filter((c) => c.type === "kubernetes/pods/logs").length,
    );
  expect(await count()).toBe(1);
  await expect(page.locator(".logs-auto-toggle")).not.toBeChecked();

  await page.locator(".logs-auto-toggle").check();
  await page.clock.runFor(5100);
  await expect.poll(count).toBe(2);

  await page.locator(".logs-dialog .logs-previous input").check();
  await expect(page.locator(".logs-auto-toggle")).toBeDisabled();
  await expect(page.locator(".logs-auto-toggle")).not.toBeChecked();
  await page.locator(".logs-dialog .logs-previous input").uncheck();
  await page.locator(".logs-auto-toggle").check();
  const before = await count();

  await page.keyboard.press("Escape");
  await expect(page.locator(".logs-dialog")).toHaveCount(0);
  await page.clock.runFor(15000);
  expect(await count()).toBe(before);
});

test("pod logs keep the scroll position unless the view was at the bottom", async ({
  page,
}) => {
  await page.clock.install();
  await page.goto(HARNESS);
  await openTab(page, "Pods");
  await page
    .locator("tr", { hasText: "db-0" })
    .locator('button[title="Show logs"]')
    .click();
  const pre = page.locator(".logs-output");
  await expect(pre).toBeVisible();
  await page.locator(".logs-wrap-toggle").uncheck();
  // Many lines so the output scrolls vertically.
  await page.evaluate(() => {
    window.__k8s.logs = Array.from({ length: 300 }, (_, i) => `line ${i}`).join("\n");
  });
  await page.locator(".logs-dialog .filter-chip", { hasText: "100" }).click();
  await expect.poll(() => pre.evaluate((el) => el.scrollTop > 0)).toBe(true);
  const atBottom = () =>
    pre.evaluate((el) => el.scrollHeight - el.scrollTop - el.clientHeight < 8);
  expect(await atBottom()).toBe(true);

  await page.locator(".logs-auto-toggle").check();
  await page.evaluate(() => {
    window.__k8s.logs += "\nnew tail";
  });
  await page.clock.runFor(5100);
  await expect(pre).toContainText("new tail");
  expect(await atBottom()).toBe(true);

  await pre.evaluate((el) => (el.scrollTop = 0));
  await page.evaluate(() => {
    window.__k8s.logs += "\nanother tail";
  });
  await page.clock.runFor(5100);
  await expect(pre).toContainText("another tail");
  expect(await pre.evaluate((el) => el.scrollTop)).toBe(0);
});

test("pod logs failure shows an inline error in the dialog", async ({ page }) => {
  await page.goto(`${HARNESS}?fail=kubernetes/pods/logs`);
  await openTab(page, "Pods");
  await page
    .locator("tr", { hasText: "web-7d9f8b-abc12" })
    .locator('button[title="Show logs"]')
    .click();

  await expect(page.locator(".logs-dialog .inline-error")).toContainText(
    "kubernetes/pods/logs failed",
  );
  await expect(page.locator(".logs-output")).toHaveCount(0);
});

test("pod detail dialog shows containers and events, closes on Escape and overlay click", async ({
  page,
}) => {
  await page.goto(HARNESS);
  await openTab(page, "Pods");
  const link = page.locator(".pod-link", { hasText: "db-0" });
  // Keyboard-accessible: Enter on the focused name opens it.
  await link.focus();
  await page.keyboard.press("Enter");

  const dialog = page.locator(".detail-dialog");
  await expect(dialog).toContainText("default/db-0");
  await expect(dialog.locator(".containers-table")).toContainText("postgres:17");
  await expect(dialog.locator(".containers-table")).toContainText(
    "waiting: CrashLoopBackOff",
  );
  await expect(dialog.locator(".containers-table")).toContainText("OOMKilled");
  await expect(dialog.locator(".containers-table")).toContainText("(exit 137)");
  await expect(dialog.locator(".containers-table")).toContainText("wait-for-disk");
  await expect(dialog.locator(".events-table")).toContainText("BackOff");
  await expect(dialog.locator(".events-table")).toContainText("Scheduled");
  expect(
    await page.evaluate(() =>
      window.__k8s.calls.filter((c) => c.type === "kubernetes/pods/describe"),
    ),
  ).toEqual([
    {
      type: "kubernetes/pods/describe",
      entry_id: "entry_1",
      pod_name: "db-0",
      namespace: "default",
    },
  ]);

  await page.keyboard.press("Escape");
  await expect(dialog).toHaveCount(0);

  await link.click();
  await expect(dialog).toBeVisible();
  // A click inside the dialog keeps it open; one on the overlay closes it.
  await dialog.locator("h3").click();
  await expect(dialog).toBeVisible();
  await page.locator(".confirm-overlay").click({ position: { x: 5, y: 5 } });
  await expect(dialog).toHaveCount(0);
});

test("pod detail renders detail-only with the RBAC hint when events are forbidden", async ({
  page,
}) => {
  await page.goto(`${HARNESS}?events_error=forbidden`);
  await openTab(page, "Pods");
  await page.locator(".pod-link", { hasText: "db-0" }).click();

  const dialog = page.locator(".detail-dialog");
  await expect(dialog.locator(".containers-table")).toContainText("postgres:17");
  await expect(dialog.locator(".events-forbidden")).toContainText("events");
  await expect(dialog.locator(".events-forbidden a")).toHaveAttribute(
    "href",
    /RBAC\.md$/,
  );
  await expect(dialog.locator(".events-table")).toHaveCount(0);
});

test("pod logs forbidden error links the RBAC docs", async ({ page }) => {
  await page.goto(HARNESS);
  await page.evaluate(() => {
    window.__k8s.failCodes["kubernetes/pods/logs"] = "forbidden";
    window.__k8s.fail.add("kubernetes/pods/logs");
  });
  await openTab(page, "Pods");
  await page
    .locator("tr", { hasText: "db-0" })
    .locator('button[title="Show logs"]')
    .click();

  const error = page.locator(".logs-dialog .inline-error");
  await expect(error).toContainText("kubernetes/pods/logs failed");
  await expect(error.locator("a")).toHaveAttribute("href", /RBAC\.md$/);
});

test("pod detail notes failed events without the RBAC hint", async ({ page }) => {
  await page.goto(`${HARNESS}?events_error=events_failed`);
  await openTab(page, "Pods");
  await page.locator(".pod-link", { hasText: "db-0" }).click();

  const dialog = page.locator(".detail-dialog");
  await expect(dialog.locator(".containers-table")).toContainText("postgres:17");
  await expect(dialog.locator(".inline-error")).toHaveText("Failed to load events.");
  await expect(dialog.locator("a")).toHaveCount(0);
  await expect(dialog.locator(".events-table")).toHaveCount(0);
});

test("switching tabs leaves one live subscription", async ({ page }) => {
  await page.goto(HARNESS);
  for (const label of ["Pods", "Workloads", "Nodes", "Overview"]) {
    await openTab(page, label);
    await expect(page.locator(".tab[active]")).toHaveText(new RegExp(label));
  }
  await expect.poll(() => page.evaluate(() => window.__k8s.subscribers.length)).toBe(1);
});

test("pod detail failure shows an inline error", async ({ page }) => {
  await page.goto(`${HARNESS}?fail=kubernetes/pods/describe`);
  await openTab(page, "Pods");
  await page.locator(".pod-link", { hasText: "db-0" }).click();

  await expect(page.locator(".detail-dialog .inline-error")).toContainText(
    "kubernetes/pods/describe failed",
  );
});

test("pod detail Logs button opens the log dialog on the previous container of a restarted pod", async ({
  page,
}) => {
  await page.goto(HARNESS);
  await openTab(page, "Pods");
  await page.locator(".pod-link", { hasText: "db-0" }).click();
  await page.locator(".detail-dialog .detail-logs").click();

  await expect(page.locator(".detail-dialog")).toHaveCount(0);
  await expect(page.locator(".logs-output")).toBeVisible();
  await expect(page.locator(".logs-previous input")).toBeChecked();
  // The select must show the container the logs were fetched for.
  await expect(page.locator(".logs-dialog select.filter-select")).toHaveValue(
    "metrics-exporter",
  );
  const logCalls = await page.evaluate(() =>
    window.__k8s.calls.filter((c) => c.type === "kubernetes/pods/logs"),
  );
  expect(logCalls.at(-1)).toMatchObject({
    pod_name: "db-0",
    container: "metrics-exporter",
    previous: true,
  });
});

test("pod detail is open to non-admins but hides the Logs button", async ({ page }) => {
  await page.goto(`${HARNESS}?admin=0`);
  await openTab(page, "Pods");
  await page.locator(".pod-link", { hasText: "db-0" }).click();

  await expect(page.locator(".detail-dialog .containers-table")).toBeVisible();
  await expect(page.locator(".detail-dialog .detail-logs")).toHaveCount(0);
});

test("pod detail Logs on a pod without restarts starts on the current container", async ({
  page,
}) => {
  await page.goto(HARNESS);
  await openTab(page, "Pods");
  await page.locator(".pod-link", { hasText: "web-7d9f8b-abc12" }).click();
  await page.locator(".detail-dialog .detail-logs").click();

  await expect(page.locator(".logs-output")).toBeVisible();
  await expect(page.locator(".logs-previous input")).not.toBeChecked();
});

test("drain dialog sends the options and shows the service response", async ({
  page,
}) => {
  await page.goto(HARNESS);
  await openTab(page, "Nodes");
  await page.locator(".node-card .action-btn.drain").click();
  await page.locator(".drain-option", { hasText: "emptyDir" }).locator("input").check();
  await page.locator(".drain-timeout").fill("30");
  await page.locator("button.drain-action").click();

  await expect(page.locator(".drain-section.blocked")).toContainText("default/db-0");
  await expect(page.locator(".confirm-dialog")).toContainText(
    "kube-system/kube-proxy-x1y2z (DaemonSet)",
  );
  await expect(page.locator(".confirm-dialog")).toContainText(
    "default/debug (no controller)",
  );
  await expect(page.locator(".confirm-dialog")).toContainText("1 pod evicted");
  expect(await page.evaluate(() => window.__k8s.services)).toEqual([
    {
      domain: "kubernetes",
      service: "drain_node",
      data: {
        node_name: "node-1",
        entry_id: "entry_1",
        ignore_daemonsets: true,
        delete_emptydir_data: true,
        force: false,
        timeout: 30,
      },
    },
  ]);

  await page.keyboard.press("Escape");
  await expect(page.locator(".confirm-dialog")).toHaveCount(0);
});

test("drain dialog's force checkbox is sent to the service", async ({ page }) => {
  await page.goto(HARNESS);
  await openTab(page, "Nodes");
  await page.locator(".node-card .action-btn.drain").click();
  await page
    .locator(".drain-option", { hasText: "without a controller" })
    .locator("input")
    .check();
  await page.locator("button.drain-action").click();

  await expect(page.locator(".confirm-dialog")).toContainText("1 pod evicted");
  expect(await page.evaluate(() => window.__k8s.services)).toEqual([
    {
      domain: "kubernetes",
      service: "drain_node",
      data: {
        node_name: "node-1",
        entry_id: "entry_1",
        ignore_daemonsets: true,
        delete_emptydir_data: false,
        force: true,
        timeout: 120,
      },
    },
  ]);
});

test("Escape closes the drain dialog without calling the service", async ({ page }) => {
  await page.goto(HARNESS);
  await openTab(page, "Nodes");
  await page.locator(".node-card .action-btn.drain").click();
  await expect(page.locator(".confirm-dialog")).toBeVisible();

  await page.keyboard.press("Escape");

  await expect(page.locator(".confirm-dialog")).toHaveCount(0);
  expect(await page.evaluate(() => window.__k8s.services)).toEqual([]);
});

test("network tab shows ingresses, HTTPRoutes, and services", async ({ page }) => {
  await page.goto(HARNESS);
  await openTab(page, "Network");

  await expect(
    page.locator("h2.section-title", { hasText: "Ingresses" }),
  ).toBeVisible();
  await expect(
    page.locator("h2.section-title", { hasText: "HTTPRoutes" }),
  ).toBeVisible();
  await expect(page.locator("h2.section-title", { hasText: "Services" })).toBeVisible();

  const httprouteRow = page.locator(".network-table tr", { hasText: "eg" });
  await expect(httprouteRow).toContainText("web.example.com");
  await expect(httprouteRow.locator("a.url-link")).toHaveAttribute(
    "href",
    "https://web.example.com",
  );
  await expect(httprouteRow.locator(".badge-ready")).toHaveText("Accepted");
});

test("network tab hides the HTTPRoutes section without routes", async ({ page }) => {
  await page.goto(`${HARNESS}?empty=kubernetes/httproutes/list`);
  await openTab(page, "Network");

  await expect(
    page.locator("h2.section-title", { hasText: "Ingresses" }),
  ).toBeVisible();
  await expect(page.locator("h2.section-title", { hasText: "HTTPRoutes" })).toHaveCount(
    0,
  );

  await page.locator("select.filter-select").selectOption("HTTPRoute");
  await expect(page.locator(".empty")).toHaveText("No HTTPRoutes found.");
});

test("network tab lists certificates with issuer, expiry and status", async ({
  page,
}) => {
  await page.goto(HARNESS);
  await openTab(page, "Network");

  await expect(
    page.locator("h2.section-title", { hasText: "Certificates" }),
  ).toBeVisible();
  const ready = page.locator(".network-table tr", { hasText: "web-tls" });
  await expect(ready).toContainText("ClusterIssuer/letsencrypt");
  await expect(ready).toContainText("web.example.com");
  await expect(ready).toContainText(/in \d+d/);
  await expect(ready.locator(".badge-ready")).toHaveText("Ready");
  const overdue = page.locator(".network-table tr", { hasText: "api-tls" });
  await expect(overdue.locator(".badge-failed")).toHaveText("Renewal Overdue");
});

test("network tab hides the Certificates section without cert-manager", async ({
  page,
}) => {
  await page.goto(`${HARNESS}?empty=kubernetes/certificates/list`);
  await openTab(page, "Network");

  await expect(
    page.locator("h2.section-title", { hasText: "Ingresses" }),
  ).toBeVisible();
  await expect(
    page.locator("h2.section-title", { hasText: "Certificates" }),
  ).toHaveCount(0);

  await page.locator("select.filter-select").selectOption("Certificate");
  await expect(page.locator(".empty")).toHaveText("No certificates found.");
});

test("overview certificate alert opens the Network tab filtered to it", async ({
  page,
}) => {
  await page.goto(HARNESS);
  const card = page.locator(".alert-card", { hasText: "default/api-tls" });
  await expect(card).toContainText("Renewal overdue");
  await card.click();
  await expect(page.locator(".tab[active]")).toHaveText(/Network/);
  await expect(page.locator(".search-input")).toHaveValue("api-tls");
  await expect(
    page.locator("h2.section-title", { hasText: "Certificates" }),
  ).toBeVisible();
  await expect(page.locator("h2.section-title", { hasText: "Services" })).toHaveCount(
    0,
  );
  await expect(page.locator(".network-table tbody tr")).toHaveCount(1);
});

test("network type filter narrows to a single section", async ({ page }) => {
  await page.goto(HARNESS);
  await openTab(page, "Network");

  await page.locator("select.filter-select").selectOption("HTTPRoute");

  await expect(
    page.locator("h2.section-title", { hasText: "HTTPRoutes" }),
  ).toBeVisible();
  await expect(page.locator("h2.section-title", { hasText: "Ingresses" })).toHaveCount(
    0,
  );
  await expect(page.locator("h2.section-title", { hasText: "Services" })).toHaveCount(
    0,
  );
});

test("reload restores the tab and its filters from the URL", async ({ page }) => {
  await page.goto(HARNESS);
  await openTab(page, "Pods");
  await page.locator(".search-input").fill("db");
  await page.locator(".filter-chip", { hasText: "Running" }).click();
  await page.getByRole("button", { name: "Restarts" }).click();
  await page.getByRole("button", { name: "Restarts" }).click();
  expect(await pathAndQuery(page)).toBe(
    "/e2e/harness.html/pods?search=db&phase=Running&sort=restarts&dir=desc",
  );

  await page.reload();
  await expect(page.locator(".tab[active]")).toHaveText(/Pods/);
  await expect(page.locator(".search-input")).toHaveValue("db");
  await expect(page.locator(".filter-chip[active]")).toHaveText("Running");
  expect(await pathAndQuery(page)).toBe(
    "/e2e/harness.html/pods?search=db&phase=Running&sort=restarts&dir=desc",
  );
});

test("back returns to the previous tab and typing adds no history entries", async ({
  page,
}) => {
  await page.goto(HARNESS);
  await openTab(page, "Nodes");
  await openTab(page, "Pods");
  const before = await page.evaluate(() => history.length);
  await page.locator(".search-input").pressSequentially("worker");
  expect(await page.evaluate(() => history.length)).toBe(before);

  await page.goBack();
  await expect(page.locator(".tab[active]")).toHaveText(/Nodes/);
  await page.goBack();
  await expect(page.locator(".tab[active]")).toHaveText(/Overview/);
  await page.goForward();
  await expect(page.locator(".tab[active]")).toHaveText(/Nodes/);
});

test("settings tab lists each cluster's configuration", async ({ page }) => {
  await page.goto(`${HARNESS}/settings`);
  await expect(page.locator(".entry-name")).toHaveText("test-cluster");
  await expect(page.locator(".badge-healthy")).toHaveText("Connected");
  const row = (label: string) =>
    page.locator(".setting-row", { hasText: label }).first();
  await expect(row("Host")).toContainText("k8s.example.com");
  await expect(row("Port")).toContainText("6443");
  await expect(row("Update Mode")).toContainText("Watch (real-time)");
  await expect(row("Sidebar Panel")).toContainText("Enabled");
  await expect(row("Admin-only Panel")).toContainText("Disabled");
  await expect(row("Pod Logs (experimental)")).toContainText("Enabled");
  await expect(
    page.getByRole("button", { name: /Configure Integration/ }),
  ).toBeVisible();
});

test("deep links apply search, namespace and the Problems phase", async ({ page }) => {
  await page.goto(`${HARNESS}/pods?phase=problems&namespace=default`);
  await expect(page.locator(".filter-chip[active]")).toContainText("Problems");
  await expect(page.locator("select.filter-select")).toHaveValue("default");
  await expect(page.locator("tbody tr")).toHaveCount(1);
  await expect(page.locator("tbody tr")).toContainText("crash-5c8d7-xyz99");
});

test("unknown query values fall back to all", async ({ page }) => {
  await page.goto(`${HARNESS}/pods?phase=bogus&namespace=gone&sort=nope&dir=up`);
  await expect(page.locator(".filter-chip[active]")).toHaveText("All");
  await expect(page.locator("tbody tr").first()).toBeVisible();
  await expect(page.locator("select.filter-select")).toHaveValue("all");
  await expect(page.locator("tbody tr")).not.toHaveCount(0);
  expect(await pathAndQuery(page)).toBe("/e2e/harness.html/pods");
});

test("an unknown path shows the overview", async ({ page }) => {
  await page.goto(`${HARNESS}/nonsense`);
  await expect(page.locator(".tab[active]")).toHaveText(/Overview/);
});

test("nodes, workloads and network read their filters from the URL", async ({
  page,
}) => {
  await page.goto(`${HARNESS}/nodes?status=ready`);
  await expect(page.locator(".filter-chip[active]")).toHaveText("Ready");
  await page.goto(`${HARNESS}/workloads?category=jobs&status=degraded&search=backup`);
  await expect(page.locator(".search-input")).toHaveValue("backup");
  await expect(page.locator(".filter-chip[active]")).toHaveText("Degraded");
  await page.goto(`${HARNESS}/network?type=NodePort&search=x`);
  await expect(page.locator(".search-input")).toHaveValue("x");
  await expect(page.locator("select.filter-select")).toHaveValue("NodePort");
});

const pushLink = (page: Page, url: string) =>
  // What HA's navigate() does when a notification link opens while the panel is shown.
  page.evaluate((u) => {
    history.pushState(null, "", u);
    window.dispatchEvent(
      new CustomEvent("location-changed", { detail: { replace: false } }),
    );
  }, url);

test("a link to the current tab replaces the filters", async ({ page }) => {
  await page.goto(`${HARNESS}/pods?search=db`);
  await expect(page.locator(".search-input")).toHaveValue("db");

  await pushLink(page, "/e2e/harness.html/pods?phase=problems");
  await expect(page.locator(".filter-chip[active]")).toContainText("Problems");
  await expect(page.locator(".search-input")).toHaveValue("");
  expect(await pathAndQuery(page)).toBe("/e2e/harness.html/pods?phase=problems");
});

test("clicking the current tab clears its filters", async ({ page }) => {
  await page.goto(`${HARNESS}/pods?search=db`);
  await openTab(page, "Pods");
  await expect(page.locator(".search-input")).toHaveValue("");
  expect(await pathAndQuery(page)).toBe("/e2e/harness.html/pods");
});

test("back and forward within one tab restore its filters", async ({ page }) => {
  await page.goto(`${HARNESS}/pods?search=db`);
  await pushLink(page, "/e2e/harness.html/pods?search=web");
  await expect(page.locator(".search-input")).toHaveValue("web");
  await page.goBack();
  await expect(page.locator(".search-input")).toHaveValue("db");
  await page.goForward();
  await expect(page.locator(".search-input")).toHaveValue("web");
});

test("two clusters share one filter bar", async ({ page }) => {
  await page.goto(`${HARNESS}/pods?clusters=2`);
  await expect(page.locator(".cluster-name")).toHaveCount(2);
  await expect(page.locator(".search-input")).toHaveCount(1);
  await expect(page.locator(".column-toggle-btn")).toHaveCount(1);
  const ns = page.locator("select.filter-select");
  await expect(ns.locator('option[value="default"]')).toHaveCount(1);
  await expect(ns.locator('option[value="staging"]')).toHaveCount(1);
  const all = await page.locator("tbody tr").count();
  await page.locator(".search-input").fill("db-0");
  await expect(page.locator("tbody tr")).toHaveCount(2);
  expect(all).toBeGreaterThan(2);

  await page.goto(`${HARNESS}/workloads?clusters=2`);
  await expect(page.locator(".cluster-name")).toHaveCount(2);
  await expect(page.locator(".search-input")).toHaveCount(1);
  const wns = page.locator("select.filter-select");
  await expect(wns.locator('option[value="default"]')).toHaveCount(1);
  await expect(wns.locator('option[value="staging"]')).toHaveCount(1);
  await expect(page.locator(".workload-card", { hasText: "web" })).toHaveCount(2);
  await page.locator(".search-input").fill("db");
  await expect(page.locator(".workload-card", { hasText: "web" })).toHaveCount(0);
  await expect(page.locator(".workload-card", { hasText: "db" })).toHaveCount(2);

  await page.goto(`${HARNESS}/nodes?clusters=2`);
  await expect(page.locator(".cluster-name")).toHaveCount(2);
  await expect(page.locator(".search-input")).toHaveCount(1);
  await expect(page.locator(".node-card")).toHaveCount(2);
  await page.locator(".search-input").fill("no-such-node");
  await expect(page.locator(".node-card")).toHaveCount(0);
  await expect(page.locator(".empty")).toHaveCount(2);
});

test("overview namespace table includes ingresses and services", async ({ page }) => {
  await page.goto(HARNESS);
  await page.locator(".section-header", { hasText: "Namespaces" }).click();
  const table = page.locator(".ns-table");
  const headers = table.locator("thead th");
  const services = headers.filter({ hasText: /^Services$/ });
  await expect(headers.filter({ hasText: /^Ingresses$/ })).toHaveCount(1);
  await expect(services).toHaveCount(1);
  const col = await headers.evaluateAll((ths) =>
    ths.findIndex((th) => th.textContent?.trim() === "Services"),
  );
  const row = table.locator("tbody tr", { hasText: "kube-system" });
  await expect(row.locator("td").nth(col)).toHaveText("1");
});

test("workloads say when no workload matches", async ({ page }) => {
  await page.goto(`${HARNESS}/workloads`);
  await page.locator(".search-input").fill("zzz");
  await expect(page.getByText("No workloads match your filters.")).toBeVisible();
});
