/* =====================================
   1. DATA
   ===================================== */
const EXCHANGE_RATE = 0.00026; // COP -> USD aprox
const FREE_SHIPPING_THRESHOLD = 250000;

const products = [
  {
    id: 1,
    name: "Bikini Cielo Reversible",
    category: "bikini",
    priceCOP: 129000,
    img:
      "https://images.unsplash.com/photo-1574941076936-2337777174db?w=800&q=80&auto=format&fit=crop",
    rating: 4.9,
    reviews: 72,
    badges: ["best", "reversible"],
    eco: true,
    familyMatch: false,
    coverage: "media",
    support: "alto",
    description:
      "Top con varilla interna y tirantes ajustables. Reversible con estampado floral y lado liso.",
    tags: ["Soporte alto", "Reversible", "Ideal busto medio-grande"],
    sizes: ["S", "M", "L"],
  },
  {
    id: 2,
    name: "Enterizo Mar Profundo",
    category: "enterizo",
    priceCOP: 145000,
    img:
      "https://images.unsplash.com/photo-1576403061730-6b669528f117?w=800&q=80&auto=format&fit=crop",
    rating: 4.8,
    reviews: 51,
    badges: ["limited"],
    eco: true,
    familyMatch: true,
    coverage: "alta",
    support: "alto",
    description:
      "Enterizo con escote en V y amarre en espalda. Compresión suave para realzar la silueta.",
    tags: ["Cobertura alta", "Súper cómodo", "Family Match"],
    sizes: ["S", "M", "L", "XL"],
  },
  {
    id: 3,
    name: "Kimono Arena Dorada",
    category: "salida",
    priceCOP: 89000,
    img:
      "https://images.unsplash.com/photo-1563178406-4cdc2923acbc?w=800&q=80&auto=format&fit=crop",
    rating: 4.7,
    reviews: 35,
    badges: [],
    eco: false,
    familyMatch: false,
    coverage: "n/a",
    support: "n/a",
    description:
      "Kimono de lino suave, ideal para playa, brunch o piscina. Combina con toda la colección.",
    tags: ["Ligero", "Secado rápido"],
    sizes: ["Única"],
  },
  {
    id: 4,
    name: "Set Océano Match",
    category: "bikini",
    priceCOP: 138000,
    img:
      "https://images.unsplash.com/photo-1545959734-77d0463c2c5c?w=800&q=80&auto=format&fit=crop",
    rating: 4.9,
    reviews: 64,
    badges: ["family"],
    eco: true,
    familyMatch: true,
    coverage: "media",
    support: "medio",
    description:
      "Set de bikini con estampado marino y opción de mini para niña. Ideal fotos familiares.",
    tags: ["Family Match", "Estampado exclusivo"],
    sizes: ["XS", "S", "M", "L"],
  },
  {
    id: 5,
    name: "Bikini Atardecer Texturizado",
    category: "bikini",
    priceCOP: 135000,
    img:
      "https://images.unsplash.com/photo-1582639510494-c80e5e63a9fb?w=800&q=80&auto=format&fit=crop",
    rating: 4.8,
    reviews: 40,
    badges: ["best"],
    eco: false,
    familyMatch: false,
    coverage: "baja",
    support: "medio",
    description:
      "Bikini triangular con textura acanalada y tonos atardecer. Ideal para bronceo.",
    tags: ["Cobertura baja", "Textura acanalada"],
    sizes: ["S", "M"],
  },
  {
    id: 6,
    name: "Sarong Tropical Multiuso",
    category: "salida",
    priceCOP: 69000,
    img:
      "https://images.unsplash.com/photo-1583949774641-606016147414?w=800&q=80&auto=format&fit=crop",
    rating: 4.6,
    reviews: 22,
    badges: [],
    eco: true,
    familyMatch: false,
    coverage: "n/a",
    support: "n/a",
    description:
      "Sarong ligero que puedes usar como falda, vestido o pareo. Secado rápido.",
    tags: ["Multiuso", "Eco friendly"],
    sizes: ["Única"],
  },
];

