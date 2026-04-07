// ============================================
// MIKAEL CHEW - Main JavaScript
// ============================================

document.addEventListener('DOMContentLoaded', () => {

  // ============================
  // THEME TOGGLE (Dark / Light)
  // ============================
  const themeBtn = document.querySelector('.theme-btn');
  const savedTheme = localStorage.getItem('mc-theme') || 'dark';

  function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('mc-theme', theme);
    if (themeBtn) {
      themeBtn.innerHTML = theme === 'dark'
        ? '<i class="fas fa-sun"></i>'
        : '<i class="fas fa-moon"></i>';
      themeBtn.setAttribute('aria-label', theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode');
    }
  }

  setTheme(savedTheme);

  if (themeBtn) {
    themeBtn.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-theme') || 'dark';
      setTheme(current === 'dark' ? 'light' : 'dark');
    });
  }

  // ============================
  // LANGUAGE TOGGLE (EN / 中文)
  // ============================
  const langBtn = document.querySelector('.lang-btn');
  const savedLang = localStorage.getItem('mc-lang') || 'en';

  function setLang(lang) {
    document.documentElement.setAttribute('lang', lang === 'zh' ? 'zh-Hant' : 'en');
    localStorage.setItem('mc-lang', lang);

    // Update button text
    if (langBtn) {
      langBtn.textContent = lang === 'en' ? '中文' : 'EN';
      langBtn.setAttribute('aria-label', lang === 'en' ? 'Switch to Chinese' : 'Switch to English');
    }

    // Swap all translatable elements
    document.querySelectorAll('[data-en]').forEach(el => {
      const text = lang === 'en' ? el.getAttribute('data-en') : el.getAttribute('data-zh');
      if (text) {
        if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
          el.placeholder = text;
        } else if (el.tagName === 'OPTION') {
          el.textContent = text;
        } else {
          el.innerHTML = text;
        }
      }
    });

    // Swap alt text on images
    document.querySelectorAll('[data-alt-en]').forEach(el => {
      el.alt = lang === 'en' ? el.getAttribute('data-alt-en') : el.getAttribute('data-alt-zh');
    });
  }

  setLang(savedLang);

  if (langBtn) {
    langBtn.addEventListener('click', () => {
      const current = localStorage.getItem('mc-lang') || 'en';
      setLang(current === 'en' ? 'zh' : 'en');
    });
  }

  // ============================
  // NAVBAR SCROLL BEHAVIOR
  // ============================
  const navbar = document.querySelector('.navbar');
  const isHomePage = navbar && navbar.classList.contains('transparent');

  function handleNavScroll() {
    if (!navbar) return;
    if (isHomePage) {
      if (window.scrollY > 80) {
        navbar.classList.add('scrolled');
        navbar.classList.remove('transparent');
      } else {
        navbar.classList.remove('scrolled');
        navbar.classList.add('transparent');
      }
    } else {
      navbar.classList.add('scrolled');
    }
  }

  handleNavScroll();
  window.addEventListener('scroll', handleNavScroll, { passive: true });

  // ============================
  // MOBILE NAV TOGGLE
  // ============================
  const navToggle = document.querySelector('.nav-toggle');
  const navLinks = document.querySelector('.nav-links');

  if (navToggle && navLinks) {
    navToggle.addEventListener('click', () => {
      navToggle.classList.toggle('open');
      navLinks.classList.toggle('open');
    });

    navLinks.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', () => {
        navToggle.classList.remove('open');
        navLinks.classList.remove('open');
      });
    });
  }

  // ============================
  // SCROLL FADE-IN ANIMATIONS
  // ============================
  const fadeElements = document.querySelectorAll('.fade-in');

  if (fadeElements.length > 0) {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible');
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.1, rootMargin: '0px 0px -50px 0px' }
    );

    fadeElements.forEach(el => observer.observe(el));
  }

  // ============================
  // ACTIVE NAV LINK
  // ============================
  const currentPath = window.location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.nav-links a').forEach(link => {
    const href = link.getAttribute('href').split('/').pop();
    if (href === currentPath) {
      link.classList.add('active');
    }
  });

  // ============================
  // CONTACT FORM (basic)
  // ============================
  // Contact form submits natively to Formspree (action + method on <form>).
  // No JS interception needed — Formspree handles the submission and redirect.
});
