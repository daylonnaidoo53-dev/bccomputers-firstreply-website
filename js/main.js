/**
 * BCComputers First-Reply Website — Main UI Script
 * Handles mobile nav, FAQ accordions, smooth scrolling, pricing tier selection, and sticky mobile action bar.
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Mobile Menu Toggle
  const navToggle = document.getElementById('nav-toggle');
  const navMenu = document.getElementById('nav-menu');

  if (navToggle && navMenu) {
    navToggle.addEventListener('click', () => {
      const isExpanded = navToggle.getAttribute('aria-expanded') === 'true';
      navToggle.setAttribute('aria-expanded', !isExpanded);
      navMenu.classList.toggle('is-open');
    });

    // Close menu when clicking outside or clicking any nav link
    navMenu.querySelectorAll('a').forEach((link) => {
      link.addEventListener('click', () => {
        navToggle.setAttribute('aria-expanded', 'false');
        navMenu.classList.remove('is-open');
      });
    });
  }

  // 2. FAQ Accordion (Accessible with ARIA)
  const faqItems = document.querySelectorAll('.faq-item');
  faqItems.forEach((item) => {
    const button = item.querySelector('.faq-question');
    const answer = item.querySelector('.faq-answer');

    if (!button || !answer) return;

    button.addEventListener('click', () => {
      const isExpanded = button.getAttribute('aria-expanded') === 'true';

      // Optionally close other open items for cleaner mobile browsing
      faqItems.forEach((otherItem) => {
        if (otherItem !== item) {
          const otherBtn = otherItem.querySelector('.faq-question');
          const otherAns = otherItem.querySelector('.faq-answer');
          if (otherBtn && otherAns) {
            otherBtn.setAttribute('aria-expanded', 'false');
            otherAns.hidden = true;
            otherItem.classList.remove('active');
          }
        }
      });

      // Toggle current
      button.setAttribute('aria-expanded', String(!isExpanded));
      answer.hidden = isExpanded;
      item.classList.toggle('active', !isExpanded);
    });
  });

  // 3. Pricing Tier Selection Buttons -> Scroll to Form & Pre-select
  const tierSelectButtons = document.querySelectorAll('[data-select-tier]');
  tierSelectButtons.forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const targetTier = btn.getAttribute('data-select-tier');
      const radio = document.querySelector(`input[name="tier"][value="${targetTier}"]`);
      if (radio) {
        radio.checked = true;
        // Trigger change event if needed
        radio.dispatchEvent(new Event('change', { bubbles: true }));
      }

      const formSection = document.getElementById('quote-form-section');
      if (formSection) {
        formSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        // Highlight form briefly
        formSection.classList.add('flash-highlight');
        setTimeout(() => formSection.classList.remove('flash-highlight'), 1200);
      }
    });
  });

  // 4. Smooth Anchor Scrolling with header offset
  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener('click', function (e) {
      const targetId = this.getAttribute('href');
      if (targetId === '#' || !targetId.startsWith('#')) return;

      const targetEl = document.querySelector(targetId);
      if (targetEl) {
        e.preventDefault();
        const headerHeight = document.querySelector('.site-header')?.offsetHeight || 70;
        const targetPos = targetEl.getBoundingClientRect().top + window.pageYOffset - headerHeight - 16;

        window.scrollTo({
          top: targetPos,
          behavior: 'smooth'
        });
      }
    });
  });

  // 5. Mobile Sticky Quick-Action Bar
  const stickyBar = document.getElementById('mobile-sticky-bar');
  const heroSection = document.getElementById('hero');

  if (stickyBar && heroSection) {
    const handleScroll = () => {
      const heroBottom = heroSection.getBoundingClientRect().bottom;
      // Show sticky bar once hero has scrolled out of view
      if (heroBottom < 100) {
        stickyBar.classList.add('visible');
      } else {
        stickyBar.classList.remove('visible');
      }
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    handleScroll();
  }
});
