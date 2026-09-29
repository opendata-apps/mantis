// Site header: mobile menu and scrolled state. Loaded by layout.html on every public page.
const toggle = document.getElementById('nav-toggle');
const nav = document.getElementById('nav-links');
const header = document.querySelector('.site-header');

function openMenu() {
  nav.classList.add('open');
  header.classList.add('menu-open');
  toggle.setAttribute('aria-expanded', 'true');
}

function closeMenu() {
  nav.classList.remove('open');
  toggle.setAttribute('aria-expanded', 'false');

  // Keep the header background until the collapse transition has finished
  function onTransitionEnd(e) {
    if (e.propertyName === 'max-height') {
      // Only remove bg if menu is still closed (handles rapid clicks)
      if (!nav.classList.contains('open')) {
        header.classList.remove('menu-open');
      }
      nav.removeEventListener('transitionend', onTransitionEnd);
    }
  }
  nav.addEventListener('transitionend', onTransitionEnd);
}

toggle.addEventListener('click', () => nav.classList.contains('open') ? closeMenu() : openMenu());

// Close on click outside
document.addEventListener('click', (e) => {
  if (!nav.contains(e.target) && !toggle.contains(e.target) && nav.classList.contains('open')) {
    closeMenu();
  }
});

// Close on ESC
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && nav.classList.contains('open')) closeMenu();
});

window.addEventListener('scroll', () => {
  header.classList.toggle('scrolled', window.scrollY > 10);
}, { passive: true });

console.log("%cGottesanbeterin Gesucht! 🦗", "background-color: #10B981; color: #FFF; font-size: 24px; padding: 10px 20px; border-radius: 5px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);");
console.log("%cHallo Entdecker! 🌍", "font-size: 18px; font-weight: bold; padding: 5px; border-bottom: 2px solid #E5E7EB;");
console.log("🕵️‍♂️ Du scheinst ein Auge für Details zu haben. Wenn du tiefer eintauchen oder beitragen möchtest, sieh dir unser GitLab-Repository an!");
console.log("%c🔗 https://gitlab.com/opendata-apps/mantis", "color: #3B82F6; font-size: 16px; font-weight: bold;");
