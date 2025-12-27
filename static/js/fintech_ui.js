/* ======================================================
   AfricaChange – UX FINTECH GLOBAL (PRO SAFE VERSION)
   - Anti double paiement
   - Loader global
   - UX mobile safe
   - Redirection contrôlée
====================================================== */

/* 🔄 Loader global */
function showLoader() {
  const loader = document.getElementById("globalLoader");
  if (loader) loader.classList.remove("hidden");
}

function hideLoader() {
  const loader = document.getElementById("globalLoader");
  if (loader) loader.classList.add("hidden");
}

/* 🔐 Verrou global paiement */
let paymentLocked = false;

/* 🔐 Soumission sécurisée */
async function secureSubmit(button) {
  if (paymentLocked) return;

  const provider = button.dataset.provider;
  const reference = button.dataset.reference;

  if (!provider || !reference) {
    alert("Erreur interne. Veuillez rafraîchir la page.");
    return;
  }

  paymentLocked = true;

  // UX immédiate
  button.disabled = true;
  button.classList.add("opacity-50", "cursor-not-allowed");
  const originalText = button.innerText;
  button.innerText = "Connexion au service…";

  showLoader();

  try {
    /* 🔐 Appel API sécurisé (POST) */
    const response = await fetch(`/paiement/${provider}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest"
      },
      body: JSON.stringify({
        reference: reference
      })
    });

    const data = await response.json();

    if (!response.ok || !data.payment_url) {
      throw new Error(data.error || "Erreur de paiement");
    }

    /* 🔁 Redirection provider */
    window.location.href = data.payment_url;

  } catch (error) {
    // 🔁 Rollback UX propre
    paymentLocked = false;
    hideLoader();

    button.disabled = false;
    button.classList.remove("opacity-50", "cursor-not-allowed");
    button.innerText = originalText;

    alert(
      "Impossible de contacter le service de paiement.\n" +
      "Veuillez réessayer dans quelques instants."
    );
  }
}

/* 🔁 Bouton retour sécurisé */
function safeBack() {
  showLoader();
  setTimeout(() => {
    window.history.back();
  }, 300);
}


let adminAction = null;

function openAdminModal(action) {
  adminAction = action;
  document.getElementById("adminModal").classList.remove("hidden");
}

function closeAdminModal() {
  document.getElementById("adminModal").classList.add("hidden");
}

document.getElementById("confirmAdminAction")?.addEventListener("click", () => {
  const reason = document.getElementById("adminReason").value;
  if (!reason) {
    alert("Motif obligatoire");
    return;
  }

  fetch(`/admin/actions/${adminAction}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      reference: TRANSACTION_REFERENCE,
      reason: reason
    })
  }).then(() => location.reload());
});
