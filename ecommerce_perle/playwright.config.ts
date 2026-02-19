import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  timeout: 120_000,
  expect: {
    timeout: 10_000,
  },
  retries: process.env.CI ? 1 : 0,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: "http://127.0.0.1:8000",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: {
    command:
      "python manage.py migrate --noinput && python manage.py seed_demo && python manage.py runserver 127.0.0.1:8000 --noreload",
    url: "http://127.0.0.1:8000",
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
    env: {
      DEBUG: "1",
      DJANGO_SECRET_KEY:
        "playwright-e2e-secret-key-with-more-than-fifty-safe-random-chars-123456",
      WHATSAPP_PHONE: "",
      DATABASE_URL: "sqlite:///db.sqlite3",
      ALLOWED_HOSTS: "127.0.0.1,localhost",
      CSRF_TRUSTED_ORIGINS: "http://127.0.0.1:8000,http://localhost:8000",
    },
  },
});
