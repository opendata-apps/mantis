/**
 * Animated counter — counts from 0 to data-target using easeOutExpo once the
 * element enters the viewport. The server renders the final number, so it
 * stays correct without JS and under reduced motion.
 *
 * Usage: <span class="counter" data-target="1234">1.234</span>
 */
const counter = document.querySelector('.counter');
if (counter && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
  const target = +counter.dataset.target;
  const format = new Intl.NumberFormat('de-DE').format;
  const duration = 2000;
  let startTime = null;
  let lastFrame = 0;
  const minInterval = 1000 / 30;

  function easeOutExpo(t) {
    return t === 1 ? 1 : 1 - Math.pow(2, -10 * t);
  }

  function animate(currentTime) {
    if (!startTime) startTime = currentTime;
    const progress = Math.min((currentTime - startTime) / duration, 1);

    if (currentTime - lastFrame >= minInterval) {
      counter.textContent = format(Math.floor(easeOutExpo(progress) * target));
      lastFrame = currentTime;
    }

    if (progress < 1) {
      requestAnimationFrame(animate);
    } else {
      counter.textContent = format(target);
    }
  }

  counter.textContent = format(0);
  const observer = new IntersectionObserver(
    entries => {
      if (entries[0].isIntersecting) {
        requestAnimationFrame(animate);
        observer.disconnect();
      }
    },
    { threshold: 0.1 }
  );
  observer.observe(counter);
}
