const couponStorageKey = "perleCouponCode";

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) {
    return parts.pop().split(";").shift();
  }
  return "";
}

function formatUSDFromCents(value) {
  const amount = (Number(value) || 0) / 100;
  const formatted = new Intl.NumberFormat("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
  return `USD ${formatted}`;
}

function normalizeToastType(type) {
  if (type === "success" || type === "warn" || type === "danger" || type === "info") {
    return type;
  }
  return "info";
}

function getToastRegion() {
  let region = document.getElementById("toast-region");
  if (!region) {
    region = document.createElement("div");
    region.id = "toast-region";
    region.className = "toast-region";
    region.setAttribute("aria-live", "polite");
    region.setAttribute("aria-atomic", "true");
    document.body.appendChild(region);
  }

  const legacyToast = region.querySelector("#app-toast");
  if (legacyToast) {
    legacyToast.remove();
  }

  return region;
}

function toast(type, message) {
  if (!message) return;

  const safeType = normalizeToastType(type);
  const region = getToastRegion();
  const node = document.createElement("div");
  node.className = `toast toast-${safeType}`;
  node.setAttribute("role", "status");

  const icon = document.createElement("span");
  if (safeType === "success") {
    icon.textContent = "✓";
  } else if (safeType === "warn") {
    icon.textContent = "!";
  } else if (safeType === "danger") {
    icon.textContent = "×";
  } else {
    icon.textContent = "i";
  }

  const text = document.createElement("span");
  text.textContent = String(message);

  node.appendChild(icon);
  node.appendChild(text);
  region.appendChild(node);

  window.requestAnimationFrame(() => {
    node.classList.add("show");
  });

  window.setTimeout(() => {
    node.classList.remove("show");
    window.setTimeout(() => node.remove(), 220);
  }, 2800);
}

function getErrorMessage(payload, fallback = "No se pudo completar la acción.") {
  if (!payload || typeof payload !== "object") return fallback;

  if (typeof payload.error === "string" && payload.error.trim()) {
    return payload.error.trim();
  }

  if (typeof payload.detail === "string" && payload.detail.trim()) {
    return payload.detail.trim();
  }

  return fallback;
}

async function apiRequest(url, options = {}) {
  const defaultHeaders = {
    "Content-Type": "application/json",
    "X-CSRFToken": getCookie("csrftoken"),
  };

  const requestOptions = {
    credentials: "same-origin",
    ...options,
    headers: {
      ...defaultHeaders,
      ...(options.headers || {}),
    },
  };

  const response = await fetch(url, requestOptions);
  let payload = {};
  try {
    payload = await response.json();
  } catch (_) {
    payload = {};
  }
  return { response, payload };
}

async function fetchCart() {
  const response = await fetch("/api/cart/", { credentials: "same-origin" });
  if (!response.ok) {
    throw new Error("No se pudo consultar carrito.");
  }
  return response.json();
}

function updateSummaryNodes(payload) {
  const items = Array.isArray(payload.items) ? payload.items : [];
  const count = items.reduce((acc, item) => acc + (Number(item.quantity) || 0), 0);
  const subtotalCents = payload.totals?.subtotal_cents ?? payload.totals?.subtotal ?? 0;
  const discountCents = payload.totals?.discount_total_cents ?? payload.totals?.discount_total ?? 0;
  const grandTotalCents = payload.totals?.grand_total_cents ?? payload.totals?.grand_total ?? 0;

  const countNode = document.getElementById("cart-count");
  const totalNode = document.getElementById("cart-total");
  if (countNode) countNode.textContent = String(count);
  if (totalNode) totalNode.textContent = count > 0 ? formatUSDFromCents(grandTotalCents) : "";

  const subtotalNode = document.getElementById("cart-subtotal");
  const discountNode = document.getElementById("cart-discount");
  const grandTotalNode = document.getElementById("cart-total-main");

  if (subtotalNode) subtotalNode.textContent = formatUSDFromCents(subtotalCents);
  if (discountNode) discountNode.textContent = formatUSDFromCents(discountCents);
  if (grandTotalNode) grandTotalNode.textContent = formatUSDFromCents(grandTotalCents);

  const itemsCountNode = document.getElementById("cart-items-count");
  if (itemsCountNode) {
    const referencesLabel = items.length === 1 ? "referencia" : "referencias";
    itemsCountNode.textContent = `${items.length} ${referencesLabel}`;
  }
}

function setCartStatus(message) {
  const node = document.getElementById("cart-status");
  if (node && message) {
    node.textContent = message;
  }
}

function collectRenderedCartImages() {
  const map = {};
  document.querySelectorAll("#cart-items tr[data-item-id]").forEach((row) => {
    const id = Number(row.dataset.itemId);
    if (!id) return;

    const img = row.querySelector(".cart-item-thumb");
    const src = img && img.tagName === "IMG" ? img.getAttribute("src") : "";
    if (src && isSafeImageUrl(src)) {
      map[id] = {
        src,
        alt: img.getAttribute("alt") || "Producto",
      };
    }
  });
  return map;
}

function normalizeText(value, fallback = "") {
  if (value === null || value === undefined) return fallback;
  return String(value);
}

function isSafeImageUrl(rawUrl) {
  if (!rawUrl) return false;
  try {
    const parsed = new URL(rawUrl, window.location.origin);
    const isHttp = parsed.protocol === "http:" || parsed.protocol === "https:";
    if (!isHttp) return false;
    return parsed.origin === window.location.origin || parsed.protocol === "https:";
  } catch (_) {
    return false;
  }
}

function buildCartItemImage(itemImage) {
  if (itemImage && isSafeImageUrl(itemImage.src)) {
    const image = document.createElement("img");
    image.className = "cart-item-thumb";
    image.loading = "lazy";
    image.alt = normalizeText(itemImage.alt, "Producto");
    image.src = itemImage.src;
    return image;
  }

  const fallback = document.createElement("div");
  fallback.className = "cart-item-thumb product-image-fallback";
  fallback.textContent = "Perle";
  return fallback;
}

function createCartRowNode(item, imageMap) {
  const row = document.createElement("tr");
  row.dataset.itemId = String(Number(item.id) || 0);

  const detailsCell = document.createElement("td");
  const detailsWrapper = document.createElement("div");
  detailsWrapper.className = "cart-item-main";

  const itemImage = imageMap[item.id];
  detailsWrapper.appendChild(buildCartItemImage(itemImage));

  const textWrapper = document.createElement("div");
  const title = document.createElement("strong");
  title.textContent = normalizeText(item.product_name, "Producto");
  textWrapper.appendChild(title);

  const variantInfo = document.createElement("p");
  variantInfo.className = "muted";
  variantInfo.textContent = `${normalizeText(item.size, "")} / ${normalizeText(item.color, "")}`;
  textWrapper.appendChild(variantInfo);
  detailsWrapper.appendChild(textWrapper);
  detailsCell.appendChild(detailsWrapper);
  row.appendChild(detailsCell);

  const qtyCell = document.createElement("td");
  const qtyStepper = document.createElement("div");
  qtyStepper.className = "qty-stepper";

  const decreaseButton = document.createElement("button");
  decreaseButton.type = "button";
  decreaseButton.className = "btn btn-ghost";
  decreaseButton.dataset.cartDecrease = String(Number(item.id) || 0);
  decreaseButton.setAttribute("aria-label", "Reducir cantidad");
  decreaseButton.textContent = "−";
  qtyStepper.appendChild(decreaseButton);

  const qtyValue = document.createElement("span");
  qtyValue.dataset.cartQty = String(Number(item.id) || 0);
  qtyValue.textContent = String(Number(item.quantity) || 0);
  qtyStepper.appendChild(qtyValue);

  const increaseButton = document.createElement("button");
  increaseButton.type = "button";
  increaseButton.className = "btn btn-ghost";
  increaseButton.dataset.cartIncrease = String(Number(item.id) || 0);
  increaseButton.setAttribute("aria-label", "Aumentar cantidad");
  increaseButton.textContent = "+";
  qtyStepper.appendChild(increaseButton);

  qtyCell.appendChild(qtyStepper);
  row.appendChild(qtyCell);

  const unitPriceCell = document.createElement("td");
  const unitPriceCents = item.unit_price_cents ?? item.unit_price ?? 0;
  unitPriceCell.textContent = formatUSDFromCents(unitPriceCents);
  row.appendChild(unitPriceCell);

  const actionsCell = document.createElement("td");
  const removeButton = document.createElement("button");
  removeButton.type = "button";
  removeButton.className = "btn btn-danger";
  removeButton.dataset.cartRemove = String(Number(item.id) || 0);
  removeButton.setAttribute("aria-label", "Eliminar producto");
  removeButton.textContent = "Eliminar";
  actionsCell.appendChild(removeButton);
  row.appendChild(actionsCell);

  return row;
}

function renderCartPage(payload) {
  const cartPage = document.querySelector("[data-cart-page]");
  if (!cartPage) return;

  updateSummaryNodes(payload);

  const items = Array.isArray(payload.items) ? payload.items : [];
  const emptyState = document.getElementById("cart-empty");
  const content = document.getElementById("cart-content");
  const tbody = document.getElementById("cart-items");

  if (emptyState) emptyState.hidden = items.length > 0;
  if (content) content.hidden = items.length < 1;
  if (!tbody) return;

  const imageMap = collectRenderedCartImages();
  tbody.textContent = "";
  const fragment = document.createDocumentFragment();
  items.forEach((item) => {
    fragment.appendChild(createCartRowNode(item, imageMap));
  });
  tbody.appendChild(fragment);

  if (items.length < 1) {
    setCartStatus("Tu carrito está vacío.");
    return;
  }

  const label = items.length === 1 ? "referencia activa" : "referencias activas";
  setCartStatus(`Tu carrito tiene ${items.length} ${label}.`);
}

async function refreshCartBadge({ render = false } = {}) {
  try {
    const payload = await fetchCart();
    updateSummaryNodes(payload);
    if (render) renderCartPage(payload);
  } catch (_) {
    // Silent fallback for badge refresh
  }
}

function setButtonLoading(button, isLoading, loadingText) {
  if (!button) return;

  const labelNode = button.querySelector("[data-button-label]");
  const spinnerNode = button.querySelector("[data-button-spinner]");

  if (isLoading) {
    const previous = labelNode ? labelNode.textContent : button.textContent;
    if (!button.dataset.previousLabel && previous) {
      button.dataset.previousLabel = previous;
    }

    const nextLabel = loadingText || button.dataset.loadingText || "Procesando...";
    if (labelNode) {
      labelNode.textContent = nextLabel;
    } else {
      button.textContent = nextLabel;
    }

    if (spinnerNode) {
      spinnerNode.hidden = false;
    }

    button.disabled = true;
    button.setAttribute("aria-busy", "true");
    return;
  }

  const previousLabel = button.dataset.previousLabel;
  if (previousLabel) {
    if (labelNode) {
      labelNode.textContent = previousLabel;
    } else {
      button.textContent = previousLabel;
    }
  }

  if (spinnerNode) {
    spinnerNode.hidden = true;
  }

  button.disabled = false;
  button.removeAttribute("aria-busy");
}

async function mutateCart(url, method, body = {}) {
  try {
    const { response, payload } = await apiRequest(url, {
      method,
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const message = getErrorMessage(payload, "No se pudo actualizar el carrito.");
      toast("danger", message);
      return null;
    }

    return payload;
  } catch (_) {
    toast("danger", "Error de red al actualizar el carrito.");
    return null;
  }
}

async function addToCart(variantId, button) {
  setButtonLoading(button, true, "Añadiendo...");
  const payload = await mutateCart("/api/cart/items/", "POST", {
    variant_id: variantId,
    quantity: 1,
  });
  setButtonLoading(button, false);

  if (!payload) return;

  updateSummaryNodes(payload);
  renderCartPage(payload);
  toast("success", "Producto agregado a la bolsa.");
}

async function updateCartItem(itemId, quantity, button) {
  setButtonLoading(button, true);
  const payload = await mutateCart(`/api/cart/items/${itemId}/`, "PATCH", { quantity });
  setButtonLoading(button, false);
  return payload;
}

async function removeCartItem(itemId, button) {
  setButtonLoading(button, true);
  const payload = await mutateCart(`/api/cart/items/${itemId}/`, "DELETE", {});
  setButtonLoading(button, false);
  return payload;
}

async function clearCart(button) {
  setButtonLoading(button, true, "Vaciando...");
  const payload = await mutateCart("/api/cart/clear/", "POST", {});
  setButtonLoading(button, false);
  return payload;
}

function getSafeConfirmationUrl(rawUrl) {
  if (!rawUrl) return "";
  try {
    const parsed = new URL(rawUrl, window.location.origin);
    const isHttp = parsed.protocol === "http:" || parsed.protocol === "https:";
    if (!isHttp || parsed.origin !== window.location.origin) return "";
    return `${parsed.pathname}${parsed.search}${parsed.hash}`;
  } catch (_) {
    return "";
  }
}

function getSafeWhatsappUrl(rawUrl) {
  if (!rawUrl) return "";
  try {
    const parsed = new URL(rawUrl);
    const isHttp = parsed.protocol === "http:" || parsed.protocol === "https:";
    const allowedHost = parsed.hostname === "wa.me" || parsed.hostname === "api.whatsapp.com";
    return isHttp && allowedHost ? parsed.toString() : "";
  } catch (_) {
    return "";
  }
}

function getAlertClassByType(type) {
  if (type === "success") return "alert alert-success";
  if (type === "warn") return "alert alert-warn";
  if (type === "danger") return "alert alert-danger";
  return "alert alert-info";
}

function showCheckoutAlert(type, message) {
  const alertNode = document.getElementById("checkout-alert");
  if (!alertNode) return;

  if (!message) {
    alertNode.hidden = true;
    alertNode.textContent = "";
    alertNode.className = "alert alert-info";
    return;
  }

  alertNode.hidden = false;
  alertNode.className = getAlertClassByType(type);
  alertNode.textContent = message;
  alertNode.focus();
}

function clearFieldErrors(form) {
  if (!form) return;

  form.querySelectorAll("[data-field-error]").forEach((node) => {
    node.textContent = "";
  });
}

function renderFieldErrors(form, payload) {
  if (!form || !payload || typeof payload !== "object") return false;

  let hasFieldErrors = false;
  Object.entries(payload).forEach(([field, value]) => {
    if (["error", "detail", "code", "non_field_errors"].includes(field)) {
      return;
    }

    const holder = form.querySelector(`[data-field-error="${field}"]`);
    if (!holder) return;

    if (Array.isArray(value)) {
      holder.textContent = value.filter(Boolean).join(" ");
    } else if (typeof value === "string") {
      holder.textContent = value;
    }

    if (holder.textContent.trim()) {
      hasFieldErrors = true;
    }
  });

  const nonField = payload.non_field_errors;
  if (Array.isArray(nonField) && nonField.length) {
    showCheckoutAlert("danger", nonField.join(" "));
    hasFieldErrors = true;
  }

  return hasFieldErrors;
}

function renderCheckoutResult(holder, confirmationUrl, whatsappUrl) {
  if (!holder) return;

  const safeConfirmationUrl = getSafeConfirmationUrl(confirmationUrl);
  const safeWhatsappUrl = getSafeWhatsappUrl(whatsappUrl);

  holder.textContent = "";
  holder.classList.remove("error");
  holder.classList.add("success");

  if (safeConfirmationUrl) {
    const confirmationLink = document.createElement("a");
    confirmationLink.href = safeConfirmationUrl;
    confirmationLink.textContent = "Ver confirmación";
    holder.appendChild(confirmationLink);
  }

  if (safeWhatsappUrl) {
    if (holder.childNodes.length > 0) {
      holder.appendChild(document.createTextNode(" · "));
    }
    const waLink = document.createElement("a");
    waLink.href = safeWhatsappUrl;
    waLink.rel = "noopener noreferrer";
    waLink.target = "_blank";
    waLink.textContent = "Finalizar por WhatsApp";
    holder.appendChild(waLink);
  }

  if (!safeConfirmationUrl && !safeWhatsappUrl) {
    holder.textContent = "Pedido confirmado correctamente.";
  }
}

function setupCartCouponInput() {
  const cartCouponInput = document.getElementById("cart-coupon");
  if (!cartCouponInput) return;

  const feedback = document.getElementById("cart-coupon-feedback");
  cartCouponInput.value = localStorage.getItem(couponStorageKey) || "";

  cartCouponInput.addEventListener("input", () => {
    localStorage.setItem(couponStorageKey, cartCouponInput.value.trim());
  });

  const applyButton = document.querySelector("[data-cart-apply-coupon]");
  if (!applyButton) return;

  applyButton.addEventListener("click", () => {
    const code = cartCouponInput.value.trim();
    if (!code) {
      localStorage.removeItem(couponStorageKey);
      if (feedback) {
        feedback.textContent = "Ingresa un cupón para guardarlo antes de checkout.";
      }
      setCartStatus("No se guardó ningún cupón.");
      toast("info", "No se guardó cupón. Ingresa un código para aplicarlo.");
      return;
    }

    localStorage.setItem(couponStorageKey, code);
    if (feedback) {
      feedback.textContent = "Cupón guardado. Se validará al confirmar checkout.";
    }
    setCartStatus(`Cupón ${code} guardado para checkout.`);
    toast("success", `Cupón ${code} guardado para checkout.`);
  });
}

function setupMobileNavigation() {
  const toggleButton = document.querySelector("[data-nav-toggle]");
  if (!toggleButton) return;

  const controlsId = toggleButton.getAttribute("aria-controls");
  const nav = controlsId ? document.getElementById(controlsId) : null;
  if (!nav) return;

  toggleButton.addEventListener("click", () => {
    const isOpen = nav.classList.toggle("is-open");
    toggleButton.setAttribute("aria-expanded", isOpen ? "true" : "false");
  });

  document.addEventListener("click", (event) => {
    if (!nav.classList.contains("is-open")) return;
    if (nav.contains(event.target) || toggleButton.contains(event.target)) return;
    nav.classList.remove("is-open");
    toggleButton.setAttribute("aria-expanded", "false");
  });

  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape" || !nav.classList.contains("is-open")) return;
    nav.classList.remove("is-open");
    toggleButton.setAttribute("aria-expanded", "false");
    toggleButton.focus();
  });

  nav.addEventListener("click", (event) => {
    const link = event.target.closest("a");
    if (!link) return;
    nav.classList.remove("is-open");
    toggleButton.setAttribute("aria-expanded", "false");
  });
}

