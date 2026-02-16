// Shared native image modal helpers
// Used by provider and admin pages via global window bindings.

function syncDialogScrollLock() {
  var hasOpenDialog = Boolean(document.querySelector('dialog[open]'));
  document.documentElement.classList.toggle('dialog-open', hasOpenDialog);
  document.body.classList.toggle('dialog-open', hasOpenDialog);
}

function openImageModal(imageUrl) {
  var imageModal = document.getElementById('imageModal');
  var modalImage = document.getElementById('modalImage');
  if (!imageModal || !modalImage) return;
  modalImage.src = imageUrl;
  if (!imageModal.open) imageModal.showModal();
  syncDialogScrollLock();
}

function closeImageModal() {
  var imageModal = document.getElementById('imageModal');
  if (imageModal && imageModal.open) imageModal.close();
  syncDialogScrollLock();
}

function openImageNewTab() {
  var modalImage = document.getElementById('modalImage');
  if (!modalImage || !modalImage.src) return;
  window.open(modalImage.src, '_blank');
}

function bindImageModal() {
  var imageDialog = document.getElementById('imageModal');
  if (!imageDialog || imageDialog.dataset.bound === 'true') return;
  imageDialog.dataset.bound = 'true';
  imageDialog.addEventListener('click', function (e) {
    if (e.target === imageDialog) closeImageModal();
  });
  imageDialog.addEventListener('close', syncDialogScrollLock);
}

document.addEventListener('DOMContentLoaded', function () {
  bindImageModal();
  syncDialogScrollLock();
});

window.openImageModal = openImageModal;
window.closeImageModal = closeImageModal;
window.openImageNewTab = openImageNewTab;

export {
  bindImageModal,
  closeImageModal,
  openImageModal,
  openImageNewTab,
  syncDialogScrollLock,
};
