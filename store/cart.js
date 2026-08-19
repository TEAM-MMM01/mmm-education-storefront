/* Client-side quote cart and disabled-by-default request intake. The funded
   path creates a request record only; it never collects payment. A validated
   Formspree endpoint in config/request-intake.json is required before the
   online request button can be enabled. */
(function () {
  const KEY = 'preparation_station_cart_v1';
  const LEGACY_KEY = 'mmm_cart_v1';
  const REQUEST_CONFIG_URL = '../config/request-intake.json';
  const FORMSPREE_ENDPOINT = /^https:\/\/formspree\.io\/f\/[A-Za-z0-9_-]+\/?$/;
  const REQUEST_FIELDS = [
    '_gotcha',
    'adult_name',
    'cart_items',
    'client_reference',
    'email',
    'internal_owner',
    'notes',
    'program',
    'source',
    'submitted_at',
  ];
  const ALLOWED_PROGRAMS = ['TEFA', 'PDSES/ClassWallet', 'Self-pay', 'Other / not sure'];

  const PRODUCTS = {
    'PS-PR-101': { name: 'Home & Repair Tool Roll', price: null, dept: 'Practical & Trade' },
    'PS-PR-102': { name: 'Money & First Job Kit', price: null, dept: 'Practical & Trade' },
    'PS-PR-103': { name: 'Kitchen & Provision Kit', price: null, dept: 'Practical & Trade' },
    'PS-SC-201': { name: 'Situation Handling Deck', price: null, dept: 'Situation Handling & Self-Command' },
    'PS-SC-202': { name: 'Focus & Energy System', price: null, dept: 'Situation Handling & Self-Command' },
    'PS-SC-203': { name: 'Self-Advocacy Workbook', price: null, dept: 'Situation Handling & Self-Command' },
    'PS-SC-204': { name: 'Interview & First Job Prep Kit', price: null, dept: 'Situation Handling & Self-Command' },
    'PS-SC-205': { name: 'Adulting Launch Kit', price: null, dept: 'Situation Handling & Self-Command' },
    'PS-CS-301': { name: 'Graphic Design Bench', price: null, dept: 'Design & Motion Studio' },
    'PS-CS-302': { name: 'Motion & Video Kit', price: null, dept: 'Design & Motion Studio' },
    'PS-CS-303': { name: 'Skill-to-Income Pack', price: null, dept: 'Design & Motion Studio' },
    'PS-AT-401': { name: 'AI Literacy Bench Kit', price: null, dept: 'AI & Emerging Tech Bench' },
    'PS-AT-402': { name: 'Electronics & Robotics Starter', price: null, dept: 'AI & Emerging Tech Bench' },
    'PS-AT-403': { name: '3D Design & Fabrication Intro', price: null, dept: 'AI & Emerging Tech Bench' },
    'PS-HS-501': { name: 'Core Subjects Workbook Set', price: null, dept: 'Homeschool Essentials' },
    'PS-HS-502': { name: 'Homeschool Assessment & Portfolio Kit', price: null, dept: 'Homeschool Essentials' },
    'PS-HS-503': { name: 'Daily Supply Restock Box', price: null, dept: 'Homeschool Essentials' },
    'PS-HS-504': { name: 'Art & Craft Foundations Kit', price: null, dept: 'Homeschool Essentials' },
  };

  const requestState = {
    config: null,
    configStatus: 'loading',
    inFlight: false,
    needsRetry: false,
    receipt: null,
    completed: false,
  };

  function normalizeCart(value) {
    if (!value || typeof value !== 'object' || Array.isArray(value)) return {};
    return Object.entries(value).reduce(function (cart, entry) {
      const sku = entry[0];
      const qty = Number.parseInt(entry[1], 10);
      if (Object.prototype.hasOwnProperty.call(PRODUCTS, sku) && Number.isFinite(qty) && qty > 0) {
        cart[sku] = Math.min(qty, 99);
      }
      return cart;
    }, {});
  }

  function validateRequestConfig(config) {
    if (!config || config.schema_version !== 1 || config.provider !== 'formspree') {
      return { valid: false, reason: 'invalid_schema' };
    }
    if (config.support_email !== 'mmminvestment25@gmail.com') {
      return { valid: false, reason: 'invalid_support_email' };
    }
    if (!Number.isInteger(config.retention_days) || config.retention_days < 1 || config.retention_days > 90) {
      return { valid: false, reason: 'invalid_retention' };
    }
    if (!Array.isArray(config.allowed_skus)) {
      return { valid: false, reason: 'invalid_allowed_skus' };
    }
    const allowedSkus = config.allowed_skus;
    if (new Set(allowedSkus).size !== allowedSkus.length || allowedSkus.some(function (sku) {
      return typeof sku !== 'string' || !Object.prototype.hasOwnProperty.call(PRODUCTS, sku);
    })) {
      return { valid: false, reason: 'invalid_allowed_skus' };
    }
    const configuredFields = Array.isArray(config.allowed_submission_fields)
      ? config.allowed_submission_fields.slice().sort()
      : [];
    if (configuredFields.join('|') !== REQUEST_FIELDS.slice().sort().join('|')) {
      return { valid: false, reason: 'invalid_fields' };
    }
    if (config.endpoint && !FORMSPREE_ENDPOINT.test(config.endpoint)) {
      return { valid: false, reason: 'invalid_endpoint' };
    }
    if (config.enabled !== true) {
      return { valid: true, enabled: false, reason: 'disabled' };
    }
    if (allowedSkus.length === 0) {
      return { valid: false, reason: 'missing_allowed_skus' };
    }
    if (!FORMSPREE_ENDPOINT.test(config.endpoint)) {
      return { valid: false, reason: 'missing_endpoint' };
    }
    return { valid: true, enabled: true, reason: 'ready' };
  }

  function cartItems(cart) {
    const cleanCart = normalizeCart(cart);
    return Object.keys(cleanCart).sort().map(function (sku) {
      return { sku: sku, quantity: cleanCart[sku] };
    });
  }

  function createClientReference(now, token) {
    const stamp = new Date(now).toISOString().slice(0, 10).replace(/-/g, '');
    const cleanToken = String(token || '').toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 12);
    if (cleanToken.length < 6) throw new Error('A reference token of at least six characters is required.');
    return 'PSQ-' + stamp + '-' + cleanToken;
  }

  function randomReferenceToken() {
    const bytes = new Uint8Array(5);
    if (typeof crypto !== 'undefined' && crypto.getRandomValues) {
      crypto.getRandomValues(bytes);
      return Array.from(bytes, function (value) { return value.toString(16).padStart(2, '0'); }).join('');
    }
    return Math.random().toString(36).slice(2, 12).padEnd(10, '0');
  }

  function buildRequestPayload(values) {
    const items = cartItems(values.cart);
    if (items.length === 0) throw new Error('At least one catalog item is required.');
    const allowedSkus = Array.isArray(values.allowedSkus) ? values.allowedSkus : [];
    if (allowedSkus.length === 0) throw new Error('No catalog items are enabled for requests.');
    const disallowedSkus = items.filter(function (item) {
      return !allowedSkus.includes(item.sku);
    }).map(function (item) { return item.sku; });
    if (disallowedSkus.length) {
      throw new Error('Cart contains unavailable request SKUs: ' + disallowedSkus.join(', '));
    }
    const adultName = String(values.adultName || '').trim();
    const email = String(values.email || '').trim();
    const program = String(values.program || '').trim();
    const notes = String(values.notes || '').trim();
    if (!adultName || adultName.length > 120) throw new Error('Adult contact name is invalid.');
    if (!email || email.length > 254 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      throw new Error('Adult contact email is invalid.');
    }
    if (!ALLOWED_PROGRAMS.includes(program)) throw new Error('Program selection is invalid.');
    if (notes.length > 1000) throw new Error('Notes are too long.');
    if (!/^PSQ-\d{8}-[A-Z0-9]{6,12}$/.test(values.clientReference)) {
      throw new Error('Client reference is invalid.');
    }
    const payload = {
      _gotcha: String(values.honeypot || '').slice(0, 200),
      adult_name: adultName,
      cart_items: items.map(function (item) { return item.sku + ' x' + item.quantity; }).join('\n'),
      client_reference: values.clientReference,
      email: email,
      internal_owner: 'Nationwide Acquisitions, LLC',
      notes: notes,
      program: program,
      source: 'Preparation Station store/order.html',
      submitted_at: new Date(values.submittedAt).toISOString(),
    };
    if (Object.keys(payload).sort().join('|') !== REQUEST_FIELDS.slice().sort().join('|')) {
      throw new Error('Request payload fields do not match the approved allowlist.');
    }
    return payload;
  }

  function receiptText(receipt, supportEmail) {
    return [
      'Preparation Station quote request receipt',
      '',
      'Reference: ' + receipt.clientReference,
      'Submitted: ' + receipt.submittedAt,
      'Adult contact: ' + receipt.adultName,
      'Email: ' + receipt.email,
      'Program: ' + receipt.program,
      'Items:',
      receipt.cartItems,
      '',
      'No payment was collected. Pricing, availability, program eligibility, and fulfillment',
      'will be confirmed in writing before an order is accepted.',
      'Support: ' + supportEmail,
    ].join('\n');
  }

  function requestError(code) {
    const error = new Error(code);
    error.code = code;
    return error;
  }

  async function postRequest(endpoint, payload, fetchImpl, timeoutMs) {
    const controller = typeof AbortController !== 'undefined' ? new AbortController() : null;
    const timer = controller ? setTimeout(function () { controller.abort(); }, timeoutMs || 15000) : null;
    let response;
    try {
      response = await fetchImpl(endpoint, {
        method: 'POST',
        headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        credentials: 'omit',
        referrerPolicy: 'strict-origin-when-cross-origin',
        signal: controller ? controller.signal : undefined,
      });
    } catch (error) {
      if (error && error.name === 'AbortError') throw requestError('timeout');
      throw requestError('network');
    } finally {
      if (timer) clearTimeout(timer);
    }
    if (response.status === 429) throw requestError('rate_limit');
    if (response.status >= 500) throw requestError('service');
    if (!response.ok) throw requestError('rejected');
    return { accepted: true };
  }

  function friendlyRequestError(error) {
    const messages = {
      timeout: 'The request timed out. Check your connection and retry with the same reference.',
      network: 'We could not reach the request service. Check your connection and retry.',
      rate_limit: 'The request service is temporarily at its limit. Please wait and retry, or email us directly.',
      service: 'The request service is temporarily unavailable. Please retry, or email us directly.',
      rejected: 'The request was not accepted. Review the fields and retry, or email us directly.',
    };
    return messages[error && error.code] || messages.service;
  }

  function privacyNotice(retentionDays) {
    return 'We use this adult contact information only to review and follow up on this request. ' +
      'Do not include child names, disability or school records, account numbers, financial documents, ' +
      'or Social Security numbers. Intake records are deleted within ' + retentionDays +
      ' days after final follow-up unless an accepted transaction or law requires separate retention.';
  }

  function migrateLegacyCart() {
    if (localStorage.getItem(KEY) !== null) return;

    const legacyValue = localStorage.getItem(LEGACY_KEY);
    if (legacyValue === null) return;

    try {
      const legacyCart = JSON.parse(legacyValue) || {};
      const cart = {};
      Object.entries(legacyCart).forEach(function ([sku, qty]) {
        const currentSku = sku.replace(/^MMM-/, 'PS-');
        cart[currentSku] = (cart[currentSku] || 0) + qty;
      });
      localStorage.setItem(KEY, JSON.stringify(normalizeCart(cart)));
      localStorage.removeItem(LEGACY_KEY);
    } catch (e) {
      // Leave malformed legacy data untouched so it can be recovered manually.
    }
  }

  function readCart() {
    migrateLegacyCart();
    try { return normalizeCart(JSON.parse(localStorage.getItem(KEY))); }
    catch (e) { return {}; }
  }
  function writeCart(cart) {
    localStorage.setItem(KEY, JSON.stringify(normalizeCart(cart)));
    updateBadges();
  }
  function addToCart(sku, qty) {
    qty = qty || 1;
    const cart = readCart();
    cart[sku] = (cart[sku] || 0) + qty;
    writeCart(cart);
  }
  function setQty(sku, qty) {
    const cart = readCart();
    qty = Math.max(0, parseInt(qty, 10) || 0);
    if (qty === 0) delete cart[sku];
    else cart[sku] = qty;
    writeCart(cart);
  }
  function removeFromCart(sku) {
    const cart = readCart();
    delete cart[sku];
    writeCart(cart);
  }
  function cartCount() {
    return Object.values(readCart()).reduce((a, b) => a + b, 0);
  }
  function cartSubtotal() {
    const cart = readCart();
    return Object.entries(cart).reduce((sum, [sku, qty]) => {
      const p = PRODUCTS[sku];
      return sum + (p && Number.isFinite(p.price) ? p.price * qty : 0);
    }, 0);
  }

  function moneyOrPending(value) {
    return Number.isFinite(value) ? '$' + value.toFixed(2) : 'Price pending';
  }
  function updateBadges() {
    const n = cartCount();
    document.querySelectorAll('[data-cart-badge]').forEach(function (el) {
      el.textContent = n;
      el.hidden = n === 0;
    });
  }

  function requestSkuEnabled(config, sku) {
    return Boolean(
      config &&
      config.enabled === true &&
      Array.isArray(config.allowed_skus) &&
      config.allowed_skus.includes(sku) &&
      Object.prototype.hasOwnProperty.call(PRODUCTS, sku)
    );
  }

  function configureRequestButtons(config) {
    if (typeof document === 'undefined') return;
    document.querySelectorAll('[data-request-sku]').forEach(function (button) {
      const sku = button.getAttribute('data-request-sku');
      const enabled = requestSkuEnabled(config, sku);
      button.disabled = !enabled;
      button.setAttribute('aria-disabled', String(!enabled));
      button.textContent = enabled ? 'Add to information request' : 'Offering review pending';
      if (!enabled || button.dataset.requestHandlerBound === 'true') return;
      button.dataset.requestHandlerBound = 'true';
      button.addEventListener('click', function (event) {
        event.preventDefault();
        const qtyInput = document.querySelector('[data-qty-for="' + sku + '"]');
        const qty = qtyInput ? parseInt(qtyInput.value, 10) || 1 : 1;
        addToCart(sku, qty);
        toast(PRODUCTS[sku].name + ' added — ' + cartCount() + ' in request');
      });
    });
  }

  function toast(msg) {
    let t = document.getElementById('preparation-station-toast');
    if (!t) {
      t = document.createElement('div');
      t.id = 'preparation-station-toast';
      t.style.cssText = 'position:fixed;bottom:1.25rem;left:50%;transform:translateX(-50%) translateY(8px);' +
        'background:var(--ink);color:var(--paper);font-family:var(--mono);font-size:.72rem;letter-spacing:.06em;' +
        'padding:.65rem 1rem;border-radius:3px;z-index:200;opacity:0;transition:opacity .2s ease, transform .2s ease;pointer-events:none';
      document.body.appendChild(t);
    }
    t.textContent = msg;
    t.style.opacity = '1';
    t.style.transform = 'translateX(-50%) translateY(0)';
    clearTimeout(t._hideTimer);
    t._hideTimer = setTimeout(function () {
      t.style.opacity = '0';
      t.style.transform = 'translateX(-50%) translateY(8px)';
    }, 1600);
  }

  if (typeof document !== 'undefined') {
    document.addEventListener('DOMContentLoaded', function () {
      updateBadges();
      document.querySelectorAll('[data-add-to-cart]').forEach(function (btn) {
        btn.addEventListener('click', function (e) {
          e.preventDefault();
          const sku = btn.getAttribute('data-add-to-cart');
          const qtyInput = document.querySelector('[data-qty-for="' + sku + '"]');
          const qty = qtyInput ? parseInt(qtyInput.value, 10) || 1 : 1;
          addToCart(sku, qty);
          const p = PRODUCTS[sku];
          toast((p ? p.name : sku) + ' added — ' + cartCount() + ' in order');
        });
      });
      initializeRequestButtons();

      // Order page render and request intake.
      const list = document.getElementById('order-list');
      if (list) {
        renderOrder();
        initializeRequestIntake();
      }
    });
  }

  function renderOrder() {
    const cart = readCart();
    const list = document.getElementById('order-list');
    const skus = Object.keys(cart);

    if (skus.length === 0) {
      list.innerHTML =
        '<tr class="order-empty-row"><td colspan="5" class="order-empty-cell">Your order is empty. <a href="shop.html">Browse the shop</a> to add a kit.</td></tr>';
      updateSummary(0);
      syncRequestAvailability();
      return;
    }

    list.innerHTML = skus.map(function (sku) {
      const p = PRODUCTS[sku] || { name: sku, price: null, dept: '' };
      const qty = cart[sku];
      const lineTotal = Number.isFinite(p.price) ? p.price * qty : null;
      return (
        '<tr data-row="' + sku + '">' +
          '<td><span class="oi-name">' + p.name + '</span><span class="oi-sku">' + sku + ' · ' + p.dept + '</span></td>' +
          '<td class="oi-num">' + moneyOrPending(p.price) + '</td>' +
          '<td style="text-align:center"><span class="qty">' +
            '<button type="button" data-step="-1" data-sku="' + sku + '" aria-label="Decrease quantity">−</button>' +
            '<input type="text" inputmode="numeric" value="' + qty + '" data-qty-for="' + sku + '" aria-label="Quantity for ' + p.name + '">' +
            '<button type="button" data-step="1" data-sku="' + sku + '" aria-label="Increase quantity">+</button>' +
          '</span></td>' +
          '<td class="oi-num">' + moneyOrPending(lineTotal) + '</td>' +
          '<td><button type="button" class="oi-remove" data-remove="' + sku + '">Remove</button></td>' +
        '</tr>'
      );
    }).join('');

    list.querySelectorAll('[data-step]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        const sku = btn.getAttribute('data-sku');
        const step = parseInt(btn.getAttribute('data-step'), 10);
        const current = readCart()[sku] || 0;
        setQty(sku, current + step);
        renderOrder();
      });
    });
    list.querySelectorAll('[data-qty-for]').forEach(function (input) {
      input.addEventListener('change', function () {
        setQty(input.getAttribute('data-qty-for'), input.value);
        renderOrder();
      });
    });
    list.querySelectorAll('[data-remove]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        removeFromCart(btn.getAttribute('data-remove'));
        renderOrder();
      });
    });

    updateSummary(cartSubtotal());
    buildQuoteLink();
    syncRequestAvailability();
  }

  function updateSummary(subtotal) {
    const el = document.getElementById('order-subtotal');
    const total = document.getElementById('order-total');
    const anyPending = Object.keys(readCart()).some(function (sku) {
      return !Number.isFinite((PRODUCTS[sku] || {}).price);
    });
    const display = anyPending ? 'Price pending' : '$' + subtotal.toFixed(2);
    if (el) el.textContent = display;
    if (total) total.textContent = display;
  }

  function buildQuoteLink() {
    const cart = readCart();
    const link = document.getElementById('quote-link');
    if (!link) return;
    const lines = Object.entries(cart).map(function ([sku, qty]) {
      const p = PRODUCTS[sku] || { name: sku, price: null };
      return '- ' + p.name + ' (' + sku + ')  x' + qty + '  — ' + moneyOrPending(p.price);
    });
    const body = 'Hi Preparation Station,%0D%0A%0D%0AI would like an itemized quote for:%0D%0A%0D%0A' +
      encodeURIComponent(lines.join('\n')).replace(/%0A/g, '%0D%0A') +
      '%0D%0A%0D%0APrices remain pending until the offering or direct listing is approved.' +
      '%0D%0A%0D%0AState: [your state]%0D%0AFunding program: [TEFA / other]%0D%0A';
    link.href = 'mailto:Mmminvestment25@gmail.com?subject=' +
      encodeURIComponent('Quote request — ' + Object.keys(cart).length + ' item(s)') +
      '&body=' + body;
  }

  function requestElements() {
    return {
      form: document.getElementById('quote-form'),
      button: document.getElementById('quote-submit'),
      status: document.getElementById('quote-status'),
      error: document.getElementById('quote-error'),
      confirmation: document.getElementById('quote-confirmation'),
      reference: document.getElementById('quote-reference'),
      privacy: document.getElementById('quote-privacy'),
      download: document.getElementById('download-receipt'),
    };
  }

  function setRequestMessage(element, message) {
    if (element) element.textContent = message;
  }

  function setRequestControlsDisabled(disabled) {
    const elements = requestElements();
    if (!elements.form) return;
    elements.form.querySelectorAll('input, select, textarea, button').forEach(function (control) {
      control.disabled = disabled;
    });
    if (elements.button) elements.button.setAttribute('aria-disabled', String(disabled));
  }

  function syncRequestAvailability() {
    if (typeof document === 'undefined') return;
    const elements = requestElements();
    if (!elements.form || requestState.inFlight || requestState.completed) return;

    let disabled = true;
    let label = 'Online requests not configured';
    let status = 'Online quote requests are disabled until the secure request endpoint is configured.';

    if (requestState.configStatus === 'loading') {
      label = 'Checking request service…';
      status = 'Checking whether the request service is available.';
    } else if (requestState.configStatus === 'unavailable') {
      label = 'Request service unavailable';
      status = 'The online request service could not be verified. You can retry by reloading or email us directly.';
    } else if (requestState.configStatus === 'ready' && cartCount() === 0) {
      label = 'Add items to request a quote';
      status = 'Add at least one catalog item before sending a quote request.';
    } else if (requestState.configStatus === 'ready') {
      const unavailable = cartItems(readCart()).filter(function (item) {
        return !requestState.config.allowed_skus.includes(item.sku);
      }).map(function (item) { return item.sku; });
      if (unavailable.length) {
        label = 'Cart contains unavailable items';
        status = 'Only configured launch items can be requested online. Remove: ' + unavailable.join(', ') + '.';
      } else {
        disabled = false;
        label = requestState.needsRetry ? 'Retry quote request' : 'Send quote request';
        status = 'Ready to create a request record. No payment will be collected.';
      }
    }

    setRequestControlsDisabled(disabled);
    if (elements.button) elements.button.textContent = label;
    setRequestMessage(elements.status, status);
  }

  function injectHoneypot(form) {
    if (form.querySelector('[name="_gotcha"]')) return;
    const wrapper = document.createElement('div');
    wrapper.className = 'request-honeypot';
    wrapper.setAttribute('aria-hidden', 'true');
    const label = document.createElement('label');
    label.setAttribute('for', 'quote-company-site');
    label.textContent = 'Company website';
    const input = document.createElement('input');
    input.type = 'text';
    input.id = 'quote-company-site';
    input.name = '_gotcha';
    input.tabIndex = -1;
    input.autocomplete = 'off';
    wrapper.appendChild(label);
    wrapper.appendChild(input);
    form.appendChild(wrapper);
  }

  async function loadRequestConfig() {
    const response = await fetch(REQUEST_CONFIG_URL, {
      cache: 'no-store',
      credentials: 'same-origin',
      headers: { Accept: 'application/json' },
    });
    if (!response.ok) throw new Error('Request configuration could not be loaded.');
    return response.json();
  }

  async function initializeRequestButtons() {
    if (typeof document === 'undefined' || !document.querySelector('[data-request-sku]')) return;
    try {
      const config = await loadRequestConfig();
      const result = validateRequestConfig(config);
      configureRequestButtons(result.valid && result.enabled ? config : null);
    } catch (error) {
      configureRequestButtons(null);
    }
  }

  function requestFormValues(form) {
    return {
      adultName: form.querySelector('#quote-name').value,
      email: form.querySelector('#quote-email').value,
      program: form.querySelector('#quote-program').value,
      notes: form.querySelector('#quote-notes').value,
      honeypot: form.querySelector('[name="_gotcha"]').value,
    };
  }

  function newRequestReceipt(values, payload) {
    return {
      clientReference: payload.client_reference,
      submittedAt: payload.submitted_at,
      adultName: payload.adult_name,
      email: payload.email,
      program: payload.program,
      cartItems: payload.cart_items,
      values: values,
    };
  }

  async function submitQuoteRequest(event) {
    event.preventDefault();
    const elements = requestElements();
    if (!elements.form || requestState.inFlight || requestState.configStatus !== 'ready') {
      syncRequestAvailability();
      return;
    }
    elements.error.hidden = true;
    if (!elements.form.checkValidity()) {
      elements.form.reportValidity();
      setRequestMessage(elements.error, 'Complete the adult contact, email, and program fields, then retry.');
      elements.error.hidden = false;
      return;
    }
    if (cartCount() === 0) {
      syncRequestAvailability();
      return;
    }

    const values = requestFormValues(elements.form);
    const submittedAt = requestState.receipt ? requestState.receipt.submittedAt : new Date().toISOString();
    const clientReference = requestState.receipt
      ? requestState.receipt.clientReference
      : createClientReference(submittedAt, randomReferenceToken());
    let payload;
    try {
      payload = buildRequestPayload({
        adultName: values.adultName,
        email: values.email,
        program: values.program,
        notes: values.notes,
        honeypot: values.honeypot,
        cart: readCart(),
        allowedSkus: requestState.config.allowed_skus,
        clientReference: clientReference,
        submittedAt: submittedAt,
      });
    } catch (error) {
      setRequestMessage(elements.error, 'The request could not be prepared. Reload the page and retry.');
      elements.error.hidden = false;
      return;
    }

    requestState.receipt = newRequestReceipt(values, payload);
    requestState.inFlight = true;
    requestState.needsRetry = false;
    setRequestControlsDisabled(true);
    elements.button.textContent = 'Sending request…';
    setRequestMessage(elements.status, 'Creating your request record. Keep this page open.');

    try {
      await postRequest(requestState.config.endpoint, payload, fetch, 15000);
      elements.form.hidden = true;
      elements.confirmation.hidden = false;
      requestState.completed = true;
      setRequestMessage(elements.reference, requestState.receipt.clientReference);
      setRequestMessage(elements.status, 'Request received. Save the reference or download the receipt.');
      if (elements.download) elements.download.disabled = false;
      elements.confirmation.focus();
    } catch (error) {
      requestState.needsRetry = true;
      setRequestMessage(elements.error, friendlyRequestError(error));
      elements.error.hidden = false;
      requestState.inFlight = false;
      syncRequestAvailability();
      return;
    }
    requestState.inFlight = false;
  }

  function downloadReceipt() {
    if (!requestState.receipt || !requestState.config) return;
    const content = receiptText(requestState.receipt, requestState.config.support_email);
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'preparation-station-' + requestState.receipt.clientReference + '.txt';
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  async function initializeRequestIntake() {
    const elements = requestElements();
    if (!elements.form) return;
    injectHoneypot(elements.form);
    elements.form.addEventListener('submit', submitQuoteRequest);
    if (elements.download) elements.download.addEventListener('click', downloadReceipt);
    setRequestMessage(elements.privacy, privacyNotice(30));
    syncRequestAvailability();

    try {
      const config = await loadRequestConfig();
      const result = validateRequestConfig(config);
      requestState.config = config;
      if (!result.valid) {
        requestState.configStatus = 'unavailable';
      } else if (!result.enabled) {
        requestState.configStatus = 'disabled';
      } else {
        requestState.configStatus = 'ready';
      }
      if (elements.privacy && result.valid) {
        setRequestMessage(elements.privacy, privacyNotice(config.retention_days));
      }
    } catch (error) {
      requestState.configStatus = 'unavailable';
    }
    syncRequestAvailability();
  }

  const exported = {
    addToCart,
    removeFromCart,
    setQty,
    cartCount,
    cartSubtotal,
    PRODUCTS,
    requestIntake: {
      REQUEST_FIELDS,
      ALLOWED_PROGRAMS,
      normalizeCart,
      validateRequestConfig,
      cartItems,
      createClientReference,
      buildRequestPayload,
      receiptText,
      postRequest,
      friendlyRequestError,
      privacyNotice,
      requestSkuEnabled,
    },
  };
  if (typeof window !== 'undefined') window.preparationStationCart = exported;
  if (typeof module !== 'undefined' && module.exports) module.exports = exported;
})();