function setupProductGallery() {
  const main = document.getElementById("product-main-image");
  if (!main) return;

  document.querySelectorAll("[data-product-thumb]").forEach((thumb) => {
    thumb.addEventListener("click", () => {
      const url = thumb.getAttribute("data-image-url");
      const alt = thumb.getAttribute("data-image-alt") || "Producto";
      if (!url) return;

      if (main.tagName === "IMG") {
        main.setAttribute("src", url);
        main.setAttribute("alt", alt);
      }

      document.querySelectorAll("[data-product-thumb]").forEach((node) => {
        node.classList.remove("is-active");
      });
      thumb.classList.add("is-active");
    });
  });
}

function setupCheckoutForm() {
  const checkoutForm = document.getElementById("checkout-form");
  if (!checkoutForm) return;

  const checkoutCouponInput = document.getElementById("checkout-coupon");
  if (checkoutCouponInput && !checkoutCouponInput.value) {
    checkoutCouponInput.value = localStorage.getItem(couponStorageKey) || "";
  }

  const submitButton = checkoutForm.querySelector('button[type="submit"]');
  const resultHolder = document.getElementById("checkout-result");

  if (submitButton) {
    const spinner = submitButton.querySelector("[data-button-spinner]");
    if (spinner) spinner.hidden = true;
  }

  checkoutForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearFieldErrors(checkoutForm);
    showCheckoutAlert("info", "");

    if (resultHolder) {
      resultHolder.textContent = "";
      resultHolder.classList.remove("error", "success");
    }

    const formPayload = Object.fromEntries(new FormData(checkoutForm).entries());
    if (formPayload.coupon_code) {
      localStorage.setItem(couponStorageKey, String(formPayload.coupon_code).trim());
    }

    setButtonLoading(submitButton, true, "Procesando...");

    try {
      const { response, payload } = await apiRequest("/checkout/api/checkout/confirm/", {
        method: "POST",
        body: JSON.stringify(formPayload),
      });

      if (!response.ok) {
        const hasFieldErrors = renderFieldErrors(checkoutForm, payload);
        const message = getErrorMessage(payload, "No se pudo confirmar el pedido. Revisa tus datos.");

        if (!hasFieldErrors) {
          showCheckoutAlert(payload?.code === "invalid_coupon" ? "warn" : "danger", message);
        }

        if (payload?.code === "invalid_coupon") {
          toast("warn", message);
        } else {
          toast("danger", message);
        }
        return;
      }

      const safeConfirmationUrl = getSafeConfirmationUrl(payload.confirmation_url);
      renderCheckoutResult(resultHolder, payload.confirmation_url, payload.whatsapp_url);
      showCheckoutAlert("success", "Pedido creado correctamente. Te estamos redirigiendo a la confirmación...");
      toast("success", "Pedido creado correctamente.");
      localStorage.removeItem(couponStorageKey);
      await refreshCartBadge();

      if (safeConfirmationUrl) {
        window.setTimeout(() => {
          window.location.assign(safeConfirmationUrl);
        }, 500);
      }
    } catch (_) {
      const message = "Error de red al confirmar pedido. Intenta nuevamente.";
      showCheckoutAlert("danger", message);
      toast("danger", message);
    } finally {
      setButtonLoading(submitButton, false);
    }
  });
}