/* QUIZ */
const quizSteps = [
  {
    id: "coverage",
    question: "¿Cómo te gusta la cobertura del top?",
    options: ["Baja (para broncear)", "Media", "Alta (prefiero sentirme cubierta)"],
  },
  {
    id: "support",
    question: "Tu prioridad principal es:",
    options: ["Soporte máximo", "Versatilidad (reversible / mix & match)", "Estilo para fotos"],
  },
  {
    id: "activity",
    question: "¿Cómo usarás más tu traje de baño?",
    options: ["Playa tranquila / piscina", "Planes activos (jugar, nadar)", "Viajes y fotos en redes"],
  },
];

/* =====================================
   2. STATE
   ===================================== */
let currency = localStorage.getItem("perleCurrency") || "COP";
let cart = JSON.parse(localStorage.getItem("perleCart")) || [];
let wishlist = JSON.parse(localStorage.getItem("perleWishlist")) || [];
let quizState = {
  stepIndex: 0,
  answers: {},
  completed: false,
};

/* =====================================
   3. HELPERS
   ===================================== */
const formatPrice = (priceCOP) => {
  if (currency === "USD") {
    const usd = priceCOP * EXCHANGE_RATE;
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 0,
    }).format(usd);
  }
  return new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency: "COP",
    minimumFractionDigits: 0,
  }).format(priceCOP);
};

const showToast = (text) => {
  const toast = document.getElementById("toast");
  const toastText = document.getElementById("toast-text");
  toastText.textContent = text;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 2600);
};

const setOverlay = (visible) => {
  const overlay = document.getElementById("overlay");
  overlay.classList.toggle("show", visible);
};

const syncStorage = () => {
  localStorage.setItem("perleCart", JSON.stringify(cart));
  localStorage.setItem("perleWishlist", JSON.stringify(wishlist));
  localStorage.setItem("perleCurrency", currency);
};

/* =====================================
   4. RENDER PRODUCTS
   ===================================== */
const productsGrid = document.getElementById("products-grid");

const renderProducts = (list = products) => {
  productsGrid.innerHTML = "";
  list.forEach((p) => {
    const article = document.createElement("article");
    article.className = "product-card";
    const inWishlist = wishlist.includes(p.id);
    const badges = [];
    if (p.badges.includes("best")) badges.push('<span class="badge">Best Seller</span>');
    if (p.badges.includes("reversible")) badges.push('<span class="badge">2 en 1</span>');
    if (p.badges.includes("family")) badges.push('<span class="badge">Family Match</span>');
    if (p.eco) badges.push('<span class="badge badge--eco">Eco</span>');
    if (p.badges.includes("limited")) badges.push('<span class="badge badge--limited">Limitado</span>');

    article.innerHTML = `
      <div class="product-card__media">
        <img src="${p.img}" alt="${p.name}" loading="lazy" />
        <div class="product-card__badges">${badges.join("")}</div>
        <button class="product-card__wishlist ${inWishlist ? "active" : ""}" data-id="${
      p.id
    }" aria-label="Favorito">
          <i class="ri-heart-3-fill"></i>
        </button>
      </div>
      <div class="product-card__info">
        <h3 class="product-card__title">${p.name}</h3>
        <div class="product-card__meta">
          <span>${p.category === "bikini" ? "Bikini" : p.category === "enterizo" ? "Enterizo" : "Salida"}</span>
          <span class="product-card__rating">
            <i class="ri-star-fill"></i>
            <span>${p.rating.toFixed(1)} (${p.reviews})</span>
          </span>
        </div>
        <div class="product-card__price">${formatPrice(p.priceCOP)}</div>
        <div class="product-card__tags">
          ${p.tags.map((t) => `<span>${t}</span>`).join("")}
        </div>
        <div class="product-card__actions">
          <button class="btn btn--sm" data-add-cart="${p.id}">
            Añadir a la bolsa
          </button>
          <button class="btn--ghost btn--sm" data-quickview="${p.id}">
            Ver fit
          </button>
        </div>
      </div>
    `;
    productsGrid.appendChild(article);
  });
};

