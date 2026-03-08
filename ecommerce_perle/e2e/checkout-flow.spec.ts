import { expect, test } from "@playwright/test";

async function completeCheckoutFlow(page: import("@playwright/test").Page) {
  await page.goto("/");
  await expect(page.getByTestId("products-grid")).toBeVisible();

  const addToCartButton = page.locator("[data-add-cart]").first();
  await expect(addToCartButton).toBeVisible();
  const addToCartResponsePromise = page.waitForResponse((response) => {
    return (
      response.request().method() === "POST" &&
      response.url().includes("/api/cart/items/")
    );
  });
  await addToCartButton.click();
  const addToCartResponse = await addToCartResponsePromise;
  expect(addToCartResponse.status()).toBe(201);

  await expect(page.locator("#cart-count")).not.toHaveText("0");
  await page.getByTestId("nav-cart").click();
  await expect(page.getByTestId("cart-page")).toBeVisible();
  await expect(page.locator("#cart-total-main")).toContainText("USD");
  await expect(page.locator("main")).not.toContainText("COP");

  await page.getByTestId("go-checkout").click();
  await expect(page.getByTestId("checkout-page")).toBeVisible();
  await expect(page.locator("#cart-total")).toContainText("USD");

  await page.fill("#checkout-full-name", "Cliente E2E");
  await page.fill("#checkout-email", "cliente-e2e@example.com");
  await page.fill("#checkout-phone", "3001234567");
  await page.fill("#checkout-line1", "Calle E2E 123");
  await page.fill("#checkout-city", "Bogota");
  await page.fill("#checkout-state", "DC");

  await page.getByTestId("confirm-order").click();
  await expect(page.getByTestId("confirmation-page")).toBeVisible();
  await expect(page.locator(".summary-row.total")).toContainText("USD");
  await expect(page.locator("main")).not.toContainText("COP");
}

test("flujo completo: catálogo -> carrito -> checkout -> confirmación", async ({ page }) => {
  await completeCheckoutFlow(page);
  await expect(page.locator("text=Pedido confirmado")).toBeVisible();
});

test("sin WHATSAPP_PHONE no se renderizan enlaces wa.me", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator('a[href*="wa.me"]')).toHaveCount(0);

  await completeCheckoutFlow(page);
  await expect(page.locator('a[href*="wa.me"]')).toHaveCount(0);
  await expect(page.locator("[data-testid='confirmation-wa']")).toHaveCount(0);
});
