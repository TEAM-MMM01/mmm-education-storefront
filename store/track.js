/* Secure-link entry point for the unified order portal. No order records are
   stored in the browser. The checked-in configuration is disabled until a
   private API with authentication and customer-level authorization exists. */
(function (root) {
  'use strict';

  const CONFIG_URL = '../config/order-portal.json';
  const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  function validateConfig(config) {
    if (!config || config.schema_version !== 1 || config.provider !== 'api_adapter') {
      return { valid: false, enabled: false, reason: 'invalid_schema' };
    }
    if (config.authentication !== 'email_magic_link') {
      return { valid: false, enabled: false, reason: 'invalid_authentication' };
    }
    const sources = Array.isArray(config.customer_visible_sources)
      ? config.customer_visible_sources.slice().sort()
      : [];
    if (sources.join('|') !== 'direct_site|tefa_odyssey') {
      return { valid: false, enabled: false, reason: 'invalid_sources' };
    }
    const privacy = config.privacy || {};
    if (privacy.public_order_lookup_allowed !== false ||
        privacy.store_order_data_in_browser !== false ||
        privacy.child_data_allowed !== false) {
      return { valid: false, enabled: false, reason: 'unsafe_privacy' };
    }
    const tefa = config.tefa || {};
    if (tefa.purchase_system !== 'odyssey_marketplace' ||
        tefa.order_history_authority !== 'odyssey' ||
        tefa.preparation_station_role !== 'fulfillment_status_mirror') {
      return { valid: false, enabled: false, reason: 'invalid_tefa_boundary' };
    }
    const direct = config.direct_commerce || {};
    if (direct.provider !== 'stripe_checkout' || direct.webhook_required !== true ||
        !Array.isArray(direct.allowed_skus) || !direct.payment_links ||
        typeof direct.payment_links !== 'object' || Array.isArray(direct.payment_links)) {
      return { valid: false, enabled: false, reason: 'invalid_direct_commerce' };
    }
    const base = String(config.api_base_url || '').replace(/\/$/, '');
    if (config.enabled !== true) {
      return { valid: true, enabled: false, reason: 'disabled', apiBaseUrl: base };
    }
    if (!/^https:\/\/[^\s/]+(?:\/[^\s]*)?$/.test(base)) {
      return { valid: false, enabled: false, reason: 'invalid_api_url' };
    }
    return { valid: true, enabled: true, reason: 'ready', apiBaseUrl: base };
  }

  function normalizeEmail(value) {
    return String(value || '').trim().toLowerCase();
  }

  function buildAccessRequest(email, returnUrl) {
    const normalized = normalizeEmail(email);
    if (!EMAIL_PATTERN.test(normalized) || normalized.length > 254) {
      throw new Error('Enter a valid adult contact email.');
    }
    const target = new URL(returnUrl);
    if (target.protocol !== 'https:' && target.hostname !== 'localhost') {
      throw new Error('A secure return URL is required.');
    }
    target.search = '';
    target.hash = '';
    return {
      email: normalized,
      return_url: target.toString(),
      source: 'preparation_station_order_portal'
    };
  }

  async function postAccessRequest(apiBaseUrl, payload, fetchImpl) {
    const response = await fetchImpl(apiBaseUrl + '/v1/order-access-links', {
      method: 'POST',
      credentials: 'omit',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json'
      },
      referrerPolicy: 'strict-origin-when-cross-origin',
      body: JSON.stringify(payload)
    });
    if (response.status === 429) throw new Error('rate_limit');
    if (!response.ok) throw new Error('service');
    return { accepted: true };
  }

  const api = { validateConfig, normalizeEmail, buildAccessRequest, postAccessRequest };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  root.PreparationStationOrderPortal = api;

  if (typeof document === 'undefined') return;

  document.addEventListener('DOMContentLoaded', async function () {
    const form = document.getElementById('order-access-form');
    const email = document.getElementById('order-access-email');
    const button = document.getElementById('order-access-submit');
    const status = document.getElementById('order-access-status');
    const error = document.getElementById('order-access-error');
    if (!form || !email || !button || !status || !error) return;

    let checked = { valid: false, enabled: false, reason: 'not_loaded' };
    try {
      const response = await fetch(CONFIG_URL, { credentials: 'same-origin', cache: 'no-store' });
      if (!response.ok) throw new Error('config');
      checked = validateConfig(await response.json());
    } catch (configError) {
      checked = { valid: false, enabled: false, reason: 'unavailable' };
    }

    if (!checked.valid || !checked.enabled) {
      status.textContent = 'Secure online order access is being configured. TEFA families can use Odyssey Order History now; direct-order help is available by email.';
      button.disabled = true;
      button.setAttribute('aria-disabled', 'true');
      return;
    }

    status.textContent = 'Enter the adult email used for the order. We will send a secure access link if a matching account exists.';
    button.disabled = false;
    button.removeAttribute('aria-disabled');

    form.addEventListener('submit', async function (event) {
      event.preventDefault();
      error.hidden = true;
      button.disabled = true;
      button.textContent = 'Sending secure link…';
      try {
        const payload = buildAccessRequest(email.value, window.location.href);
        await postAccessRequest(checked.apiBaseUrl, payload, window.fetch.bind(window));
        form.reset();
        status.textContent = 'If that email matches an order account, a secure link is on its way. Check spam before requesting another link.';
      } catch (requestError) {
        error.textContent = requestError.message === 'rate_limit'
          ? 'Too many attempts. Wait a few minutes before trying again.'
          : requestError.message === 'service'
            ? 'Secure order access is temporarily unavailable. Email support and include only your order reference.'
            : requestError.message;
        error.hidden = false;
      } finally {
        button.disabled = false;
        button.textContent = 'Email my secure tracking link';
      }
    });
  });
})(typeof window !== 'undefined' ? window : globalThis);