/* =====================================
   5. CART
   ===================================== */
const cartCountElement = document.getElementById("cart-count");
const cartItemsContainer = document.getElementById("cart-items");
const cartTotalElement = document.getElementById("cart-total");
const cartProgressText = document.getElementById("cart-progress-text");
const cartProgressFill = document.getElementById("cart-progress-fill");

const renderCart = () => {
  cartItemsContainer.innerHTML = "";
  if (!cart.length) {
    cartItemsContainer.innerHTML =
      '<p class="cart__empty">Tu bolsa está vacía 🛍️<br>Empieza agregando tu bikini favorito.</p>';
  } else {
    cart.forEach((item) => {
      const div = document.createElement("div");
      div.className = "cart__item";
      div.innerHTML = `
        <div class="cart__thumb">
          <img src="${item.img}" alt="${item.name}" />
        </div>
        <div class="cart__info">
          <div class="cart__name">${item.name}</div>
          <div class="cart__meta">
            ${item.category === "bikini" ? "Bikini" : item.category === "enterizo" ? "Enterizo" : "Salida"} · ${
        item.size || "Talla única"
      }
          </div>
          <div class="cart__amount">
            <button class="cart__qty-btn" data-qty-dec="${item.id}">-</button>
            <span>${item.qty}</span>
            <button class="cart__qty-btn" data-qty-inc="${item.id}">+</button>
          </div>
        </div>
        <button class="cart__remove" data-remove="${item.id}" aria-label="Eliminar">
          <i class="ri-delete-bin-line"></i>
        </button>
      `;
      cartItemsContainer.appendChild(div);
    });
  }

  // total & count
  let totalCOP = 0;
  let count = 0;
  cart.forEach((i) => {
    totalCOP += i.priceCOP * i.qty;
    count += i.qty;
  });
  cartCountElement.textContent = count;
  cartTotalElement.textContent = formatPrice(totalCOP);

  // progreso envío gratis
  const progress = Math.min(1, totalCOP / FREE_SHIPPING_THRESHOLD);
  cartProgressFill.style.width = progress * 100 + "%";
  if (totalCOP === 0) {
    cartProgressText.textContent = `Te faltan ${formatPrice(FREE_SHIPPING_THRESHOLD)} para envío gratis`;
  } else if (totalCOP < FREE_SHIPPING_THRESHOLD) {
    const diff = FREE_SHIPPING_THRESHOLD - totalCOP;
    cartProgressText.textContent = `Te faltan ${formatPrice(diff)} para envío gratis`;
  } else {
    cartProgressText.textContent = "¡Ya tienes envío gratis en tu compra! 🎉";
  }

  syncStorage();
};

const addToCart = (id) => {
  const product = products.find((p) => p.id === id);
  if (!product) return;

  const existing = cart.find((i) => i.id === id);
  if (existing) {
    existing.qty += 1;
  } else {
    cart.push({
      ...product,
      qty: 1,
      size: product.sizes[0] || "Única",
    });
  }
  renderCart();
  showToast(`✨ ${product.name} añadido a tu bolsa`);
  openCart();
};

const openCart = () => {
  document.getElementById("cart").classList.add("show-cart");
  setOverlay(true);
};
const closeCart = () => {
  document.getElementById("cart").classList.remove("show-cart");
  setOverlay(false);
};

/* =====================================
   6. WISHLIST & QUICKVIEW
   ===================================== */
const toggleWishlist = (id) => {
  if (wishlist.includes(id)) {
    wishlist = wishlist.filter((w) => w !== id);
    showToast("💔 Eliminado de tus favoritos");
  } else {
    wishlist.push(id);
    showToast("❤️ Añadido a tus favoritos");
  }
  syncStorage();
  renderProducts(getFilteredProducts());
};

