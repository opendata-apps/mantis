// Lightbox2 for gallery pages - auto-initializes
import jQuery from 'jquery';
window.jQuery = window.$ = jQuery;
import lightbox from 'lightbox2';
import 'lightbox2/dist/css/lightbox.css';
import '../css/gallery.css';

// Auto-initialize lightbox with German labels
document.addEventListener('DOMContentLoaded', () => {
  lightbox.option({
    'resizeDuration': 200,
    'wrapAround': true,
    'albumLabel': 'Bild %1 von %2',
    'fadeDuration': 300,
  });

  // Add hover title to all lightbox images
  const lightboxImages = document.querySelectorAll('a[data-lightbox], a[rel^="lightbox"]');
  lightboxImages.forEach(image => {
    if (!image.getAttribute('title')) {
      image.setAttribute('title', 'Klicken zum Vergrößern');
    }
  });
});
