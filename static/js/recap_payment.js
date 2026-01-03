document.addEventListener("DOMContentLoaded", () => {
  const buttons = document.querySelectorAll(".pay-btn");

  buttons.forEach(btn => {
    btn.addEventListener("click", async () => {
      const provider = btn.dataset.provider;
      const reference = btn.dataset.reference;

      console.log("Paiement init :", provider, reference);

      btn.disabled = true;
      btn.innerText = "⏳ Initialisation du paiement...";

      try {
        const res = await fetch("/paiement/init", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": window.csrfToken
          },
          body: JSON.stringify({
            provider: provider,
            reference: reference
          })
        });

        const data = await res.json();

        if (!res.ok || data.error) {
          throw new Error(data.error || "Erreur paiement");
        }

        if (!data.payment_url) {
          throw new Error("URL de paiement manquante");
        }

        // 🔥 REDIRECTION ORANGE / WAVE
        window.location.href = data.payment_url;

      } catch (err) {
        alert("❌ " + err.message);
        btn.disabled = false;
        btn.innerText =
          provider === "orange"
            ? "🟠 Payer avec Orange Money"
            : "🌊 Payer avec Wave";
      }
    });
  });
});
