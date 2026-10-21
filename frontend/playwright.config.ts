import { defineConfig, devices } from "@playwright/test";

// Drives the panel mounted by e2e/harness.html against a fake `hass`;
// no Home Assistant or cluster involved. See docs/DEVELOPMENT.md.
export default defineConfig({
  testDir: "e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  use: {
    baseURL: "http://localhost:5173",
    trace: "retain-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    command: "npx vite --port 5173 --strictPort",
    url: "http://localhost:5173/e2e/harness.html",
    reuseExistingServer: !process.env.CI,
  },
});
