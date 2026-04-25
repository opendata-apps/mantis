// HTMX - only used in statistics pages
import htmx from 'htmx.org';

window.htmx = htmx;

// CSP hardening: disable eval-based attribute features (hx-on::*, `js:` prefix).
// No statistics page uses them; this lets us drop `unsafe-eval` from CSP.
htmx.config.allowEval = false;
