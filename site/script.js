/* ==========================================================================
   Site Scripts (vanilla JS, no dependencies)
   Modules:
     01. Mobile Navigation
     02. Services Dropdown
     03. FAQ Accordion
     04. Scroll To Top
     05. Contact Form Validation + Success Message
     06. Smooth Scroll Fallback
     07. Footer Year
   ========================================================================== */
(function () {
  'use strict';

  /* ------------------------------------------------------------------
     01. MOBILE NAVIGATION
     Toggles the off-canvas nav panel and keeps ARIA state in sync.
     ------------------------------------------------------------------ */
  function initMobileNav() {
    var burger = document.querySelector('.nav-burger');
    var nav = document.getElementById('primary-nav');
    if (!burger || !nav) return;

    function setOpen(open) {
      burger.setAttribute('aria-expanded', String(open));
      nav.classList.toggle('is-open', open);
    }

    burger.addEventListener('click', function () {
      setOpen(burger.getAttribute('aria-expanded') !== 'true');
    });

    // Close on Escape and return focus to the toggle
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && burger.getAttribute('aria-expanded') === 'true') {
        setOpen(false);
        burger.focus();
      }
    });

    // Close when a nav link is followed
    nav.addEventListener('click', function (e) {
      if (e.target.closest('a')) setOpen(false);
    });

    // Reset state when resizing back to desktop
    window.addEventListener('resize', function () {
      if (window.innerWidth > 900) setOpen(false);
    });
  }

  /* ------------------------------------------------------------------
     02. SERVICES DROPDOWN
     Click/keyboard accessible submenu (no hover-only interaction).
     ------------------------------------------------------------------ */
  function initDropdown() {
    var toggles = document.querySelectorAll('.nav__toggle');
    if (!toggles.length) return;

    Array.prototype.forEach.call(toggles, function (toggle) {
      var menu = document.getElementById(toggle.getAttribute('aria-controls'));
      if (!menu) return;

      toggle.addEventListener('click', function (e) {
        e.preventDefault();
        var open = toggle.getAttribute('aria-expanded') === 'true';
        toggle.setAttribute('aria-expanded', String(!open));
        menu.classList.toggle('is-open', !open);
      });

      // Close on outside click (desktop only behaviour)
      document.addEventListener('click', function (e) {
        if (window.innerWidth <= 900) return;
        if (!toggle.parentNode.contains(e.target)) {
          toggle.setAttribute('aria-expanded', 'false');
          menu.classList.remove('is-open');
        }
      });

      // Close on Escape
      toggle.parentNode.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
          toggle.setAttribute('aria-expanded', 'false');
          menu.classList.remove('is-open');
          toggle.focus();
        }
      });
    });
  }

  /* ------------------------------------------------------------------
     03. FAQ ACCORDION
     Buttons control panels via aria-expanded / aria-controls.
     ------------------------------------------------------------------ */
  function initAccordion() {
    var triggers = document.querySelectorAll('.faq__trigger');
    if (!triggers.length) return;

    Array.prototype.forEach.call(triggers, function (trigger) {
      var panel = document.getElementById(trigger.getAttribute('aria-controls'));
      if (!panel) return;

      trigger.addEventListener('click', function () {
        var open = trigger.getAttribute('aria-expanded') === 'true';
        trigger.setAttribute('aria-expanded', String(!open));
        panel.classList.toggle('is-open', !open);
        var item = trigger.closest('.faq__item');
        if (item) item.classList.toggle('is-open', !open);
      });
    });
  }

  /* ------------------------------------------------------------------
     04. SCROLL TO TOP BUTTON
     Shown after 400px of scroll; passive listener for performance.
     ------------------------------------------------------------------ */
  function initToTop() {
    var btn = document.querySelector('.to-top');
    if (!btn) return;
    var ticking = false;

    function update() {
      btn.classList.toggle('is-visible', window.pageYOffset > 400);
      ticking = false;
    }

    window.addEventListener('scroll', function () {
      if (!ticking) {
        window.requestAnimationFrame(update);
        ticking = true;
      }
    }, { passive: true });

    btn.addEventListener('click', function () {
      var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      window.scrollTo({ top: 0, behavior: reduce ? 'auto' : 'smooth' });
    });

    update();
  }

  /* ------------------------------------------------------------------
     05. CONTACT FORM
     Client-side required-field validation, inline errors, success state.
     Backend integration placeholder: replace submitLead() below.
     ------------------------------------------------------------------ */
  var EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
  var PHONE_RE = /^[0-9+()\-.\s]{10,}$/;

  function fieldError(input, message) {
    var wrap = input.closest('.field');
    var slot = wrap ? wrap.querySelector('.field__error') : null;
    if (message) {
      input.setAttribute('aria-invalid', 'true');
      if (slot) slot.textContent = message;
    } else {
      input.removeAttribute('aria-invalid');
      if (slot) slot.textContent = '';
    }
  }

  function validateField(input) {
    var value = (input.value || '').trim();
    var label = input.getAttribute('data-label') || 'This field';

    if (input.hasAttribute('required') && !value) {
      fieldError(input, label + ' is required.');
      return false;
    }
    if (input.type === 'email' && value && !EMAIL_RE.test(value)) {
      fieldError(input, 'Enter a valid email address.');
      return false;
    }
    if (input.type === 'tel' && value && !PHONE_RE.test(value)) {
      fieldError(input, 'Enter a valid phone number.');
      return false;
    }
    fieldError(input, '');
    return true;
  }

  /* ==================================================================
     FORM DELIVERY — PASTE YOUR APPS SCRIPT URL HERE
     ------------------------------------------------------------------
     Leads are posted straight from the browser to a Google Apps Script
     web app, which writes each one as a row in your Google Sheet and
     (optionally) emails you. No server, no third-party form service.

     Setup is in README.md under "Deliver leads to a Google Sheet".
     The short version: create a Sheet, paste google-apps-script.gs into
     Extensions -> Apps Script, deploy it as a Web app with access set to
     "Anyone", then paste the /exec URL below.

     Until a real URL is set, forms still validate and show the success
     message but nothing is delivered — which is what you want while
     previewing locally.
     ================================================================== */
  // Set this to the /exec URL of THIS site's Apps Script deployment.
  // It was carried over from Windsor when this folder was copied - leaving it
  // would have posted every Grimsby lead into the Windsor spreadsheet.
  // Rerun build.py after changing it so the cache fingerprint updates.
  var SHEET_ENDPOINT = 'YOUR-APPS-SCRIPT-EXEC-URL';

  /* Fallback for CORS trouble. Leave false. If submissions are reaching
     the sheet but the page still shows an error, set this to true: the
     request is then sent "fire and forget" and always reports success.
     You lose error detection, so only use it if you need it. */
  var SHEET_USE_NO_CORS = false;

  function endpointIsSet() {
    return SHEET_ENDPOINT && SHEET_ENDPOINT.indexOf('YOUR-') !== 0;
  }

  /**
   * Sends one lead. Returns a Promise that resolves on success and
   * rejects on failure, so the form can show the right message.
   */
  function submitLead(data) {
    if (!endpointIsSet()) {
      if (window.console && console.warn) {
        console.warn('[site] No endpoint set — lead NOT delivered. ' +
                     'Set SHEET_ENDPOINT in script.js.', data);
      }
      return Promise.resolve();          // preview mode
    }

    /* Content-Type is deliberately text/plain. That keeps this a "simple"
       cross-origin request, so the browser skips the CORS preflight —
       Apps Script does not answer OPTIONS requests. The Apps Script side
       parses the body as JSON regardless. */
    var options = {
      method: 'POST',
      headers: { 'Content-Type': 'text/plain;charset=utf-8' },
      body: JSON.stringify(data),
      redirect: 'follow'
    };

    if (SHEET_USE_NO_CORS) {
      options.mode = 'no-cors';
      return fetch(SHEET_ENDPOINT, options);   // opaque response, assume sent
    }

    return fetch(SHEET_ENDPOINT, options)
      .then(function (res) { return res.json(); })
      .then(function (json) {
        if (!json.success) throw new Error(json.message || 'Submission was rejected');
      });
  }

  function initForms() {
    var forms = document.querySelectorAll('.lead-form');
    if (!forms.length) return;

    Array.prototype.forEach.call(forms, function (form) {
      var fields = form.querySelectorAll('input, select, textarea');
      var success = form.parentNode.querySelector('.form-success');

      // Validate on blur, clear errors as the user corrects them
      Array.prototype.forEach.call(fields, function (input) {
        input.addEventListener('blur', function () { validateField(input); });
        input.addEventListener('input', function () {
          if (input.getAttribute('aria-invalid') === 'true') validateField(input);
        });
      });

      form.addEventListener('submit', function (e) {
        e.preventDefault();

        var valid = true;
        var firstBad = null;
        Array.prototype.forEach.call(fields, function (input) {
          if (!validateField(input)) {
            valid = false;
            if (!firstBad) firstBad = input;
          }
        });

        if (!valid) {
          if (success) success.classList.remove('is-visible');
          if (firstBad) firstBad.focus();
          return;
        }

        // Honeypot: a hidden field that only automated scripts fill in.
        // If it has a value, show the normal success state and discard.
        var honey = form.querySelector('[name="botcheck"]');
        if (honey && honey.value) {
          form.reset();
          if (success) success.classList.add('is-visible');
          return;
        }

        var data = {};
        Array.prototype.forEach.call(fields, function (input) {
          if (input.name && input.name !== 'botcheck') data[input.name] = input.value.trim();
        });
        // Which form on which page produced this lead
        data.source = form.getAttribute('data-source') || document.title;
        data.pageUrl = window.location.href;

        var button = form.querySelector('button[type="submit"]');
        var originalText = button ? button.textContent : '';
        if (button) { button.disabled = true; button.textContent = 'Sending…'; }

        submitLead(data)
          .then(function () {
            form.reset();
            if (success) {
              success.classList.add('is-visible');
              success.setAttribute('tabindex', '-1');
              success.focus();
            }
          })
          .catch(function () {
            if (success) {
              // Pull this site's number out of the page rather than hardcoding
              // it. A literal number here shipped the wrong city's phone to
              // every site built from this template.
              var telLink = document.querySelector('a[href^="tel:"]');
              var telHref = telLink ? telLink.getAttribute('href') : '';
              var telText = telLink ? telLink.textContent.trim() : '';
              success.classList.add('is-visible');
              success.innerHTML = '<div><strong>Something went wrong.</strong> ' +
                (telHref
                  ? 'Please call us at <a href="' + telHref + '">' + telText + '</a> and we will take your details by phone.'
                  : 'Please call us and we will take your details by phone.') +
                '</div>';
            }
          })
          .then(function () {
            if (button) { button.disabled = false; button.textContent = originalText; }
          });
      });
    });
  }

  /* ------------------------------------------------------------------
     05b. PROJECT GALLERY LIGHTBOX
     Opens the larger image on demand. Fully keyboard operable:
       Escape        close
       Left / Right  previous / next photo
       Tab           cycles within the dialog only (focus trap)
     Returns focus to the thumbnail that opened it.
     ------------------------------------------------------------------ */
  function initLightbox() {
    var box = document.getElementById('lightbox');
    var triggers = document.querySelectorAll('.gallery__btn');
    if (!box || !triggers.length) return;

    var img = box.querySelector('.lightbox__img');
    var caption = box.querySelector('.lightbox__caption');
    var closeBtn = box.querySelector('[data-lb-close]');
    var prevBtn = box.querySelector('[data-lb-prev]');
    var nextBtn = box.querySelector('[data-lb-next]');
    var items = Array.prototype.slice.call(triggers);
    var index = 0;
    var lastFocused = null;

    // WebP is near-universal, but fall back to the JPG if it fails to decode
    img.addEventListener('error', function () {
      var fb = items[index].getAttribute('data-large-fallback');
      if (fb && img.getAttribute('src') !== fb) img.setAttribute('src', fb);
    });

    function show(i) {
      index = (i + items.length) % items.length;
      var btn = items[index];
      img.setAttribute('src', btn.getAttribute('data-large'));
      img.setAttribute('alt', btn.getAttribute('data-caption') || '');
      caption.textContent = (index + 1) + ' of ' + items.length + ' — ' +
                            (btn.getAttribute('data-caption') || '');
    }

    function open(i) {
      lastFocused = document.activeElement;
      show(i);
      box.hidden = false;
      document.body.style.overflow = 'hidden';   // stop background scroll
      closeBtn.focus();
    }

    function close() {
      box.hidden = true;
      document.body.style.overflow = '';
      img.setAttribute('src', '');
      if (lastFocused) lastFocused.focus();
    }

    items.forEach(function (btn, i) {
      btn.addEventListener('click', function () { open(i); });
    });

    closeBtn.addEventListener('click', close);
    prevBtn.addEventListener('click', function () { show(index - 1); });
    nextBtn.addEventListener('click', function () { show(index + 1); });

    // Click the backdrop (but not the image or controls) to dismiss
    box.addEventListener('click', function (e) {
      if (e.target === box) close();
    });

    document.addEventListener('keydown', function (e) {
      if (box.hidden) return;
      if (e.key === 'Escape') { e.preventDefault(); close(); }
      else if (e.key === 'ArrowLeft') { e.preventDefault(); show(index - 1); }
      else if (e.key === 'ArrowRight') { e.preventDefault(); show(index + 1); }
      else if (e.key === 'Tab') {
        // Trap focus inside the dialog
        var focusable = [prevBtn, nextBtn, closeBtn];
        var pos = focusable.indexOf(document.activeElement);
        e.preventDefault();
        var next = e.shiftKey ? pos - 1 : pos + 1;
        if (next < 0) next = focusable.length - 1;
        if (next >= focusable.length) next = 0;
        focusable[next].focus();
      }
    });
  }

  /* ------------------------------------------------------------------
     06. SMOOTH SCROLL FALLBACK
     For browsers without CSS scroll-behavior support.
     ------------------------------------------------------------------ */
  function initSmoothScroll() {
    if ('scrollBehavior' in document.documentElement.style) return;

    document.addEventListener('click', function (e) {
      var link = e.target.closest('a[href^="#"]');
      if (!link) return;
      var id = link.getAttribute('href');
      if (id === '#' || id.length < 2) return;
      var target = document.querySelector(id);
      if (!target) return;
      e.preventDefault();
      window.scrollTo(0, target.getBoundingClientRect().top + window.pageYOffset - 90);
      target.setAttribute('tabindex', '-1');
      target.focus();
    });
  }

  /* ------------------------------------------------------------------
     07. FOOTER YEAR
     ------------------------------------------------------------------ */
  function initYear() {
    var el = document.querySelector('[data-year]');
    if (el) el.textContent = new Date().getFullYear();
  }

  /* ------------------------------------------------------------------
     BOOTSTRAP
     ------------------------------------------------------------------ */
  function init() {
    initMobileNav();
    initDropdown();
    initAccordion();
    initToTop();
    initForms();
    initLightbox();
    initSmoothScroll();
    initYear();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
