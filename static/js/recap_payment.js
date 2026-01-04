document.addEventListener("DOMContentLoaded", () => {
  const buttons = document.querySelectorAll("[data-provider]");

  buttons.forEach(btn => {
    btn.addEventListener("click", async () => {
      const provider = btn.dataset.provider;
      const reference = btn.dataset.reference;

      const telephone = prompt("Numéro de téléphone de paiement :");
      if (!telephone) {
        alert("Numéro requis");
        return;
      }

      try {
        const response = await fetch("/paiement/orange", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": window.csrfToken
          },
          body: JSON.stringify({
            reference: reference,
            telephone: telephone
          })
        });

        const data = await response.json();

        if (!response.ok) {
          alert(data.error || "Erreur paiement");
          return;
        }

        if (data.payment_url) {
          window.location.href = data.payment_url; // 🚀 REDIRECTION ORANGE
        } else {
          alert("URL de paiement introuvable");
        }

      } catch (err) {
        console.error(err);
        alert("Erreur réseau");
      }
    });
  });
});
