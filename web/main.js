// Smooth scroll for anchor links
const links = document.querySelectorAll('a[href^="#"]');
for (const link of links) {
    link.addEventListener('click', function(e) {
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            e.preventDefault();
            target.scrollIntoView({ behavior: 'smooth' });
        }
    });
}
console.log('Welcome to PainPain! Inspired by Apple.');

// Countdown Timer
const countdownEl = document.getElementById('countdown');
if (countdownEl) {
  let seconds = 10;
  countdownEl.textContent = `Demo download available in ${seconds} seconds...`;
  const interval = setInterval(() => {
    seconds--;
    if (seconds > 0) {
      countdownEl.textContent = `Demo download available in ${seconds} seconds...`;
    } else {
      countdownEl.textContent = 'Download is now available!';
      clearInterval(interval);
    }
  }, 1000);
}

// Modal logic
const disclaimerModal = document.getElementById('disclaimerModal');
const openDisclaimer = document.getElementById('openDisclaimer');
const closeDisclaimer = document.getElementById('closeDisclaimer');
const closeDisclaimer2 = document.getElementById('closeDisclaimer2');

function openModal() {
  disclaimerModal.classList.remove('hidden');
  disclaimerModal.setAttribute('aria-modal', 'true');
  disclaimerModal.setAttribute('role', 'dialog');
  document.body.style.overflow = 'hidden';
}
function closeModal() {
  disclaimerModal.classList.add('hidden');
  disclaimerModal.removeAttribute('aria-modal');
  disclaimerModal.removeAttribute('role');
  document.body.style.overflow = '';
}
if (openDisclaimer) openDisclaimer.onclick = openModal;
if (closeDisclaimer) closeDisclaimer.onclick = closeModal;
if (closeDisclaimer2) closeDisclaimer2.onclick = closeModal;
disclaimerModal && disclaimerModal.addEventListener('click', (e) => {
  if (e.target === disclaimerModal) closeModal();
});
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && !disclaimerModal.classList.contains('hidden')) closeModal();
});

// Fade-in animation for sections
const fadeEls = document.querySelectorAll('.fade-in');
const observer = new window.IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('opacity-100', 'translate-y-0');
        entry.target.classList.remove('opacity-0', 'translate-y-8');
      }
    });
  },
  { threshold: 0.15 }
);
fadeEls.forEach((el) => {
  el.classList.add('opacity-0', 'translate-y-8', 'transition-all', 'duration-1000');
  observer.observe(el);
}); 