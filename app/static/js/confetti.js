// Canvas confetti for celebration - auto-initializes from data attributes
import confetti from 'canvas-confetti';

function sprayConfetti() {
  confetti({
    particleCount: 100,
    spread: 70,
    origin: { y: 0.6 }
  });
}

function fireworks() {
  const duration = 15 * 1000;
  const animationEnd = Date.now() + duration;
  const defaults = { startVelocity: 30, spread: 360, ticks: 60, zIndex: 0 };

  function randomInRange(min, max) {
    return Math.random() * (max - min) + min;
  }

  const interval = setInterval(() => {
    const timeLeft = animationEnd - Date.now();

    if (timeLeft <= 0) {
      return clearInterval(interval);
    }

    const particleCount = 50 * (timeLeft / duration);
    confetti({ ...defaults, particleCount, origin: { x: randomInRange(0.1, 0.3), y: Math.random() - 0.2 } });
    confetti({ ...defaults, particleCount, origin: { x: randomInRange(0.7, 0.9), y: Math.random() - 0.2 } });
  }, 250);
}

function danceMantis() {
  const mantis = document.getElementById('dancingMantis');
  if (mantis) {
    mantis.classList.add('dancing');
    setTimeout(() => mantis.classList.remove('dancing'), 1000);
  }
}

function openModal() {
  const modal = document.getElementById('thanksModal');
  if (!modal) return;

  modal.classList.remove('opacity-0', 'pointer-events-none');
  const innerDiv = modal.querySelector('div:nth-child(2)');
  if (innerDiv) innerDiv.classList.remove('scale-95');
  document.body.style.overflow = 'hidden';
  sprayConfetti();
  fireworks();
  danceMantis();
}

function closeModal() {
  const modal = document.getElementById('thanksModal');
  if (!modal) return;

  modal.classList.add('opacity-0', 'pointer-events-none');
  const innerDiv = modal.querySelector('div:nth-child(2)');
  if (innerDiv) innerDiv.classList.add('scale-95');
  document.body.style.overflow = '';
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  const modal = document.getElementById('thanksModal');
  if (!modal) return;

  // Open modal after 1 second delay
  setTimeout(openModal, 1000);

  // Close modal when close button is clicked
  const closeBtn = document.getElementById('closeModal');
  if (closeBtn) {
    closeBtn.addEventListener('click', closeModal);
  }

  // More confetti button
  const moreConfettiBtn = document.getElementById('moreConfetti');
  if (moreConfettiBtn) {
    moreConfettiBtn.addEventListener('click', () => {
      sprayConfetti();
      danceMantis();
    });
  }
});
