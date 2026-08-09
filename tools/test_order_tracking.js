'use strict';

const assert = require('assert');
const portal = require('../store/track.js');

function baseConfig() {
  return {
    schema_version: 1,
    enabled: false,
    provider: 'api_adapter',
    api_base_url: '',
    authentication: 'email_magic_link',
    customer_visible_sources: ['tefa_odyssey', 'direct_site'],
    tefa: {
      purchase_system: 'odyssey_marketplace',
      order_history_authority: 'odyssey',
      preparation_station_role: 'fulfillment_status_mirror'
    },
    direct_commerce: {
      enabled: false,
      provider: 'stripe_checkout',
      webhook_required: true,
      allowed_skus: [],
      payment_links: {}
    },
    privacy: {
      public_order_lookup_allowed: false,
      store_order_data_in_browser: false,
      child_data_allowed: false
    }
  };
}

assert.deepStrictEqual(portal.validateConfig(baseConfig()), {
  valid: true,
  enabled: false,
  reason: 'disabled',
  apiBaseUrl: ''
});

const live = baseConfig();
live.enabled = true;
live.api_base_url = 'https://orders.example.com/';
assert.strictEqual(portal.validateConfig(live).enabled, true);
assert.strictEqual(portal.validateConfig(live).apiBaseUrl, 'https://orders.example.com');

const unsafe = baseConfig();
unsafe.privacy.public_order_lookup_allowed = true;
assert.strictEqual(portal.validateConfig(unsafe).valid, false);

const mixed = baseConfig();
mixed.tefa.order_history_authority = 'preparation_station';
assert.strictEqual(portal.validateConfig(mixed).reason, 'invalid_tefa_boundary');

assert.deepStrictEqual(
  portal.buildAccessRequest(' Adult@Example.com ', 'https://example.com/store/track.html?token=secret#orders'),
  {
    email: 'adult@example.com',
    return_url: 'https://example.com/store/track.html',
    source: 'preparation_station_order_portal'
  }
);
assert.throws(() => portal.buildAccessRequest('not-an-email', 'https://example.com/track'));
assert.throws(() => portal.buildAccessRequest('adult@example.com', 'http://example.com/track'));

console.log('Order tracking configuration and access requests are valid.');
