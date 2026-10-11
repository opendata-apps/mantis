// Celebration dialog on the home page; loaded only when it is rendered.
import confetti from 'canvas-confetti';

const dialog = document.getElementById('thanksModal');
// showModal() puts the dialog in the top layer, so the confetti draws on a
// canvas inside it; the library's own body canvas would end up behind it.
const fire = confetti.create(document.getElementById('confettiCanvas'), {
  resize: true,
  disableForReducedMotion: true,
});

function sprayConfetti() {
  fire({ particleCount: 100, spread: 70, origin: { y: 0.6 } });
}

function randomInRange(min, max) {
  return Math.random() * (max - min) + min;
}

function fireworks() {
  const duration = 15 * 1000;
  const animationEnd = Date.now() + duration;
  const defaults = { startVelocity: 30, spread: 360, ticks: 60 };

  const interval = setInterval(() => {
    const timeLeft = animationEnd - Date.now();

    if (timeLeft <= 0) {
      return clearInterval(interval);
    }

    const particleCount = 50 * (timeLeft / duration);
    fire({ ...defaults, particleCount, origin: { x: randomInRange(0.1, 0.3), y: Math.random() - 0.2 } });
    fire({ ...defaults, particleCount, origin: { x: randomInRange(0.7, 0.9), y: Math.random() - 0.2 } });
  }, 250);
}

function danceMantis() {
  const mantis = document.getElementById('dancingMantis');
  mantis.classList.add('animate-dance');
  setTimeout(() => mantis.classList.remove('animate-dance'), 1000);
}

setTimeout(() => {
  dialog.showModal();
  sprayConfetti();
  fireworks();
  danceMantis();
}, 1000);

// The dialog fills the viewport, so only a click beside the panel hits it.
dialog.addEventListener('click', (e) => {
  if (e.target === dialog) dialog.close();
});

document.getElementById('moreConfetti').addEventListener('click', () => {
  sprayConfetti();
  danceMantis();
});
