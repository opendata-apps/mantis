// HTMX for admin report card interactions
import htmx from 'htmx.org';
window.htmx = htmx;

// CSRF via meta tag (admin uses <meta name="csrf-token">)
document.body.addEventListener('htmx:configRequest', (event) => {
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
    if (csrfToken) {
        event.detail.headers['X-CSRFToken'] = csrfToken;
    }
});

// When a card is removed (HX-Reswap:delete), check if container is now empty → reload
document.body.addEventListener('htmx:afterSwap', (event) => {
    if (!event.detail.target?.closest('#reportContainer')) return;
    const container = document.getElementById('reportContainer');
    if (container && container.querySelectorAll('.report-card').length === 0) {
        location.reload();
    }
});

// Show brief error toast on failed HTMX requests (4xx/5xx)
document.body.addEventListener('htmx:responseError', (event) => {
    const status = event.detail.xhr?.status;
    if (!status) return;

    const toast = document.createElement('div');
    toast.className = 'fixed top-4 right-4 z-[9999] flex items-center gap-2 px-4 py-3 '
        + 'text-sm font-medium text-red-800 bg-red-100 rounded-lg border border-red-300 shadow-lg';
    toast.setAttribute('role', 'alert');
    toast.textContent = status >= 500
        ? 'Serverfehler — bitte Seite neu laden.'
        : 'Aktion fehlgeschlagen.';

    document.body.appendChild(toast);
    window.setTimeout(function () { toast.remove(); }, 4000);
});