const quickviewModal = document.getElementById("quickview-modal");
const quickviewBody = document.getElementById("quickview-body");
const quickviewTitle = document.getElementById("quickview-title");

const openQuickview = (id) => {
  const product = products.find((p) => p.id === id);
  if (!product) return;
  quickviewTitle.textContent = product.name;
  quickviewBody.innerHTML = `
    <div class="quickview__grid">
      <div class="quickview__media">
        <img src="${product.img}" alt="${product.name}" />
      </div>
      <div>
        <p class="quickview__meta">
          ${
            product.category === "bikini"
              ? "Bikini"
              : product.category === "enterizo"
              ? "Enterizo"
              : "Salida"
          } · ${product.rating.toFixed(1)} ★ (${product.reviews} reseñas)
        </p>
        <div class="quickview__tags">
          ${product.eco ? "<span>Eco-friendly</span>" : ""}
          ${product.badges.includes("reversible") ? "<span>Reversible</span>" : ""}
          ${product.familyMatch ? "<span>Family Match</span>" : ""}
        </div>
        <p class="quickview__fit">
          <strong>Fit:</strong> Cobertura ${
            product.coverage === "n/a" ? "—" : product.coverage
          }, soporte ${product.support === "n/a" ? "—" : product.support}.
        </p>
        <p style="font-size: .86rem; margin-bottom: .8rem;">
          ${product.description}
        </p>
        <div class="quickview__price">${formatPrice(product.priceCOP)}</div>
        <div class="quickview__sizes">
          ${product.sizes
            .map((s) => `<button class="quickview__size" data-size="${s}">${s}</button>`)
            .join("")}
        </div>
        <div style="display:flex; gap:.5rem; flex-wrap:wrap;">
          <button class="btn btn--sm" data-add-cart="${product.id}">Añadir a la bolsa</button>
          <button class="btn--ghost btn--sm" id="quickview-whatsapp">
            Preguntar por este modelo
            <i class="ri-whatsapp-line"></i>
          </button>
        </div>
      </div>
    </div>
  `;
  quickviewModal.classList.add("show");
  setOverlay(true);

  // link de whatsapp en quickview
  const waBtn = document.getElementById("quickview-whatsapp");
  if (waBtn) {
    waBtn.onclick = () => {
      const url = `https://wa.me/573001234567?text=Hola%20Perle!%20Quiero%20saber%20m%C3%A1s%20sobre%20*${encodeURIComponent(
        product.name
      )}* 👙`;
      window.open(url, "_blank");
    };
  }
};

const closeQuickview = () => {
  quickviewModal.classList.remove("show");
  setOverlay(false);
};

/* =====================================
   7. FILTROS
   ===================================== */
let currentCategoryFilter = "all";
let currentSpecialFilter = null;

const getFilteredProducts = () => {
  return products.filter((p) => {
    let categoryMatch =
      currentCategoryFilter === "all" || p.category === currentCategoryFilter;
    let specialMatch = true;
    if (currentSpecialFilter === "reversible") {
      specialMatch = p.badges.includes("reversible");
    } else if (currentSpecialFilter === "eco") {
      specialMatch = p.eco;
    } else if (currentSpecialFilter === "family") {
      specialMatch = p.familyMatch;
    }
    return categoryMatch && specialMatch;
  });
};

const initFilters = () => {
  document
    .getElementById("filter-category")
    .addEventListener("click", (e) => {
      if (!e.target.classList.contains("chip")) return;
      const value = e.target.dataset.value;
      currentCategoryFilter = value;
      [...e.currentTarget.children].forEach((chip) =>
        chip.classList.remove("chip--active")
      );
      e.target.classList.add("chip--active");
      renderProducts(getFilteredProducts());
    });

  document
    .getElementById("filter-special")
    .addEventListener("click", (e) => {
      if (!e.target.classList.contains("chip")) return;
      const value = e.target.dataset.value;
      if (currentSpecialFilter === value) {
        currentSpecialFilter = null;
        e.target.classList.remove("chip--active");
      } else {
        currentSpecialFilter = value;
        [...e.currentTarget.children].forEach((chip) =>
          chip.classList.remove("chip--active")
        );
        e.target.classList.add("chip--active");
      }
      renderProducts(getFilteredProducts());
    });
};

