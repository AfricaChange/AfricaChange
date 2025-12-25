function adminAction(action, reference) {
  const reason = prompt("Motif obligatoire :");
  if (!reason) return;

  fetch(`/admin/actions/${action}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrf_token
    },
    body: JSON.stringify({
      reference: reference,
      reason: reason
    })
  })
  .then(r => r.json())
  .then(data => {
    if (data.success) {
      alert("Action effectuée avec succès");
      location.reload();
    } else {
      alert(data.error || "Erreur");
    }
  });
}

function adminRefund(reference) {
  const amount = prompt("Montant à rembourser :");
  const reason = prompt("Motif du remboursement :");

  if (!amount || !reason) return;

  fetch("/admin/actions/refund", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrf_token
    },
    body: JSON.stringify({
      reference: reference,
      amount: amount,
      reason: reason
    })
  })
  .then(r => r.json())
  .then(data => {
    if (data.success) {
      alert("Remboursement effectué");
      location.reload();
    } else {
      alert(data.error || "Erreur");
    }
  });
}


let adminAction = null;
let adminReference = null;

function openAdminModal(action, reference) {
  adminAction = action;
  adminReference = reference;

  document.getElementById("adminModal").classList.remove("hidden");
  document.getElementById("adminModalTitle").innerText =
    action === "validate" ? "Validation manuelle" :
    action === "block" ? "Blocage de transaction" :
    "Remboursement";

  document.getElementById("refundAmount").classList.toggle(
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
    alert("La raison est obligatoire");
    return;
  }

  const payload = {
    reference: adminReference,
    reason: reason
  };

  if (adminAction === "refund") {
    payload.amount = parseFloat(
      document.getElementById("refundAmount").value
    );
  }

  fetch(`/admin/actions/${adminAction}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": window.csrfToken
    },
    body: JSON.stringify(payload)
  })
  .then(r => r.json())
  .then(() => window.location.reload())
  .catch(() => alert("Erreur admin"));
}
