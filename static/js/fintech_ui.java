/* ======================================================
   AfricaChange – UX FINTECH GLOBAL
   Règles :
   - Empêche double clic
   - Affiche le loader global
   - Sécurise les actions financières
====================================================== */

/* 🔄 Loader global (déjà présent dans base.html) */
function showLoader() {
  const loader = document.getElementById("globalLoader");
  if (loader) loader.classList.remove("hidden");
}

function hideLoader() {
  const loader = document.getElementById("globalLoader");
  if (loader) loader.classList.add("hidden");
}

/* 🔐 Soumission sécurisée (ANTI DOUBLE PAIEMENT) */
let paymentLocked = false;

function secureSubmit(button) {
  if (paymentLocked) return;

  const provider = button.dataset.provider;
  const reference = button.dataset.reference;

  if (!provider || !reference) {
    alert("Erreur interne. Veuillez rafraîchir la page.");
    return;
  }

  paymentLocked = true;

  button.disabled = true;
  button.classList.add("opacity-50", "cursor-not-allowed");
  button.innerText = "Connexion au service…";

  showLoader();

  // Redirection explicite et contrôlée
  window.location.href = `/paiement/${provider}?reference=${reference}`;
}


/* 🔁 Bouton retour sécurisé */
function safeBack() {
  showLoader();
  setTimeout(() => {
    window.history.back();
  }, 300);
}
