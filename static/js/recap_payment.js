document.addEventListener("DOMContentLoaded", () => {
  console.log("recap_payment.js chargé ✅");

  const buttons = document.querySelectorAll("[data-provider]");

  if (buttons.length === 0) {
    console.warn("Aucun bouton paiement détecté ❌");
    return;
  }

  buttons.forEach((btn) => {
    btn.addEventListener("click", async () => {
      const provider = btn.dataset.provider;
      const reference = btn.dataset.reference;

      console.log("CLICK →", provider, reference);

      if (provider !== "orange") {
        alert("Provider non supporté");
        return;
      }

      const telephone = prompt("Numéro Orange Money :");
      if (!telephone) return;

      try {
        const response = await fetch("/paiement/orange", {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            reference: reference,
            telephone: telephone
          })
        });

        const data = await response.json();
        console.log("BACKEND RESPONSE:", data);

        if (!response.ok) {
          alert(data.error || "Erreur paiement");
          return;
        }

        if (data.payment_url) {
          window.location.href = data.payment_url;
        } else {
          alert("URL de paiement manquante");
        }

      } catch (e) {
        console.error("Erreur JS paiement", e);
        alert("Erreur réseau");
      }
    });
  });
});
