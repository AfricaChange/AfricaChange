function openAdminModal(action, reference) {
  const modal = document.getElementById("adminModal");
  if (!modal) return;

  modal.querySelector("input[name='action']").value = action;
  modal.querySelector("input[name='reference']").value = reference;

  modal.classList.remove("hidden");
}

function closeAdminModal() {
  document.getElementById("adminModal").classList.add("hidden");
}
