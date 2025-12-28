let lastUpdate = 0;

async function refreshAdminStats() {
  try {
    const res = await fetch("/admin/realtime/stats");
    if (!res.ok) return;

    const data = await res.json();

    // Transactions
    document.getElementById("stat-pending").innerText = data.transactions.pending;
    document.getElementById("stat-blocked").innerText = data.transactions.blocked;
    document.getElementById("stat-success").innerText = data.transactions.success;

    // Volume
    document.getElementById("stat-volume").innerText =
      data.volume.total.toLocaleString() + " FCFA";

    // Alerts
    document.getElementById("stat-risks").innerText = data.risks.alerts;

    lastUpdate = Date.now();
  } catch (e) {
    console.error("Admin realtime error", e);
  }
}

// Toutes les 7 secondes (équilibre charge / réactivité)
setInterval(refreshAdminStats, 7000);

// Chargement initial
refreshAdminStats();
