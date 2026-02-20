(() => {
  const palette = {
    text: "#173447",
    muted: "rgba(95, 119, 135, 0.9)",
    grid: "rgba(15, 143, 178, 0.16)",
    aqua: "#0f8fb2",
    aquaSoft: "rgba(15, 143, 178, 0.22)",
    pearl: "#f2dfbf",
    pearlSoft: "rgba(242, 223, 191, 0.38)",
    infoSoft: "rgba(43, 120, 178, 0.62)",
  };

  function axisOptions() {
    return {
      ticks: { color: palette.muted },
      grid: { color: palette.grid },
      border: { color: palette.grid },
    };
  }

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
            borderColor: palette.pearl,
            backgroundColor: palette.pearlSoft,
            pointBackgroundColor: palette.pearl,
            pointRadius: 3,
            fill: true,
            tension: 0.34,
          },
        ],
      },
      options: {
        plugins: {
          legend: {
            labels: {
              color: palette.text,
            },
          },
        },
        scales: {
          x: axisOptions(),
          y: axisOptions(),
        },
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
            backgroundColor: palette.infoSoft,
            borderRadius: 7,
            maxBarThickness: 22,
          },
        ],
      },
      options: {
        plugins: {
          legend: {
            labels: {
              color: palette.text,
            },
          },
        },
        scales: {
          x: axisOptions(),
          y: axisOptions(),
        },
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
              "#0f8fb2",
              "#f2dfbf",
              "#2f8f62",
              "#a1701a",
              "#b24a57",
              "#2b78b2",
            ],
            borderColor: "#ffffff",
            borderWidth: 2,
          },
        ],
      },
      options: {
        plugins: {
          legend: {
            labels: {
              color: palette.text,
            },
          },
        },
      },
    });
  }
})();