/* =====================================
   8. QUIZ
   ===================================== */
const quizStepsContainer = document.getElementById("quiz-steps");
const quizQuestionEl = document.getElementById("quiz-question");
const quizOptionsEl = document.getElementById("quiz-options");
const quizPrevBtn = document.getElementById("quiz-prev");
const quizNextBtn = document.getElementById("quiz-next");
const quizSummaryEl = document.getElementById("quiz-summary");

const renderQuizSteps = () => {
  quizStepsContainer.innerHTML = "";
  quizSteps.forEach((step, index) => {
    const span = document.createElement("span");
    span.className =
      "quiz__step-pill" +
      (index === quizState.stepIndex ? " active" : "");
    span.textContent = `Paso ${index + 1}`;
    quizStepsContainer.appendChild(span);
  });
};

const renderQuizStep = () => {
  const step = quizSteps[quizState.stepIndex];
  quizQuestionEl.textContent = step.question;
  quizOptionsEl.innerHTML = "";
  step.options.forEach((opt) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "quiz__option";
    btn.textContent = opt;
    if (quizState.answers[step.id] === opt) {
      btn.classList.add("selected");
    }
    btn.addEventListener("click", () => {
      quizState.answers[step.id] = opt;
      [...quizOptionsEl.children].forEach((c) =>
        c.classList.remove("selected")
      );
      btn.classList.add("selected");
    });
    quizOptionsEl.appendChild(btn);
  });

  quizPrevBtn.disabled = quizState.stepIndex === 0;
  quizNextBtn.textContent =
    quizState.stepIndex === quizSteps.length - 1 ? "Ver resultados" : "Siguiente";
  renderQuizSteps();
};

const applyQuizResults = () => {
  quizState.completed = true;
  const { coverage, support } = quizState.answers;
  let recommendations = products;

  if (coverage && coverage.includes("Baja")) {
    recommendations = recommendations.filter((p) => p.coverage === "baja" || p.category === "bikini");
  } else if (coverage && coverage.includes("Alta")) {
    recommendations = recommendations.filter((p) => p.coverage === "alta" || p.category === "enterizo");
  } else if (coverage) {
    recommendations = recommendations.filter((p) => p.coverage === "media" || p.category === "bikini");
  }

  if (support && support.includes("Soporte")) {
    recommendations = recommendations.filter((p) => p.support === "alto");
  } else if (support && support.includes("reversible")) {
    recommendations = recommendations.filter((p) => p.badges.includes("reversible"));
  }

  if (!recommendations.length) {
    recommendations = products;
  }

  quizSummaryEl.innerHTML = `
    <p>
      Hemos marcado algunos estilos que combinan con lo que elegiste. 
      <strong>Tip:</strong> busca las etiquetas "Soporte alto" y "Reversible".
    </p>
  `;

  renderProducts(recommendations);
  document.getElementById("products").scrollIntoView({ behavior: "smooth" });
};

/* =====================================
   9. NEWSLETTER
   ===================================== */
const newsletterForm = document.getElementById("newsletter-form");
const newsletterModalForm = document.getElementById("newsletter-modal-form");
const newsletterModal = document.getElementById("newsletter-modal");

const handleNewsletterSubmit = (email, fromModal = false) => {
  if (!email || !email.includes("@")) {
    showToast("Por favor ingresa un correo válido");
    return;
  }
  localStorage.setItem("perleNewsletter", email);
  localStorage.setItem("perleNewsletterJoined", "true");
  showToast("Gracias por unirte al Perle Club 🐚");
  if (fromModal) {
    closeNewsletterModal();
  }
};

const openNewsletterModal = () => {
  if (localStorage.getItem("perleNewsletterJoined") === "true") return;
  setOverlay(true);
  newsletterModal.classList.add("show");
};

