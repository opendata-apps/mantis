// Red error toast shared by the admin pages. One at a time; it closes after
// 4 s unless the pointer or focus rests on it, or with its close button.
export function showToast(message) {
    document.querySelector('[data-toast]')?.remove();
    const toast = document.createElement('div');
    toast.dataset.toast = '';
    toast.className = 'fixed top-4 right-4 z-[9999] flex items-center gap-2 py-3 pr-2 pl-4 '
        + 'text-sm font-medium text-red-800 bg-red-100 rounded-lg border border-red-300 shadow-lg';
    toast.setAttribute('role', 'alert');

    const text = document.createElement('span');
    text.textContent = message;
    const close = document.createElement('button');
    close.type = 'button';
    close.textContent = '×';
    close.setAttribute('aria-label', 'Meldung schließen');
    close.className = 'px-2 text-lg/none rounded-sm hover:bg-red-200 focus-visible:ring-2 focus-visible:ring-red-500';
    close.addEventListener('click', () => toast.remove());
    toast.append(text, close);

    let timer;
    const start = () => { timer = window.setTimeout(() => toast.remove(), 4000); };
    const pause = () => window.clearTimeout(timer);
    toast.addEventListener('pointerenter', pause);
    toast.addEventListener('pointerleave', start);
    toast.addEventListener('focusin', pause);
    toast.addEventListener('focusout', start);

    // An open modal dialog makes the rest of the page inert and covers it, so
    // the toast goes inside it.
    (document.querySelector('dialog:modal') ?? document.body).append(toast);
    start();
}
