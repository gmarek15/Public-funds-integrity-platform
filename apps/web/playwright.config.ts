import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? [["list"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL: "http://127.0.0.1:3100",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
  webServer: [
    {
      command: "..\\api\\.venv\\Scripts\\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8010",
      port: 8010,
      reuseExistingServer: false,
      cwd: `${__dirname}\\..\\api`,
      timeout: 120 * 1000,
    },
    {
      command: "cmd /c npx.cmd next dev --hostname 127.0.0.1 --port 3100",
      port: 3100,
      reuseExistingServer: false,
      cwd: __dirname,
      env: {
        NEXT_PUBLIC_API_BASE_URL: "http://127.0.0.1:8010/api/v1",
      },
      timeout: 120 * 1000,
    },
  ],
});
