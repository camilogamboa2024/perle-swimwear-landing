(() => {
  const body = document.body;
  if (!body) return;

  body.classList.add("perle-admin-theme");
  if (document.getElementById("login-form")) {
    body.classList.add("perle-admin-login");
  }

  document.querySelectorAll(".messagelist li").forEach((message) => {
    window.setTimeout(() => {
      message.style.opacity = "0";
      message.style.transition = "opacity 220ms ease";
      window.setTimeout(() => message.remove(), 240);
    }, 4200);
  });

  document.querySelectorAll("[title]").forEach((node) => {
    if (!node.getAttribute("data-toggle")) {
      node.setAttribute("data-toggle", "tooltip");
    }
  });
})();
