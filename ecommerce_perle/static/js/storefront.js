const currency = localStorage.getItem("perleCurrency") || "COP";
const couponStorageKey = "perleCouponCode";

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) {
    return parts.pop().split(";").shift();
  }
  return null;
}

function formatCOP(value) {
  return new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency: "COP",
    minimumFractionDigits: 0,
  }).format(value || 0);
}

function showToast(message) {
  const node = document.getElementById("app-toast");
  if (!node) return;
  node.textContent = message;
  node.classList.add("show");
  setTimeout(() => node.classList.remove("show"), 1900);
}

async function apiRequest(url, options = {}) {
  const defaultHeaders = {
    "Content-Type": "application/json",
    "X-CSRFToken": getCookie("csrftoken") || "",
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
  const total = payload.totals?.grand_total ?? 0;

  const countNode = document.getElementById("cart-count");
  const totalNode = document.getElementById("cart-total");
  if (countNode) countNode.textContent = String(count);
  if (totalNode) totalNode.textContent = count > 0 ? formatCOP(total) : "";

  const subtotalNode = document.getElementById("cart-subtotal");
  const discountNode = document.getElementById("cart-discount");
  const grandTotalNode = document.getElementById("cart-total-main");
  if (subtotalNode) subtotalNode.textContent = formatCOP(payload.totals?.subtotal || 0);
  if (discountNode) discountNode.textContent = formatCOP(payload.totals?.discount_total || 0);
  if (grandTotalNode) grandTotalNode.textContent = formatCOP(total);
}

function cartRowTemplate(item) {
  return `
    <tr data-item-id="${item.id}">
      <td>
        <strong>${item.product_name}</strong>
        <p class="muted">${item.size} / ${item.color}</p>
      </td>
      <td>
        <div class="qty-stepper">
          <button type="button" class="btn btn-ghost" data-cart-decrease="${item.id}" aria-label="Reducir cantidad">-</button>
          <span data-cart-qty="${item.id}">${item.quantity}</span>
          <button type="button" class="btn btn-ghost" data-cart-increase="${item.id}" aria-label="Aumentar cantidad">+</button>
        </div>
      </td>
      <td>${formatCOP(item.unit_price)}</td>
      <td><button type="button" class="btn btn-ghost danger" data-cart-remove="${item.id}">Eliminar</button></td>
    </tr>
  `;
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

  tbody.innerHTML = items.map(cartRowTemplate).join("");
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

async function addToCart(variantId) {
  try {
    const { response, payload } = await apiRequest("/api/cart/items/", {
      method: "POST",
      body: JSON.stringify({ variant_id: variantId, quantity: 1 }),
    });
    if (!response.ok) {
      showToast(payload.error || "No se pudo agregar a la bolsa.");
      return;
    }
    updateSummaryNodes(payload);
    renderCartPage(payload);
    showToast("Producto agregado a la bolsa");
  } catch (_) {
    showToast("Error de red al agregar producto");
  }
}

async function updateCartItem(itemId, quantity) {
  const { response, payload } = await apiRequest(`/api/cart/items/${itemId}/`, {
    method: "PATCH",
    body: JSON.stringify({ quantity }),
  });
  if (!response.ok) {
    showToast(payload.error || "No se pudo actualizar la cantidad.");
    return null;
  }
  return payload;
}

async function removeCartItem(itemId) {
  const { response, payload } = await apiRequest(`/api/cart/items/${itemId}/`, {
    method: "DELETE",
    body: JSON.stringify({}),
  });
  if (!response.ok) {
    showToast(payload.error || "No se pudo eliminar el item.");
    return null;
  }
  return payload;
}

async function clearCart() {
  const { response, payload } = await apiRequest("/api/cart/clear/", {
    method: "POST",
    body: JSON.stringify({}),
  });
  if (!response.ok) {
    showToast(payload.error || "No se pudo vaciar el carrito.");
    return null;
  }
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

function renderCheckoutError(holder, message) {
  if (!holder) return;
  holder.classList.remove("success");
  holder.classList.add("error");
  holder.textContent = message;
}

function renderCheckoutSuccess(holder, confirmationUrl, whatsappUrl) {
  if (!holder) return;
  holder.classList.remove("error");
  holder.classList.add("success");
  holder.textContent = "";

  const safeConfirmationUrl = getSafeConfirmationUrl(confirmationUrl);
  const safeWhatsappUrl = getSafeWhatsappUrl(whatsappUrl);

  if (safeConfirmationUrl) {
    const confirmationLink = document.createElement("a");
    confirmationLink.href = safeConfirmationUrl;
    confirmationLink.textContent = "Ver confirmación";
    holder.appendChild(confirmationLink);
  }

  if (safeWhatsappUrl) {
    if (holder.childNodes.length > 0) holder.appendChild(document.createTextNode(" · "));
    const waLink = document.createElement("a");
    waLink.href = safeWhatsappUrl;
    waLink.rel = "noreferrer";
    waLink.target = "_blank";
    waLink.textContent = "Finalizar por WhatsApp";
    holder.appendChild(waLink);
  }

  if (holder.childNodes.length === 0) {
    holder.textContent = "Pedido confirmado correctamente.";
  }
}

document.addEventListener("click", async (event) => {
  const addCartBtn = event.target.closest("[data-add-cart]");
  if (addCartBtn) {
    await addToCart(Number(addCartBtn.dataset.addCart));
    return;
  }

  const increaseBtn = event.target.closest("[data-cart-increase]");
  if (increaseBtn) {
    const itemId = Number(increaseBtn.dataset.cartIncrease);
    const qtyNode = document.querySelector(`[data-cart-qty="${itemId}"]`);
    const currentQty = Number(qtyNode?.textContent || 1);
    const payload = await updateCartItem(itemId, currentQty + 1);
    if (payload) {
      renderCartPage(payload);
      showToast("Cantidad actualizada");
    }
    return;
  }

  const decreaseBtn = event.target.closest("[data-cart-decrease]");
  if (decreaseBtn) {
    const itemId = Number(decreaseBtn.dataset.cartDecrease);
    const qtyNode = document.querySelector(`[data-cart-qty="${itemId}"]`);
    const currentQty = Number(qtyNode?.textContent || 1);
    if (currentQty <= 1) {
      const payload = await removeCartItem(itemId);
      if (payload) {
        renderCartPage(payload);
        showToast("Item eliminado");
      }
      return;
    }
    const payload = await updateCartItem(itemId, currentQty - 1);
    if (payload) {
      renderCartPage(payload);
      showToast("Cantidad actualizada");
    }
    return;
  }

  const removeBtn = event.target.closest("[data-cart-remove]");
  if (removeBtn) {
    const itemId = Number(removeBtn.dataset.cartRemove);
    const payload = await removeCartItem(itemId);
    if (payload) {
      renderCartPage(payload);
      showToast("Item eliminado");
    }
    return;
  }

  const clearBtn = event.target.closest("[data-cart-clear]");
  if (clearBtn) {
    const payload = await clearCart();
    if (payload) {
      renderCartPage(payload);
      showToast("Carrito vaciado");
    }
  }
});

const cartCouponInput = document.getElementById("cart-coupon");
if (cartCouponInput) {
  cartCouponInput.value = localStorage.getItem(couponStorageKey) || "";
  cartCouponInput.addEventListener("input", () => {
    localStorage.setItem(couponStorageKey, cartCouponInput.value.trim());
  });
}

const checkoutForm = document.getElementById("checkout-form");
if (checkoutForm) {
  const checkoutCouponInput = document.getElementById("checkout-coupon");
  if (checkoutCouponInput && !checkoutCouponInput.value) {
    checkoutCouponInput.value = localStorage.getItem(couponStorageKey) || "";
  }

  checkoutForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const resultHolder = document.getElementById("checkout-result");
    const submitButton = checkoutForm.querySelector('button[type="submit"]');
    const formPayload = Object.fromEntries(new FormData(checkoutForm).entries());
    const previousLabel = submitButton?.textContent || "Confirmar pedido";

    if (formPayload.coupon_code) {
      localStorage.setItem(couponStorageKey, String(formPayload.coupon_code).trim());
    }

    if (submitButton) {
      submitButton.disabled = true;
      submitButton.textContent = "Procesando...";
    }

    try {
      const { response, payload } = await apiRequest("/checkout/api/checkout/confirm/", {
        method: "POST",
        body: JSON.stringify(formPayload),
      });

      if (!response.ok) {
        const errorMessage =
          payload.error || payload.detail || "No se pudo confirmar el pedido. Revisa tus datos.";
        renderCheckoutError(resultHolder, errorMessage);
        showToast(errorMessage);
        return;
      }

      renderCheckoutSuccess(resultHolder, payload.confirmation_url, payload.whatsapp_url);
      showToast("Pedido creado correctamente");
      await refreshCartBadge();
    } catch (_) {
      renderCheckoutError(resultHolder, "Error de red al confirmar pedido. Intenta nuevamente.");
      showToast("Error de red");
    } finally {
      if (submitButton) {
        submitButton.disabled = false;
        submitButton.textContent = previousLabel;
      }
    }
  });
}

localStorage.setItem("perleCurrency", currency);
refreshCartBadge({ render: Boolean(document.querySelector("[data-cart-page]")) });
