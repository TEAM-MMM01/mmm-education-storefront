'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const cart = require(path.join(root, 'store', 'cart.js'));
const intake = cart.requestIntake;
const config = JSON.parse(fs.readFileSync(path.join(root, 'config', 'request-intake.json'), 'utf8'));

async function expectCode(promise, code) {
  await assert.rejects(promise, function (error) {
    return error && error.code === code;
  });
}

async function main() {
  assert.deepEqual(intake.validateRequestConfig(config), {
    valid: true,
    enabled: false,
    reason: 'disabled',
  });

  const readyConfig = {
    ...config,
    enabled: true,
    endpoint: 'https://worker.example/intake',
    allowed_skus: ['PS-PR-101', 'PS-SC-201'],
  };
  assert.deepEqual(intake.validateRequestConfig(readyConfig), {
    valid: true,
    enabled: true,
    reason: 'ready',
  });
  assert.deepEqual(
    intake.validateRequestConfig({ ...readyConfig, allowed_skus: [] }),
    { valid: false, reason: 'missing_allowed_skus' },
  );
  assert.deepEqual(
    intake.validateRequestConfig({ ...readyConfig, allowed_skus: ['PS-NO-999'] }),
    { valid: false, reason: 'invalid_allowed_skus' },
  );
  assert.deepEqual(
    intake.validateRequestConfig({ ...readyConfig, allowed_skus: ['PS-PR-101', 'PS-PR-101'] }),
    { valid: false, reason: 'invalid_allowed_skus' },
  );
  assert.equal(intake.requestSkuEnabled(readyConfig, 'PS-PR-101'), true);
  assert.equal(intake.requestSkuEnabled(readyConfig, 'PS-HS-504'), false);
  assert.equal(intake.requestSkuEnabled({ ...readyConfig, enabled: false }, 'PS-PR-101'), false);
  for (const endpoint of [
    'http://worker.example/intake',
    'https://evil.example/f/test',
    'https://worker.example',
    'https://worker.example/intake?redirect=evil',
  ]) {
    assert.equal(
      intake.validateRequestConfig({ ...readyConfig, endpoint }).valid,
      false,
      `Rejected unsafe endpoint: ${endpoint}`,
    );
  }

  assert.deepEqual(
    intake.normalizeCart({ 'PS-PR-101': 2, 'PS-SC-201': '3', UNKNOWN: 4, 'PS-HS-501': -1 }),
    { 'PS-PR-101': 2, 'PS-SC-201': 3 },
  );
  assert.deepEqual(intake.normalizeCart({ 'PS-PR-101': 1000 }), { 'PS-PR-101': 99 });

  const reference = intake.createClientReference('2026-08-09T12:00:00.000Z', 'a1-b2-c3-d4');
  assert.equal(reference, 'PSQ-20260809-A1B2C3D4');
  const payload = intake.buildRequestPayload({
    adultName: ' Adult Owner ',
    email: 'adult@example.com ',
    program: 'TEFA',
    notes: 'Please confirm the product format.',
    honeypot: '',
    cart: { 'PS-SC-201': 1, UNKNOWN: 2, 'PS-PR-101': 2 },
    allowedSkus: readyConfig.allowed_skus,
    clientReference: reference,
    submittedAt: '2026-08-09T12:00:00.000Z',
  });
  assert.deepEqual(Object.keys(payload).sort(), intake.REQUEST_FIELDS.slice().sort());
  assert.equal(payload.adult_name, 'Adult Owner');
  assert.equal(payload.cart_items, 'PS-PR-101 x2\nPS-SC-201 x1');
  assert.equal(payload.internal_owner, 'Nationwide Acquisitions, LLC');
  assert.ok(!JSON.stringify(payload).includes('UNKNOWN'));
  for (const forbidden of ['child_name', 'school_id', 'payment', 'account_number', 'ssn']) {
    assert.ok(!Object.prototype.hasOwnProperty.call(payload, forbidden));
  }
  assert.throws(function () {
    intake.buildRequestPayload({
      adultName: 'Adult Owner',
      email: 'adult@example.com',
      program: 'TEFA approved purchase',
      notes: '',
      honeypot: '',
      cart: { 'PS-PR-101': 1 },
      allowedSkus: readyConfig.allowed_skus,
      clientReference: reference,
      submittedAt: '2026-08-09T12:00:00.000Z',
    });
  }, /Program selection is invalid/);
  assert.throws(function () {
    intake.buildRequestPayload({
      adultName: 'Adult Owner',
      email: 'adult@example.com',
      program: 'TEFA',
      notes: '',
      honeypot: '',
      cart: { 'PS-PR-101': 1 },
      allowedSkus: [],
      clientReference: reference,
      submittedAt: '2026-08-09T12:00:00.000Z',
    });
  }, /No catalog items are enabled/);
  assert.throws(function () {
    intake.buildRequestPayload({
      adultName: 'Adult Owner',
      email: 'adult@example.com',
      program: 'TEFA',
      notes: '',
      honeypot: '',
      cart: { 'PS-PR-101': 1, 'PS-SC-201': 1 },
      allowedSkus: ['PS-PR-101'],
      clientReference: reference,
      submittedAt: '2026-08-09T12:00:00.000Z',
    });
  }, /unavailable request SKUs: PS-SC-201/);

  const receipt = intake.receiptText({
    clientReference: reference,
    submittedAt: payload.submitted_at,
    adultName: payload.adult_name,
    email: payload.email,
    program: payload.program,
    cartItems: payload.cart_items,
  }, config.support_email);
  assert.match(receipt, /No payment was collected/);
  assert.match(receipt, new RegExp(reference));
  assert.match(receipt, /PS-PR-101 x2/);
  assert.ok(!receipt.includes(payload.notes), 'Receipt intentionally omits free-form notes');

  let submittedOptions;
  const accepted = await intake.postRequest(
    readyConfig.endpoint,
    payload,
    async function (endpoint, options) {
      assert.equal(endpoint, readyConfig.endpoint);
      submittedOptions = options;
      return { ok: true, status: 200 };
    },
    100,
  );
  assert.deepEqual(accepted, { accepted: true });
  assert.equal(submittedOptions.method, 'POST');
  assert.equal(submittedOptions.credentials, 'omit');
  assert.deepEqual(JSON.parse(submittedOptions.body), payload);

  await expectCode(
    intake.postRequest(readyConfig.endpoint, payload, async function () {
      return { ok: false, status: 429 };
    }, 100),
    'rate_limit',
  );
  await expectCode(
    intake.postRequest(readyConfig.endpoint, payload, async function () {
      throw new Error('offline');
    }, 100),
    'network',
  );
  assert.match(intake.friendlyRequestError({ code: 'rate_limit' }), /temporarily at its limit/);
  assert.match(intake.privacyNotice(config.retention_days), /30 days/);
  assert.match(intake.privacyNotice(config.retention_days), /Do not include child names/);

  console.log('Request intake tests passed.');
}

main().catch(function (error) {
  console.error(error);
  process.exitCode = 1;
});
