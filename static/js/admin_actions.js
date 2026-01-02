let currentAction = null;
let currentReference = null;

function openAdminModal(action, reference) {
  currentAction = action;
  currentReference = reference;

  document.getElementById("adminModal").classList.remove("hidden");
  document.getElementById("adminReason").value = "";

  document.getElementById("refundAmountWrapper").classList.toggle(
    "hidden",
    action !== "refund"
  );
}

function closeAdminModal() {
  document.getElementById("adminModal").classList.add("hidden");
}

function confirmAdminAction() {
  const reason = document.getElementById("adminReason").value.trim();
  if (!reason) {
    alert("Motif obligatoire");
    return;
  }

  const payload = {
    reference: currentReference,
    reason: reason
  };

  if (currentAction === "refund") {
    payload.amount = parseFloat(
      document.getElementById("refundAmount").value
    );
    if (!payload.amount || payload.amount <= 0) {
      alert("Montant invalide");
      return;
    }
  }

  fetch(`/admin/actions/${currentAction}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": window.csrfToken
    },
    body: JSON.stringify(payload)
  })
  .then(r => r.json())
  .then(data => {
    if (data.success) {
      location.reload();
    } else {
      alert(data.error || "Erreur admin");
    }
  })
  .catch(() => alert("Erreur réseau"));
}
