'use strict';

(function (root) {
  var SUCCESS = "Request received. We'll reply within one business day with best-fit options, current status, and the correct purchase path.";
  var FAILURE = 'We could not send your request right now. Please try again shortly. If the issue continues, use the support contact listed below.';
  var VALIDATION = 'Please complete the required fields with a valid email.';
  var DISABLED = 'Online intake is not connected yet, so this form cannot pretend to send. Email Hello@preparationstation.org with the same details. Do not include records, health data, payment details, or program credentials.';
  var VERIFY = 'Please complete the verification step, then send the request again.';
  var FORM_ID_RE = /^[A-Za-z0-9]{6,32}$/;

  function isFormId(value) {
    if (typeof value !== 'string') return false;
    var trimmed = value.trim();
    if (!trimmed || trimmed.indexOf('[') !== -1) return false;
    return FORM_ID_RE.test(trimmed);
  }

  function isSitekey(value) {
    if (typeof value !== 'string') return false;
    var trimmed = value.trim();
    return trimmed.length >= 8 && !/secret/i.test(trimmed) && trimmed.indexOf('[') === -1;
  }

  function publicValues(config) {
    config = config || {};
    return {
      pathway: config.PATHWAY_RECOMMENDATION_FORMSPREE_ID || config.pathway_form_id || '',
      quote: config.SCHOOL_DISTRICT_QUOTE_FORMSPREE_ID || config.quote_form_id || '',
      sitekey: config.TURNSTILE_SITE_KEY || config.turnstile_sitekey || ''
    };
  }

  function isReady(config) {
    var values = publicValues(config);
    return Boolean(
      config &&
        config.enabled === true &&
        isFormId(values.pathway) &&
        isFormId(values.quote) &&
        isSitekey(values.sitekey)
    );
  }

  function endpoint(formId) {
    if (!isFormId(formId)) return '';
    return 'https://formspree.io/f/' + formId.trim();
  }

  function show(el, text) {
    if (!el) return;
    el.hidden = false;
    el.style.display = 'block';
    el.textContent = text;
  }

  function hide(el) {
    if (!el) return;
    el.hidden = true;
    el.style.display = 'none';
    el.textContent = '';
  }

  function tokenFrom(form) {
    var hidden = form.querySelector('[name="cf-turnstile-response"]');
    if (hidden && hidden.value) return hidden.value;
    var widgetId = form.getAttribute('data-turnstile-widget-id');
    if (root.turnstile && widgetId) return root.turnstile.getResponse(widgetId) || '';
    return '';
  }

  function resetTurnstile(form) {
    var widgetId = form.getAttribute('data-turnstile-widget-id');
    if (root.turnstile && widgetId) root.turnstile.reset(widgetId);
  }

  function renderTurnstile(form) {
    var slot = form.querySelector('[data-turnstile-slot]');
    var sitekey = form.getAttribute('data-turnstile-sitekey') || '';
    if (!slot || !sitekey || !root.turnstile) return;
    var id = root.turnstile.render(slot, {
      sitekey: sitekey,
      action: form.getAttribute('data-intake-source') || 'contact',
      theme: 'light'
    });
    form.setAttribute('data-turnstile-widget-id', id);
  }

  function setBusy(form, busy) {
    var button = form.querySelector('[type="submit"]');
    form.setAttribute('aria-busy', busy ? 'true' : 'false');
    if (button) {
      button.disabled = busy;
      if (busy) button.setAttribute('data-original-label', button.textContent);
      else if (button.getAttribute('data-original-label')) {
        button.textContent = button.getAttribute('data-original-label');
      }
      if (busy) button.textContent = 'Sending…';
    }
  }

  function bindForm(form) {
    if (!form || form.getAttribute('data-formspree-bound') === 'true') return;
    form.setAttribute('data-formspree-bound', 'true');
    var ok = form.querySelector('[data-form-ok]');
    var err = form.querySelector('[data-form-error]');
    var params = new URLSearchParams(root.location ? root.location.search : '');
    try {
      var sku = params.get('sku');
      var skuField = form.elements.sku;
      if (sku && skuField && !skuField.value) skuField.value = sku;
      var body = params.get('body');
      if (body && form.elements.message && !form.elements.message.value) form.elements.message.value = body;
    } catch (e) {}

    form.addEventListener('submit', function (ev) {
      ev.preventDefault();
      hide(ok);
      hide(err);
      if (!form.checkValidity()) {
        form.reportValidity();
        show(err, VALIDATION);
        return;
      }
      var ready = form.getAttribute('data-formspree-ready') === 'true';
      var action = form.getAttribute('action') || '';
      if (!ready || !action || action.indexOf('https://formspree.io/f/') !== 0) {
        show(err, DISABLED);
        return;
      }
      if (form.getAttribute('aria-busy') === 'true') return;
      if ((form.getAttribute('data-turnstile-sitekey') || '') && !tokenFrom(form)) {
        show(err, VERIFY);
        return;
      }
      setBusy(form, true);
      var payload = new FormData(form);
      fetch(action, {
        method: 'POST',
        headers: { Accept: 'application/json' },
        body: payload,
        credentials: 'omit'
      }).then(function (res) {
        if (res.ok) {
          show(ok, SUCCESS);
          form.reset();
          return;
        }
        if (res.status >= 400 && res.status < 500) {
          show(err, VALIDATION);
          return;
        }
        show(err, FAILURE);
      }).catch(function () {
        show(err, FAILURE);
      }).then(function () {
        setBusy(form, false);
        resetTurnstile(form);
      });
    });
  }

  function start() {
    var forms = root.document ? root.document.querySelectorAll('form[data-formspree-ready]') : [];
    forms.forEach(function (form) {
      bindForm(form);
      if (form.getAttribute('data-formspree-ready') === 'true' && form.getAttribute('data-turnstile-sitekey')) {
        renderTurnstile(form);
      }
    });
  }

  function boot() {
    if (!root.document) return;
    var needsTurnstile = root.document.querySelector('form[data-formspree-ready="true"][data-turnstile-sitekey]:not([data-turnstile-sitekey=""])');
    if (needsTurnstile && !root.turnstile) {
      var script = root.document.createElement('script');
      script.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit';
      script.async = true;
      script.onload = start;
      script.onerror = start;
      root.document.head.appendChild(script);
      return;
    }
    start();
  }

  var api = {
    SUCCESS: SUCCESS,
    FAILURE: FAILURE,
    VALIDATION: VALIDATION,
    DISABLED: DISABLED,
    isFormId: isFormId,
    isSitekey: isSitekey,
    isReady: isReady,
    publicValues: publicValues,
    endpoint: endpoint,
    bindForm: bindForm,
    boot: boot
  };

  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  root.PSFormspree = api;
  if (root.document) {
    if (root.document.readyState === 'loading') {
      root.document.addEventListener('DOMContentLoaded', boot);
    } else {
      boot();
    }
  }
})(typeof window !== 'undefined' ? window : globalThis);
