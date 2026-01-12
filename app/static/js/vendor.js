// Native UI helpers (dropdowns)
// Close dropdowns when clicking outside, but ignore datepicker clicks

document.addEventListener('click', (e) => {
  // Don't close dropdown if clicking inside a datepicker element
  // The datepicker popup has class 'datepicker-dropdown' and cells have 'datepicker-cell'
  if (e.target.closest('[class*="datepicker"]')) {
    return;
  }

  // Close all open details dropdowns when clicking outside
  document.querySelectorAll('details.dropdown[open]').forEach(dropdown => {
    if (!dropdown.contains(e.target)) {
      dropdown.removeAttribute('open');
    }
  });
});
