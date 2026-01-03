document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".pay-btn").forEach(btn => {
    btn.addEventListener("click", async () => {
      const provider = btn.dataset.provider;
      const reference = btn.dataset.reference;

      const phone = prompt("Numéro de téléphone de paiement :");
      if (!phone) return;

      try {
        const response = await fetch("/paiement/init", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": window.csrfToken
          },
          body: JSON.stringify({
            provider: provider,
            reference: reference,
            phone: phone
          })
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
          alert(data.error || "Erreur paiement");
          return;
        }

        if (data.payment_url) {
          window.location.href = data.payment_url;
        } else {
          alert("Lien de paiement indisponible");
        }

      } catch (e) {
        alert("Erreur réseau");
        console.error(e);
      }
    });
  });
});