const closeNewsletterModal = () => {
  newsletterModal.classList.remove("show");
  setOverlay(false);
};

/* =====================================
   10. THEME & NAV
   ===================================== */
const themeButton = document.getElementById("theme-button");
const darkTheme = "dark-theme";
const iconTheme = "ri-sun-line";

const selectedTheme = localStorage.getItem("selected-theme");
const selectedIcon = localStorage.getItem("selected-icon");

if (selectedTheme) {
  document.body.classList[selectedTheme === "dark" ? "add" : "remove"](darkTheme);
  themeButton.classList[selectedIcon === iconTheme ? "add" : "remove"](iconTheme);
}

themeButton.addEventListener("click", () => {
  document.body.classList.toggle(darkTheme);
  themeButton.classList.toggle(iconTheme);
  localStorage.setItem(
    "selected-theme",
    document.body.classList.contains(darkTheme) ? "dark" : "light"
  );
  localStorage.setItem(
    "selected-icon",
    themeButton.classList.contains(iconTheme) ? iconTheme : "ri-moon-line"
  );
});

const navMenu = document.getElementById("nav-menu");
const navToggle = document.getElementById("nav-toggle");
const navClose = document.getElementById("nav-close");

if (navToggle) {
  navToggle.addEventListener("click", () => {
    navMenu.classList.add("show-menu");
  });
}
if (navClose) {
  navClose.addEventListener("click", () => {
    navMenu.classList.remove("show-menu");
  });
}

document.querySelectorAll(".nav__link").forEach((link) => {
  link.addEventListener("click", () => navMenu.classList.remove("show-menu"));
});

window.addEventListener("scroll", () => {
  const header = document.getElementById("header");
  const scrollTopBtn = document.getElementById("scroll-top");
  if (window.scrollY >= 60) header.classList.add("scroll-header");
  else header.classList.remove("scroll-header");

  if (window.scrollY >= 350) scrollTopBtn.classList.add("show");
  else scrollTopBtn.classList.remove("show");
});

document.getElementById("scroll-top").addEventListener("click", () => {
  window.scrollTo({ top: 0, behavior: "smooth" });
});

/* =====================================
   11. EVENTS
   ===================================== */
// Productos (delegación)
productsGrid.addEventListener("click", (e) => {
  const addBtn = e.target.closest("[data-add-cart]");
  const wishBtn = e.target.closest(".product-card__wishlist");
  const quickviewBtn = e.target.closest("[data-quickview]");

  if (addBtn) {
    const id = parseInt(addBtn.dataset.addCart, 10);
    addToCart(id);
  }

  if (wishBtn) {
    const id = parseInt(wishBtn.dataset.id, 10);
    toggleWishlist(id);
  }

  if (quickviewBtn) {
    const id = parseInt(quickviewBtn.dataset.quickview, 10);
    openQuickview(id);
  }
});

// Cart
document.getElementById("cart-btn").addEventListener("click", openCart);
document.getElementById("cart-close").addEventListener("click", closeCart);
document.getElementById("cart-clear-btn").addEventListener("click", () => {
  cart = [];
  renderCart();
  showToast("Bolsa vaciada 🧺");
});

cartItemsContainer.addEventListener("click", (e) => {
  const dec = e.target.closest("[data-qty-dec]");
  const inc = e.target.closest("[data-qty-inc]");
  const rm = e.target.closest("[data-remove]");
  if (dec) {
    const id = parseInt(dec.dataset.qtyDec, 10);
    const item = cart.find((i) => i.id === id);
    if (!item) return;
    item.qty -= 1;
    if (item.qty <= 0) {
      cart = cart.filter((i) => i.id !== id);
    }
    renderCart();
  }
  if (inc) {
    const id = parseInt(inc.dataset.qtyInc, 10);
    const item = cart.find((i) => i.id === id);
    if (!item) return;
    item.qty += 1;
    renderCart();
  }
  if (rm) {
    const id = parseInt(rm.dataset.remove, 10);
    cart = cart.filter((i) => i.id !== id);
    renderCart();
  }
});

