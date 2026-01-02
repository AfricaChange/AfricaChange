document.addEventListener("DOMContentLoaded", () => {
  const buttons = document.querySelectorAll("[data-pay]");

  buttons.forEach(btn => {
    btn.addEventListener("click", async () => {
      const provider = btn.dataset.provider;
      const reference = btn.dataset.reference;

      alert("CLIC OK : " + provider + " / " + reference);

      // Étape suivante : appel backend
    });
  });
});
