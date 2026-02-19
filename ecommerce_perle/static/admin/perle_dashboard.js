(() => {
  const palette = {
    text: "#dceaf4",
    muted: "rgba(178, 204, 223, 0.82)",
    grid: "rgba(121, 177, 210, 0.18)",
    aqua: "#34c3e6",
    aquaSoft: "rgba(52, 195, 230, 0.2)",
    pearl: "#f1dfbe",
    pearlSoft: "rgba(241, 223, 190, 0.24)",
    infoSoft: "rgba(121, 183, 238, 0.72)",
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
              "#34c3e6",
              "#f1dfbe",
              "#4dc18d",
              "#e3b465",
              "#e07878",
              "#79b7ee",
            ],
            borderColor: "#0f2538",
            borderWidth: 1,
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
