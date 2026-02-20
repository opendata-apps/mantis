// Native <dialog> lightbox — replaces jQuery + Lightbox2
// Supports: albums, captions, keyboard nav, wrap-around, backdrop close

class Lightbox {
  constructor() {
    this.dialog = document.getElementById('lightbox');
    if (!this.dialog) return;

    this.img = this.dialog.querySelector('.lightbox-img');
    this.caption = this.dialog.querySelector('.lightbox-caption');
    this.counter = this.dialog.querySelector('.lightbox-counter');
    this.prevBtn = this.dialog.querySelector('.lightbox-prev');
    this.nextBtn = this.dialog.querySelector('.lightbox-next');
    this.newtabBtn = this.dialog.querySelector('.lightbox-newtab');
    this.album = [];
    this.currentIndex = 0;

    this.bindTriggers();
    this.bindControls();
  }

  bindTriggers() {
    // Event delegation — handles dynamically added images too
    document.addEventListener('click', (e) => {
      const trigger = e.target.closest('a[data-lightbox], a[rel^="lightbox"]');
      if (!trigger) return;
      e.preventDefault();
      this.open(trigger);
    });
  }

  bindControls() {
    // Backdrop click to close
    this.dialog.addEventListener('click', (e) => {
      if (e.target === this.dialog) this.close();
    });

    this.dialog.querySelector('.lightbox-close').addEventListener('click', () => this.close());
    this.dialog.querySelector('.lightbox-newtab')?.addEventListener('click', () => {
      if (this.img.src) window.open(this.img.src, '_blank');
    });
    this.prevBtn.addEventListener('click', () => this.prev());
    this.nextBtn.addEventListener('click', () => this.next());

    // Keyboard navigation
    this.dialog.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowRight') { e.preventDefault(); this.next(); }
      else if (e.key === 'ArrowLeft') { e.preventDefault(); this.prev(); }
    });

    // Swipe support for mobile
    let touchStartX = 0;
    this.dialog.addEventListener('touchstart', (e) => {
      touchStartX = e.changedTouches[0].screenX;
    }, { passive: true });

    this.dialog.addEventListener('touchend', (e) => {
      const diff = e.changedTouches[0].screenX - touchStartX;
      if (Math.abs(diff) > 50) {
        diff > 0 ? this.prev() : this.next();
      }
    }, { passive: true });
  }

  open(trigger) {
    // Build album from group attribute
    const group = trigger.getAttribute('data-lightbox') ||
                  trigger.getAttribute('rel')?.match(/lightbox\[(.+)\]/)?.[1];

    if (group) {
      this.album = [...document.querySelectorAll(
        `a[data-lightbox="${group}"], a[rel="lightbox[${group}]"]`
      )];
    } else {
      this.album = [trigger];
    }

    this.currentIndex = this.album.indexOf(trigger);
    // Compact mode when opened from inside another dialog or a report card
    const compact = !!trigger.closest('dialog, .report-card');
    this.dialog.classList.toggle('lightbox-compact', compact);

    // New-tab button: only in compact/reviewer mode
    if (this.newtabBtn) {
      this.newtabBtn.classList.toggle('hidden', !compact);
      this.newtabBtn.classList.toggle('flex', compact);
    }

    this.show();
    this.dialog.showModal();
  }

  show() {
    const link = this.album[this.currentIndex];
    // Show loading state while image loads
    this.img.style.opacity = '0.3';
    this.img.src = link.href;
    this.img.onload = () => { this.img.style.opacity = '1'; };

    const title = link.getAttribute('data-title') || link.getAttribute('title') || '';
    this.img.alt = title;
    this.caption.textContent = title;

    const hasAlbum = this.album.length > 1;
    this.counter.textContent = hasAlbum ? `Bild ${this.currentIndex + 1} von ${this.album.length}` : '';
    this.prevBtn.hidden = !hasAlbum;
    this.nextBtn.hidden = !hasAlbum;
  }

  next() {
    if (this.album.length <= 1) return;
    this.currentIndex = (this.currentIndex + 1) % this.album.length;
    this.show();
  }

  prev() {
    if (this.album.length <= 1) return;
    this.currentIndex = (this.currentIndex - 1 + this.album.length) % this.album.length;
    this.show();
  }

  close() {
    this.dialog.close();
    this.img.src = '';
  }
}

document.addEventListener('DOMContentLoaded', () => new Lightbox());
