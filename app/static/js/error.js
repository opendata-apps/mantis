// Error pages: the mantis blinks every 5 seconds
const mantis = document.getElementById('mantis');
setInterval(() => mantis.classList.toggle('animate-blink'), 5000);
