// HTMX for admin report card interactions
import htmx from 'htmx.org';
import { showToast } from './toast.js';
window.htmx = htmx;

// When a card is removed (HX-Reswap:delete), check if container is now empty → reload
document.body.addEventListener('htmx:afterSwap', (event) => {
    const container = event.detail.target?.closest('#reportContainer');
    if (!container) return;
    if (container.querySelectorAll('.report-card').length === 0) {
        location.reload();
    }
});

// Show brief error toast on failed HTMX requests (4xx/5xx)
document.body.addEventListener('htmx:responseError', (event) => {
    const status = event.detail.xhr?.status;
    if (!status) return;
    showToast(status >= 500 ? 'Serverfehler — bitte Seite neu laden.' : 'Aktion fehlgeschlagen.');
});
