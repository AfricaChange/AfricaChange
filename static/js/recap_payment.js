async function secureSubmit(btn) {
  const provider = btn.dataset.provider;
  const reference = btn.dataset.reference;

  const res = await fetch(`/paiement/${provider}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ reference })
  });

  const data = await res.json();

  if (data.payment_url) {
    window.location.href = data.payment_url;
  } else {
    alert(data.error || "Erreur paiement");
  }
}