// Checkout
document.getElementById("checkout-btn").addEventListener("click", () => {
  if (!cart.length) {
    showToast("Tu bolsa está vacía");
    return;
  }
  let totalCOP = 0;
  const lines = cart.map((i) => {
    totalCOP += i.priceCOP * i.qty;
    return `${i.qty} x ${i.name}`;
  });
  const totalText = formatPrice(totalCOP);
  const msg = `Hola Perle! Quiero finalizar mi compra:%0A%0A${lines.join(
    "%0A"
  )}%0A%0ATotal: ${totalText}`;
  window.open(`https://wa.me/573001234567?text=${msg}`, "_blank");
});

// Quickview
document
  .getElementById("quickview-close")
  .addEventListener("click", closeQuickview);

quickviewBody.addEventListener("click", (e) => {
  const addBtn = e.target.closest("[data-add-cart]");
  const sizeBtn = e.target.closest(".quickview__size");
  if (sizeBtn) {
    [...quickviewBody.querySelectorAll(".quickview__size")].forEach((s) =>
      s.classList.remove("selected")
    );
    sizeBtn.classList.add("selected");
  }
  if (addBtn) {
    const id = parseInt(addBtn.dataset.addCart, 10);
    const selectedSize =
      quickviewBody.querySelector(".quickview__size.selected")?.dataset.size ||
      products.find((p) => p.id === id)?.sizes[0];
    const product = products.find((p) => p.id === id);
    if (!product) return;
    const existing = cart.find((i) => i.id === id && i.size === selectedSize);
    if (existing) {
      existing.qty += 1;
    } else {
      cart.push({
        ...product,
        qty: 1,
        size: selectedSize,
      });
    }
    renderCart();
    showToast(`✨ ${product.name} (${selectedSize}) añadido a tu bolsa`);
    openCart();
  }
});

// Overlay cerrar
document.getElementById("overlay").addEventListener("click", () => {
  closeCart();
  closeQuickview();
  closeNewsletterModal();
});

// Currency
const currencySelect = document.getElementById("currency-select");
currencySelect.value = currency;
currencySelect.addEventListener("change", (e) => {
  currency = e.target.value;
  syncStorage();
  renderProducts(getFilteredProducts());
  renderCart();
});

// Quiz
quizPrevBtn.addEventListener("click", () => {
  if (quizState.stepIndex === 0) return;
  quizState.stepIndex -= 1;
  renderQuizStep();
});
quizNextBtn.addEventListener("click", () => {
  const step = quizSteps[quizState.stepIndex];
  if (!quizState.answers[step.id]) {
    showToast("Selecciona una opción para continuar");
    return;
  }
  if (quizState.stepIndex === quizSteps.length - 1) {
    applyQuizResults();
  } else {
    quizState.stepIndex += 1;
    renderQuizStep();
  }
});

// Newsletter forms
newsletterForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const email = document.getElementById("newsletter-email").value.trim();
  handleNewsletterSubmit(email, false);
  newsletterForm.reset();
});

newsletterModalForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const email = document
    .getElementById("newsletter-modal-email")
    .value.trim();
  handleNewsletterSubmit(email, true);
  newsletterModalForm.reset();
});

document
  .getElementById("newsletter-close")
  .addEventListener("click", closeNewsletterModal);

// Fit WhatsApp
document.getElementById("fit-whatsapp").addEventListener("click", () => {
  const url =
    "https://wa.me/573001234567?text=Hola%20Perle!%20Quiero%20enviarte%20mis%20medidas%20para%20que%20me%20ayudes%20a%20elegir%20talla%20👙";
  window.open(url, "_blank");
});

// Newsletter modal delay
setTimeout(openNewsletterModal, 5500);

/* =====================================
   12. INIT
   ===================================== */
const init = () => {
  renderProducts();
  renderCart();
  initFilters();
  renderQuizSteps();
  renderQuizStep();
};

init();
