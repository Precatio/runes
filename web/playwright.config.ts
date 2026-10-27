// Smoke tests in a real browser (e2e/): the pages load, show what they should and throw no uncaught errors.
// Locally they run against the app that is already running (npm run local, port 3000); in CI the app is built and
// started first (webServer). Nothing here talks to the analysis engine or Firestore.
//
//   npx playwright test            (PLAYWRIGHT_BASE_URL to point elsewhere)
import { defineConfig, devices } from "@playwright/test";

const baseURL = process.env.PLAYWRIGHT_BASE_URL || "http://127.0.0.1:3000";

export default defineConfig({
  testDir: "e2e",
  timeout: 60_000,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: process.env.CI ? [["list"], ["github"]] : "list",
  use: { baseURL, trace: "retain-on-failure" },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: process.env.CI
    ? { command: "npm run build && npm run start -- -p 3000", url: baseURL, timeout: 600_000, reuseExistingServer: false }
    : undefined,
});
