import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  timeout: 120_000,
  expect: {
    timeout: 10_000,
  },
  retries: 0,
  reporter: [["list"], ["html", { open: "never", outputFolder: "playwright-report-qa" }]],
  outputDir: "test-results-qa",
  use: {
    baseURL: "http://127.0.0.1:8012",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
    headless: true,
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: {
    command:
      "PYTHON_BIN=.venv/bin/python; if [ ! -x \"$PYTHON_BIN\" ]; then PYTHON_BIN=python; fi; rm -f /tmp/perle_playwright_qa.sqlite3 && $PYTHON_BIN manage.py migrate --noinput && $PYTHON_BIN manage.py seed_demo --reset && $PYTHON_BIN manage.py runserver 127.0.0.1:8012 --noreload",
    url: "http://127.0.0.1:8012",
    reuseExistingServer: false,
    timeout: 120_000,
    env: {
      DEBUG: "1",
      DB_SSL_REQUIRE: "0",
      DB_CONN_MAX_AGE: "0",
      DJANGO_SECRET_KEY:
        "playwright-e2e-qa-secret-key-with-more-than-fifty-safe-random-chars-123456",
      WHATSAPP_PHONE: "",
      DATABASE_URL: "sqlite:////tmp/perle_playwright_qa.sqlite3",
      ALLOWED_HOSTS: "127.0.0.1,localhost",
      CSRF_TRUSTED_ORIGINS: "http://127.0.0.1:8012,http://localhost:8012",
    },
  },
});
