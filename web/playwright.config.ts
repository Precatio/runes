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
  // --in-process-gpu: on macOS the GPU process that the test runner's Chromium starts dies at once ("Invalid file
  // descriptor to ICU data", exit code 5); after six restarts Chromium gives up ("GPU process isn't usable. Goodbye.")
  // and the whole browser exits, so any page with a canvas (e.g. /stenanalys) looked as if it closed itself. Plain
  // scripts with the same browser build are not affected. Running the GPU code inside the browser process avoids it.
  use: { baseURL, trace: "retain-on-failure", launchOptions: { args: ["--in-process-gpu"] } },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: process.env.CI
    ? { command: "npm run build && npm run start -- -p 3000", url: baseURL, timeout: 600_000, reuseExistingServer: false }
    : undefined,
});
