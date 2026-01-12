// Admin-specific functionality
// Only loaded on admin pages

import { DateRangePicker, Datepicker } from 'flowbite-datepicker';

// Register German locale
Datepicker.locales.de = {
  days: ["Sonntag", "Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag"],
  daysShort: ["So", "Mo", "Di", "Mi", "Do", "Fr", "Sa"],
  daysMin: ["So", "Mo", "Di", "Mi", "Do", "Fr", "Sa"],
  months: ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"],
  monthsShort: ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"],
  today: "Heute",
  monthsTitle: "Monate",
  clear: "Löschen",
  weekStart: 1,
  format: "dd.mm.yyyy"
};

// Initialize date range pickers on page load
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[date-rangepicker]').forEach(el => {
    // Read options from data attributes (matching original Flowbite behavior)
    const format = el.getAttribute('datepicker-format') || 'dd.mm.yyyy';
    const buttons = el.hasAttribute('datepicker-buttons');
    const autoSelectToday = el.hasAttribute('datepicker-autoselect-today');

    // Note: autohide is NOT used for DateRangePicker - users need to select two dates
    new DateRangePicker(el, {
      format: format,
      language: 'de',
      todayBtn: buttons,
      todayBtnMode: 1,  // 1 = select today's date (not just navigate to current month)
      clearBtn: buttons,
      todayHighlight: true,
      autoSelectToday: autoSelectToday ? 1 : 0
    });
  });
});
