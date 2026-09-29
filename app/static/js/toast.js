// Red error toast shared by the admin pages.
export function showToast(message) {
    const toast = document.createElement('div');
    toast.className = 'fixed top-4 right-4 z-[9999] flex items-center gap-2 px-4 py-3 '
        + 'text-sm font-medium text-red-800 bg-red-100 rounded-lg border border-red-300 shadow-lg';
    toast.setAttribute('role', 'alert');
    toast.textContent = message;
    document.body.appendChild(toast);
    window.setTimeout(() => toast.remove(), 4000);
}
