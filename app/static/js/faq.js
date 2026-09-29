// FAQ accordion and search
document.querySelectorAll('.faq-item').forEach((item) => {
  const button = item.querySelector('button');
  const content = item.querySelector('div[id^="faq"]');

  button.addEventListener('click', () => {
    const expanded = button.getAttribute('aria-expanded') === 'true';
    button.setAttribute('aria-expanded', !expanded);

    content.style.maxHeight = expanded ? '0px' : content.scrollHeight + 'px';
  });
});

document.querySelector('#faq-search').addEventListener('input', (e) => {
  const val = e.target.value.toLowerCase();
  document.querySelectorAll('.faq-item').forEach((item) => {
    item.hidden = !item.dataset.title.includes(val);
  });
});
