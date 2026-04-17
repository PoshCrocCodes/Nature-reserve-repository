/**
 * static/js/main.js
 * Greenfield Local Hub — progressive enhancement JavaScript.
 * All functionality degrades gracefully without JS.
 * No external dependencies required.
 */

'use strict';

/* =========================================================================
   MOBILE NAVIGATION TOGGLE
   ========================================================================= */
(function initMobileNav() {
  const btn = document.getElementById('mobile-menu-btn');
  const menu = document.getElementById('mobile-menu');
  if (!btn || !menu) return;

  btn.addEventListener('click', function () {
    const isOpen = menu.classList.toggle('hidden') === false;
    btn.setAttribute('aria-expanded', String(isOpen));
  });

  // Close on Escape key
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && !menu.classList.contains('hidden')) {
      menu.classList.add('hidden');
      btn.setAttribute('aria-expanded', 'false');
      btn.focus();
    }
  });
})();

/* =========================================================================
   ACCOUNT DROPDOWN TOGGLE
   ========================================================================= */
function toggleDropdown(triggerBtn) {
  const dropdown = document.getElementById('account-dropdown');
  if (!dropdown) return;

  const isOpen = dropdown.classList.toggle('hidden') === false;
  triggerBtn.setAttribute('aria-expanded', String(isOpen));

  // Close when clicking outside
  if (isOpen) {
    function handleOutsideClick(e) {
      if (!triggerBtn.contains(e.target) && !dropdown.contains(e.target)) {
        dropdown.classList.add('hidden');
        triggerBtn.setAttribute('aria-expanded', 'false');
        document.removeEventListener('click', handleOutsideClick);
      }
    }
    // Delay to avoid immediate trigger
    setTimeout(function () {
      document.addEventListener('click', handleOutsideClick);
    }, 0);
  }
}

/* =========================================================================
   AUTO-DISMISS FLASH MESSAGES after 5 seconds
   ========================================================================= */
(function autoDismissMessages() {
  const messages = document.querySelectorAll('[role="alert"] > div');
  messages.forEach(function (msg) {
    setTimeout(function () {
      msg.style.transition = 'opacity 0.4s ease';
      msg.style.opacity = '0';
      setTimeout(function () { msg.remove(); }, 400);
    }, 5000);
  });
})();

/* =========================================================================
   STAR RATING — interactive ★ selector on review forms
   Highlights stars on hover/keyboard for visual feedback.
   ========================================================================= */
(function initStarRatings() {
  document.querySelectorAll('[role="radiogroup"]').forEach(function (group) {
    const labels = group.querySelectorAll('label');

    labels.forEach(function (label, index) {
      const span = label.querySelector('span');
      const input = label.querySelector('input[type="radio"]');
      if (!span || !input) return;

      // Highlight on hover
      label.addEventListener('mouseenter', function () {
        labels.forEach(function (l, i) {
          const s = l.querySelector('span');
          if (s) s.style.color = i <= index ? '#facc15' : '#d1d5db';
        });
      });

      group.addEventListener('mouseleave', function () {
        updateStarsFromChecked(labels);
      });

      // Update on change
      input.addEventListener('change', function () {
        updateStarsFromChecked(labels);
      });
    });

    updateStarsFromChecked(labels);
  });

  function updateStarsFromChecked(labels) {
    let checkedIndex = -1;
    labels.forEach(function (l, i) {
      if (l.querySelector('input:checked')) checkedIndex = i;
    });
    labels.forEach(function (l, i) {
      const s = l.querySelector('span');
      if (s) {
        s.style.color = checkedIndex >= 0 && i <= checkedIndex
          ? '#facc15'
          : '#d1d5db';
      }
    });
  }
})();

/* =========================================================================
   QUANTITY INPUTS — +/- buttons in cart
   (Inline handlers also work; these add keyboard support)
   ========================================================================= */
function decrementQty(btn) {
  const input = btn.nextElementSibling;
  const val = parseInt(input.value, 10);
  if (val > 1) {
    input.value = val - 1;
    input.dispatchEvent(new Event('change'));
  }
}

function incrementQty(btn) {
  const input = btn.previousElementSibling;
  const max = parseInt(input.max, 10) || 9999;
  const val = parseInt(input.value, 10);
  if (val < max) {
    input.value = val + 1;
    input.dispatchEvent(new Event('change'));
  }
}

/* =========================================================================
   MODAL HELPERS — accessible open/close
   ========================================================================= */
(function initModals() {
  // Trap focus inside open modals
  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Tab') return;
    const modal = document.querySelector('[role="dialog"]:not(.hidden)');
    if (!modal) return;

    const focusable = modal.querySelectorAll(
      'a[href], button:not([disabled]), input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    if (!focusable.length) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];

    if (e.shiftKey) {
      if (document.activeElement === first) {
        e.preventDefault();
        last.focus();
      }
    } else {
      if (document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }
  });

  // Close modal with Escape
  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') return;
    const modal = document.querySelector('[role="dialog"]:not(.hidden)');
    if (modal) modal.classList.add('hidden');
  });
})();

/* =========================================================================
   FORM VALIDATION FEEDBACK — inline, WCAG-friendly
   Adds aria-invalid on blur for required empty fields.
   ========================================================================= */
(function initFormValidation() {
  document.querySelectorAll('form[novalidate]').forEach(function (form) {
    form.querySelectorAll('[required]').forEach(function (input) {
      input.addEventListener('blur', function () {
        if (!input.value.trim()) {
          input.setAttribute('aria-invalid', 'true');
          input.classList.add('border-red-400');
        } else {
          input.removeAttribute('aria-invalid');
          input.classList.remove('border-red-400');
        }
      });
    });
  });
})();
