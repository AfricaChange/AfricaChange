document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-provider]").forEach(btn => {
    btn.addEventListener("click", async () => {
      const provider = btn.dataset.provider;
      const reference = btn.dataset.reference;

      try {
        const res = await fetch(`/paiement/${provider}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ reference })
        });

        const text = await res.text();
        console.log("BACKEND RESPONSE:", text);

        const data = JSON.parse(text);

        if (data.payment_url) {
          window.location.href = data.payment_url;
        } else {
          alert(data.error || "Erreur paiement");
        }

      } catch (e) {
        console.error(e);
        alert("Erreur réseau ou serveur");
      }
    });
  });
});
