(() => {
  function parseJsonScript(id) {
    const node = document.getElementById(id);
    if (!node) return null;
    try {
      return JSON.parse(node.textContent);
    } catch (_) {
      return null;
    }
  }

  const series7d = parseJsonScript("kpi-series-7d");
  const series30d = parseJsonScript("kpi-series-30d");
  const statusDistribution = parseJsonScript("kpi-status-distribution") || [];

  const ordersCanvas = document.getElementById("perle-orders-7d-chart");
  if (ordersCanvas && series7d && Array.isArray(series7d.labels)) {
    new window.Chart(ordersCanvas, {
      type: "line",
      data: {
        labels: series7d.labels,
        datasets: [
          {
            label: "Órdenes",
            data: series7d.orders || [],
            borderColor: "#f0d4a5",
            backgroundColor: "rgba(240, 212, 165, 0.14)",
          },
        ],
      },
    });
  }

  const revenueCanvas = document.getElementById("perle-revenue-30d-chart");
  if (revenueCanvas && series30d && Array.isArray(series30d.labels)) {
    new window.Chart(revenueCanvas, {
      type: "bar",
      data: {
        labels: series30d.labels,
        datasets: [
          {
            label: "Ingresos",
            data: series30d.revenue || [],
            backgroundColor: "rgba(116, 164, 231, 0.68)",
          },
        ],
      },
    });
  }

  const statusCanvas = document.getElementById("perle-status-chart");
  if (statusCanvas && statusDistribution.length) {
    new window.Chart(statusCanvas, {
      type: "doughnut",
      data: {
        labels: statusDistribution.map((row) => row.label),
        datasets: [
          {
            label: "Estados",
            data: statusDistribution.map((row) => row.value),
            backgroundColor: [
              "#f0d4a5",
              "#74a4e7",
              "#3fbe8a",
              "#e1ac5c",
              "#e77474",
              "#9eafc3",
            ],
          },
        ],
      },
    });
  }
})();
