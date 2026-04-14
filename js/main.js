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
  // CONTACT FORM (AJAX via Formspree)
  // ============================
  const contactForm = document.querySelector('.contact-form');
  if (contactForm) {
    contactForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const lang = localStorage.getItem('mc-lang') || 'en';
      const btn = contactForm.querySelector('button[type="submit"]');
      const origText = btn.textContent;
      btn.disabled = true;
      btn.textContent = lang === 'en' ? 'Sending...' : '發送中...';

      const data = new FormData(contactForm);

      fetch('https://formspree.io/f/xreojdqa', {
        method: 'POST',
        body: data,
        headers: { 'Accept': 'application/json' }
      }).then(function(response) {
        if (response.ok) {
          contactForm.innerHTML = '<div class="form-success">'
            + '<i class="fas fa-check-circle"></i>'
            + '<h3>' + (lang === 'en' ? 'Message Sent' : '訊息已發送') + '</h3>'
            + '<p>' + (lang === 'en'
              ? 'Thank you for reaching out. I will get back to you soon.'
              : '感謝您的來信。我會盡快回覆您。') + '</p>'
            + '<a href="index.html" class="btn btn-primary">' + (lang === 'en' ? 'Back to Home' : '返回首頁') + '</a>'
            + '</div>';
        } else {
          alert(lang === 'en'
            ? 'Something went wrong. Please try again or email me directly.'
            : '出了點問題。請重試或直接發送電子郵件給我。');
          btn.disabled = false;
          btn.textContent = origText;
        }
      }).catch(function() {
        alert(lang === 'en'
          ? 'Something went wrong. Please try again or email me directly.'
          : '出了點問題。請重試或直接發送電子郵件給我。');
        btn.disabled = false;
        btn.textContent = origText;
      });
    });
  }

  // ============================
  // SCROLL TO TOP BUTTON
  // ============================
  // Create button if not already in HTML
  var scrollBtn = document.querySelector('.scroll-top');
  if (!scrollBtn) {
    scrollBtn = document.createElement('button');
    scrollBtn.className = 'scroll-top';
    scrollBtn.setAttribute('aria-label', 'Scroll to top');
    scrollBtn.innerHTML = '<i class="fas fa-arrow-up"></i>';
    // Insert before site-toggles so they don't overlap
    var toggles = document.querySelector('.site-toggles');
    if (toggles) {
      toggles.parentNode.insertBefore(scrollBtn, toggles);
    } else {
      document.body.appendChild(scrollBtn);
    }
  }

  function checkScroll() {
    if (window.scrollY > 300) {
      scrollBtn.classList.add('visible');
    } else {
      scrollBtn.classList.remove('visible');
    }
  }

  window.addEventListener('scroll', checkScroll);
  checkScroll(); // Check on page load in case already scrolled

  scrollBtn.addEventListener('click', function() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

  // ============================
  // BLOG CATEGORY FILTER
  // ============================
  const filterBtns = document.querySelectorAll('.blog-filter');
  const blogCards = document.querySelectorAll('.blog-card');
  const showMoreWrap = document.getElementById('blog-show-more');

  function applyShowMore() {
    if (!showMoreWrap) return;
    var visibleCards = Array.from(blogCards).filter(function(c) { return c.style.display !== 'none'; });
    var hiddenCount = 0;
    visibleCards.forEach(function(card, i) {
      if (i >= 6) { card.classList.add('blog-card-hidden'); hiddenCount++; }
    });
    showMoreWrap.style.display = hiddenCount > 0 ? '' : 'none';
  }

  if (filterBtns.length && blogCards.length) {
    applyShowMore();

    filterBtns.forEach(function(btn) {
      btn.addEventListener('click', function() {
        filterBtns.forEach(function(b) { b.classList.remove('active'); });
        btn.classList.add('active');
        var filter = btn.dataset.filter;

        blogCards.forEach(function(card) {
          card.classList.remove('blog-card-hidden');
          card.style.display = (filter === 'all' || card.dataset.category === filter) ? '' : 'none';
        });

        if (filter === 'all') { applyShowMore(); }
        else if (showMoreWrap) { showMoreWrap.style.display = 'none'; }
      });
    });
  }

  if (showMoreWrap) {
    var showMoreBtn = showMoreWrap.querySelector('button');
    if (showMoreBtn) {
      showMoreBtn.addEventListener('click', function() {
        document.querySelectorAll('.blog-card.blog-card-hidden').forEach(function(c) { c.classList.remove('blog-card-hidden'); });
        showMoreWrap.style.display = 'none';
      });
    }
  }

});
