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
function secureSubmit(button) {
  if (!button || !button.form) return;

  // Désactiver le bouton
  button.disabled = true;
  button.classList.add("opacity-50", "cursor-not-allowed");

  // Changer le texte (UX rassurante)
  const originalText = button.innerText;
  button.dataset.originalText = originalText;
  button.innerText = "Traitement…";

  // Afficher loader
  showLoader();

  // Soumettre le formulaire
  button.form.submit();
}

/* 🔁 Bouton retour sécurisé */
function safeBack() {
  showLoader();
  setTimeout(() => {
    window.history.back();
  }, 300);
}
