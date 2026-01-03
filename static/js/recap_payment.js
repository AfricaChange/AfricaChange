document.addEventListener("DOMContentLoaded", () => {
  const buttons = document.querySelectorAll("[data-provider]");

  buttons.forEach(btn => {
    btn.addEventListener("click", async () => {
      const provider = btn.dataset.provider;
      const reference = btn.dataset.reference;

      const phone = prompt("Numéro de téléphone de paiement :");
      if (!phone) return;

      try {
        const res = await fetch("/paiement/init", {
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

        const data = await res.json();

        if (!res.ok || data.error) {
          alert(data.error || "Erreur paiement");
          return;
        }

        // 🔴 REDIRECTION VERS ORANGE / WAVE
        if (data.payment_url) {
          window.location.href = data.payment_url;
        } else {
          alert("Lien de paiement non reçu");
        }

      } catch (err) {
        console.error(err);
        alert("Erreur réseau");
      }
    });
  });
});
