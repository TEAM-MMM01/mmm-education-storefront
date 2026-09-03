import assert from 'node:assert/strict';
import test from 'node:test';
import {
  extractTurnstileToken,
  handleRequest,
  resetRateLimitForTests,
  validOrigin,
  validPayload,
  validateEnv
} from '../src/index.js';

const ENV = {
  ALLOWED_ORIGIN: 'https://preparationstation.org',
  TURNSTILE_SECRET_KEY: 'test-turnstile-secret',
  TURNSTILE_HOSTNAMES: 'preparationstation.org',
  RESEND_API_KEY: 're_test_key',
  OPERATIONS_EMAIL: 'Operations@preparationstation.org',
  RESEND_FROM_EMAIL: 'Support@preparationstation.org'
};

function pathwayPayload(overrides = {}) {
  return {
    adult_name: 'Adult Example',
    email: 'adult@example.com',
    age_band: 'Ages 13–17 Advanced Command',
    goal: 'Independent living and money habits',
    purchase_path: 'TEFA / official marketplace',
    message: 'Please recommend a current pathway. No student records attached.',
    organization: '',
    client_reference: 'PSQ-20260903-TEST01',
    submitted_at: new Date(Date.now() - 2000).toISOString(),
    source: 'contact_pathway',
    _gotcha: '',
    ...overrides
  };
}

function mockFetch({ siteverify = { success: true, action: 'contact_pathway', hostname: 'preparationstation.org' }, resendStatus = 200 } = {}) {
  const calls = [];
  const fetchImpl = async (url, options = {}) => {
    calls.push({ url, options });
    if (String(url).includes('turnstile/v0/siteverify')) {
      return new Response(JSON.stringify(siteverify), { status: 200 });
    }
    if (String(url).includes('api.resend.com')) {
      return new Response(JSON.stringify({ id: 'mock-email' }), { status: resendStatus });
    }
    throw new Error(`unexpected fetch ${url}`);
  };
  return { fetchImpl, calls };
}

async function post(body, { headers = {}, fetchImpl } = {}) {
  resetRateLimitForTests();
  const request = new Request('https://preparation-station-intake.example/intake', {
    method: 'POST',
    headers: {
      origin: ENV.ALLOWED_ORIGIN,
      'content-type': 'application/json',
      'CF-Connecting-IP': '203.0.113.10',
      ...headers
    },
    body: typeof body === 'string' ? body : JSON.stringify(body)
  });
  return handleRequest(request, ENV, { fetchImpl });
}

test('validateEnv requires Turnstile and email secrets, not a browser shared secret', () => {
  assert.equal(validateEnv(ENV), null);
  assert.equal(validateEnv({ ...ENV, TURNSTILE_SECRET_KEY: '' }), 'missing_env_turnstile_secret_key');
  assert.equal(validateEnv({ ...ENV, INTAKE_SHARED_SECRET: 'x' }), null);
});

test('validOrigin requires exact configured origin', () => {
  const request = new Request('https://worker.example', {
    headers: { origin: 'https://preparationstation.org' }
  });
  assert.equal(validOrigin(request, 'https://preparationstation.org'), true);
  assert.equal(validOrigin(request, 'https://evil.example'), false);
});

test('validPayload accepts a pathway request and a school quote', () => {
  assert.equal(validPayload(pathwayPayload()), null);
  assert.equal(
    validPayload({
      adult_name: 'Adult Example',
      email: 'adult@example.com',
      organization: 'Example ISD',
      grade_band: '9-12',
      interest: 'PS-IL-1995',
      learner_count: '12',
      timeline: 'Fall',
      message: 'Written quote only.',
      client_reference: 'PSQ-20260903-QUOTE1',
      submitted_at: new Date(Date.now() - 2000).toISOString(),
      source: 'school_quote',
      _gotcha: ''
    }),
    null
  );
});

test('validPayload rejects secrets-shaped fields, honeypots, and invalid values', () => {
  assert.equal(validPayload(pathwayPayload({ card_number: '4242' })), 'unexpected_field');
  assert.equal(validPayload(pathwayPayload({ ssn: '000-00-0000' })), 'unexpected_field');
  assert.equal(validPayload(pathwayPayload({ _gotcha: 'bot' })), 'spam_detected');
  assert.equal(validPayload(pathwayPayload({ email: 'not-an-email' })), 'invalid_email');
  assert.equal(validPayload(pathwayPayload({ purchase_path: 'Stripe checkout' })), 'invalid_purchase_path');
});

test('extractTurnstileToken removes the token so it is never stored or emailed', () => {
  const payload = { turnstile_token: 'tok', adult_name: 'A' };
  assert.equal(extractTurnstileToken(payload), 'tok');
  assert.equal('turnstile_token' in payload, false);
});

test('OPTIONS CORS does not allow x-intake-secret', async () => {
  resetRateLimitForTests();
  const response = await handleRequest(
    new Request('https://preparation-station-intake.example/intake', {
      method: 'OPTIONS',
      headers: { origin: ENV.ALLOWED_ORIGIN }
    }),
    ENV,
    mockFetch()
  );
  assert.equal(response.status, 204);
  assert.equal(response.headers.get('access-control-allow-headers'), 'content-type');
  assert.equal(response.headers.get('access-control-allow-headers').includes('x-intake-secret'), false);
});

test('POST without a Turnstile token is rejected and does not send email', async () => {
  const { fetchImpl, calls } = mockFetch();
  const response = await post(pathwayPayload(), { fetchImpl });
  assert.equal(response.status, 403);
  assert.deepEqual(await response.json(), { ok: false, code: 'verification_failed' });
  assert.equal(calls.some((call) => String(call.url).includes('api.resend.com')), false);
});

test('POST with a failed siteverify is rejected', async () => {
  const { fetchImpl } = mockFetch({ siteverify: { success: false, 'error-codes': ['invalid-input-response'] } });
  const response = await post({ ...pathwayPayload(), turnstile_token: 'bad-token' }, { fetchImpl });
  assert.equal(response.status, 403);
});

test('POST with mocked Turnstile and Resend succeeds without a shared secret header', async () => {
  const { fetchImpl, calls } = mockFetch();
  const response = await post({ ...pathwayPayload(), turnstile_token: 'ok-token' }, { fetchImpl });
  assert.equal(response.status, 202);
  const body = await response.json();
  assert.equal(body.ok, true);
  assert.equal(body.reference, 'PSQ-20260903-TEST01');
  assert.equal(calls.some((call) => String(call.url).includes('siteverify')), true);
  assert.equal(calls.some((call) => String(call.url).includes('api.resend.com')), true);
  const resend = calls.find((call) => String(call.url).includes('api.resend.com'));
  const mailed = JSON.parse(resend.options.body);
  assert.equal(JSON.stringify(mailed).includes('ok-token'), false);
  assert.equal(JSON.stringify(mailed).includes('test-turnstile-secret'), false);
});

test('x-intake-secret is ignored and cannot replace Turnstile', async () => {
  const { fetchImpl } = mockFetch();
  const response = await post(pathwayPayload(), {
    fetchImpl,
    headers: { 'x-intake-secret': 'anything' }
  });
  assert.equal(response.status, 403);
});