function setupRevealAnimations() {
  const nodes = Array.from(document.querySelectorAll(".fx-reveal"));
  if (nodes.length < 1) return;

  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches || !("IntersectionObserver" in window)) {
    nodes.forEach((node) => node.classList.add("is-visible"));
    return;
  }

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add("is-visible");
      observer.unobserve(entry.target);
    });
  }, { threshold: 0.14 });

  nodes.forEach((node) => observer.observe(node));
}

document.addEventListener("click", async (event) => {
  const addCartButton = event.target.closest("[data-add-cart]");
  if (addCartButton) {
    const variantId = Number(addCartButton.dataset.addCart);
    if (variantId) {
      await addToCart(variantId, addCartButton);
      setCartStatus("Producto agregado al carrito.");
    }
    return;
  }

  const increaseButton = event.target.closest("[data-cart-increase]");
  if (increaseButton) {
    const itemId = Number(increaseButton.dataset.cartIncrease);
    const qtyNode = document.querySelector(`[data-cart-qty="${itemId}"]`);
    const currentQty = Number(qtyNode?.textContent || 1);
    const payload = await updateCartItem(itemId, currentQty + 1, increaseButton);
    if (payload) {
      renderCartPage(payload);
      setCartStatus("Cantidad actualizada en el carrito.");
      toast("success", "Cantidad actualizada.");
    }
    return;
  }

  const decreaseButton = event.target.closest("[data-cart-decrease]");
  if (decreaseButton) {
    const itemId = Number(decreaseButton.dataset.cartDecrease);
    const qtyNode = document.querySelector(`[data-cart-qty="${itemId}"]`);
    const currentQty = Number(qtyNode?.textContent || 1);

    if (currentQty <= 1) {
      const payload = await removeCartItem(itemId, decreaseButton);
      if (payload) {
        renderCartPage(payload);
        setCartStatus("Producto eliminado del carrito.");
        toast("info", "Producto eliminado del carrito.");
      }
      return;
    }

    const payload = await updateCartItem(itemId, currentQty - 1, decreaseButton);
    if (payload) {
      renderCartPage(payload);
      setCartStatus("Cantidad actualizada en el carrito.");
      toast("success", "Cantidad actualizada.");
    }
    return;
  }

  const removeButton = event.target.closest("[data-cart-remove]");
  if (removeButton) {
    const itemId = Number(removeButton.dataset.cartRemove);
    const payload = await removeCartItem(itemId, removeButton);
    if (payload) {
      renderCartPage(payload);
      setCartStatus("Producto eliminado del carrito.");
      toast("info", "Producto eliminado del carrito.");
    }
    return;
  }

  const clearButton = event.target.closest("[data-cart-clear]");
  if (clearButton) {
    const payload = await clearCart(clearButton);
    if (payload) {
      renderCartPage(payload);
      setCartStatus("Carrito vaciado.");
      toast("info", "Carrito vaciado.");
    }
  }
});

setupMobileNavigation();
setupProductGallery();
setupCartCouponInput();
setupCheckoutForm();
setupRevealAnimations();
refreshCartBadge({ render: Boolean(document.querySelector("[data-cart-page]")) });
