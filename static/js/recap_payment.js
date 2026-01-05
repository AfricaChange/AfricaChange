document.addEventListener("DOMContentLoaded", () => {
  const orangeBtn = document.querySelector(
    "button[data-provider='orange']"
  );

  if (!orangeBtn) return;

  orangeBtn.addEventListener("click", async () => {
    const reference = orangeBtn.dataset.reference;

    const telephone = prompt("Numéro de téléphone de paiement :");
    if (!telephone) return;

    console.log("SEND →", { reference, telephone });

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
      alert(data.error || "Erreur paiement Orange");
     
