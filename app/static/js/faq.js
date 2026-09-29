// FAQ search
document.querySelector('#faq-search').addEventListener('input', (e) => {
  const val = e.target.value.toLowerCase();
  document.querySelectorAll('.faq-item').forEach((item) => {
    item.hidden = !item.dataset.title.includes(val);
  });
});
