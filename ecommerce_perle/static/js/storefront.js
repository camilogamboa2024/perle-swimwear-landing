const currency = localStorage.getItem('perleCurrency') || 'COP';
const wishlist = JSON.parse(localStorage.getItem('perleWishlist') || '[]');

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return null;
}

function formatCOP(value) {
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(value || 0);
}

function showToast(message) {
  const node = document.getElementById('app-toast');
  if (!node) return;
  node.textContent = message;
  node.classList.add('show');
  setTimeout(() => node.classList.remove('show'), 1800);
}

async function refreshCartBadge() {
  try {
    const resp = await fetch('/api/cart/', { credentials: 'same-origin' });
    if (!resp.ok) return;
    const payload = await resp.json();
    const items = Array.isArray(payload.items) ? payload.items : [];
    const count = items.reduce((acc, item) => acc + (Number(item.quantity) || 0), 0) || items.length || 0;
    const total = payload.totals?.grand_total ?? payload.totals?.total ?? payload.totals?.amount ?? null;
    const countNode = document.getElementById('cart-count');
    const totalNode = document.getElementById('cart-total');
    if (countNode) countNode.textContent = String(count);
    if (totalNode && typeof total === 'number') totalNode.textContent = formatCOP(total);
    else if (totalNode) totalNode.textContent = '';
  } catch (_) {
    // silent fallback
  }
}

async function addToCart(variantId) {
  try {
    const resp = await fetch('/api/cart/items/', {
      method: 'POST',
      credentials: 'same-origin',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken') || '',
      },
      body: JSON.stringify({ variant_id: variantId, quantity: 1 }),
    });

    if (!resp.ok) {
      showToast('No se pudo agregar a la bolsa');
      return;
    }
    await refreshCartBadge();
    showToast('Agregado a la bolsa');
  } catch (_) {
    showToast('Error de red al agregar producto');
  }
}

function toggleWishlist(productId) {
  const idx = wishlist.indexOf(productId);
  if (idx >= 0) wishlist.splice(idx, 1);
  else wishlist.push(productId);
  localStorage.setItem('perleWishlist', JSON.stringify(wishlist));
}

function renderCheckoutError(holder, message) {
  if (!holder) return;
  holder.textContent = '';
  const errorNode = document.createElement('p');
  errorNode.style.color = '#b42318';
  errorNode.textContent = message;
  holder.appendChild(errorNode);
}

function getSafeConfirmationUrl(rawUrl) {
  if (!rawUrl) return '';
  try {
    const parsed = new URL(rawUrl, window.location.origin);
    const isHttp = parsed.protocol === 'http:' || parsed.protocol === 'https:';
    if (!isHttp || parsed.origin !== window.location.origin) return '';
    return `${parsed.pathname}${parsed.search}${parsed.hash}`;
  } catch (_) {
    return '';
  }
}

function getSafeWhatsappUrl(rawUrl) {
  if (!rawUrl) return '';
  try {
    const parsed = new URL(rawUrl);
    const isHttp = parsed.protocol === 'http:' || parsed.protocol === 'https:';
    const allowedHost = parsed.hostname === 'wa.me' || parsed.hostname === 'api.whatsapp.com';
    return isHttp && allowedHost ? parsed.toString() : '';
  } catch (_) {
    return '';
  }
}

function renderCheckoutSuccess(holder, confirmationUrl, whatsappUrl) {
  if (!holder) return;
  holder.textContent = '';

  const safeConfirmationUrl = getSafeConfirmationUrl(confirmationUrl);
  const safeWhatsappUrl = getSafeWhatsappUrl(whatsappUrl);

  if (safeConfirmationUrl) {
    const confirmationLink = document.createElement('a');
    confirmationLink.href = safeConfirmationUrl;
    confirmationLink.textContent = 'Ver confirmación';
    holder.appendChild(confirmationLink);
  }

  if (safeWhatsappUrl) {
    if (holder.childNodes.length > 0) holder.appendChild(document.createTextNode(' · '));
    const whatsappLink = document.createElement('a');
    whatsappLink.href = safeWhatsappUrl;
    whatsappLink.textContent = 'WhatsApp';
    whatsappLink.rel = 'noreferrer';
    holder.appendChild(whatsappLink);
  }

  if (holder.childNodes.length === 0) {
    const successNode = document.createElement('p');
    successNode.textContent = 'Pedido creado correctamente.';
    holder.appendChild(successNode);
  }
}

document.addEventListener('click', (e) => {
  const cartBtn = e.target.closest('[data-add-cart]');
  if (cartBtn) addToCart(Number(cartBtn.dataset.addCart));
  const wishBtn = e.target.closest('[data-wishlist]');
  if (wishBtn) toggleWishlist(Number(wishBtn.dataset.wishlist));
});

const checkoutForm = document.getElementById('checkout-form');
if (checkoutForm) {
  checkoutForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const holder = document.getElementById('checkout-result');
    const submitButton = checkoutForm.querySelector('button[type="submit"]');
    const previousLabel = submitButton ? submitButton.textContent : '';
    const data = Object.fromEntries(new FormData(checkoutForm).entries());

    if (submitButton) {
      submitButton.disabled = true;
      submitButton.textContent = 'Procesando...';
    }

    try {
      const resp = await fetch('/checkout/api/checkout/confirm/', {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken') || '',
        },
        body: JSON.stringify(data),
      });

      const payload = await resp.json().catch(() => ({}));
      if (!resp.ok) {
        const errorMsg = payload.detail || payload.error || 'No se pudo confirmar el pedido. Verifica tus datos.';
        renderCheckoutError(holder, errorMsg);
        showToast('Revisa los datos del checkout');
        return;
      }

      renderCheckoutSuccess(holder, payload.confirmation_url, payload.whatsapp_url);
      showToast('Pedido creado correctamente');
      await refreshCartBadge();
    } catch (_) {
      renderCheckoutError(holder, 'Error de red al confirmar el pedido. Intenta de nuevo.');
      showToast('Error de red');
    } finally {
      if (submitButton) {
        submitButton.disabled = false;
        submitButton.textContent = previousLabel || 'Confirmar pedido';
      }
    }
  });
}

localStorage.setItem('perleCurrency', currency);
refreshCartBadge();
