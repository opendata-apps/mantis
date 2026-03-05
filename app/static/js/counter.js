/**
 * Animated counter — counts from 0 to data-target using easeOutExpo.
 * Triggers when the element enters the viewport (IntersectionObserver).
 *
 * Usage: <span class="counter" data-target="1234">0</span>
 *        <script type="module" src="counter.js"></script>
 */
const counter = document.querySelector('.counter');
if (counter) {
  const target = +counter.dataset.target;
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
      counter.innerText = Math.floor(easeOutExpo(progress) * target);
      lastFrame = currentTime;
    }

    if (progress < 1) {
      requestAnimationFrame(animate);
    } else {
      counter.innerText = target;
    }
  }

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
