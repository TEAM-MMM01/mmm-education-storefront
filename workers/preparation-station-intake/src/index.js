const MAX_BODY_BYTES = 16384;
const MIN_FORM_AGE_MS = 1500;
const MAX_FORM_AGE_MS = 1000 * 60 * 60 * 24;
const MAX_FIELD_LENGTH = 2000;
const RATE_WINDOW_MS = 10 * 60 * 1000;
const RATE_MAX = 8;
const SITEVERIFY_URL = 'https://challenges.cloudflare.com/turnstile/v0/siteverify';
const RESEND_URL = 'https://api.resend.com/emails';

const ALLOWED_FIELDS = new Set([
  '_gotcha',
  'adult_name',
  'age_band',
  'client_reference',
  'email',
  'goal',
  'grade_band',
  'interest',
  'learner_count',
  'message',
  'organization',
  'purchase_path',
  'source',
  'submitted_at',
  'timeline'
]);

const AGE_BANDS = new Set([
  'Ages 3–5 Launchpad',
  'Ages 6–8 Explorer',
  'Ages 9–12 Mission Control',
  'Ages 13–17 Advanced Command',
  'Parent / educator Planner Mode'
]);

const GOALS = new Set([
  'Practical life skills',
  'Independent living and money habits',
  'Career readiness',
  'Self-command and communication',
  'Digital judgment / AI literacy',
  'Design and making',
  'Homeschool planning',
  'Not sure yet'
]);

const PURCHASE_PATHS = new Set([
  'TEFA / official marketplace',
  'Direct family purchase',
  'School or district',
  'Not sure yet'
]);

const SOURCES = {
  contact_pathway: ['adult_name', 'email', 'age_band', 'goal', 'purchase_path', 'message', 'client_reference', 'submitted_at'],
  school_quote: ['adult_name', 'email', 'organization', 'grade_band', 'interest', 'learner_count', 'timeline', 'message', 'client_reference', 'submitted_at']
};

const rateBuckets = new Map();

function json(body, status = 200, extraHeaders = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      'content-type': 'application/json; charset=utf-8',
      'cache-control': 'no-store',
      'x-content-type-options': 'nosniff',
      ...extraHeaders
    }
  });
}

function reject(status, code, extraHeaders = {}) {
  return json({ ok: false, code }, status, extraHeaders);
}

function validOrigin(request, expectedOrigin) {
  if (typeof expectedOrigin !== 'string' || !expectedOrigin) return false;
  return request.headers.get('origin') === expectedOrigin;
}

function corsHeaders(origin) {
  return {
    'access-control-allow-origin': origin,
    'access-control-allow-methods': 'POST, OPTIONS',
    'access-control-allow-headers': 'content-type',
    'access-control-max-age': '600',
    vary: 'Origin'
  };
}

function originHeaders(origin) {
  return {
    'access-control-allow-origin': origin,
    vary: 'Origin'
  };
}

function validateEnv(env) {
  const required = [
    'ALLOWED_ORIGIN',
    'TURNSTILE_SECRET_KEY',
    'TURNSTILE_HOSTNAMES',
    'RESEND_API_KEY',
    'OPERATIONS_EMAIL',
    'RESEND_FROM_EMAIL'
  ];

  for (const key of required) {
    if (typeof env[key] !== 'string' || !env[key].trim()) {
      return `missing_env_${key.toLowerCase()}`;
    }
  }

  try {
    new URL(env.ALLOWED_ORIGIN);
  } catch {
    return 'invalid_env_allowed_origin';
  }

  return null;
}

function clientIp(request) {
  const cf = request.headers.get('CF-Connecting-IP');
  if (cf && cf.trim()) return cf.trim();
  const forwarded = request.headers.get('X-Forwarded-For');
  if (forwarded) return forwarded.split(',')[0].trim() || 'unknown';
  return 'unknown';
}

function resetRateLimitForTests() {
  rateBuckets.clear();
}

function rateLimited(ip, now = Date.now()) {
  const recent = (rateBuckets.get(ip) || []).filter((stamp) => now - stamp < RATE_WINDOW_MS);
  if (recent.length >= RATE_MAX) {
    rateBuckets.set(ip, recent);
    return true;
  }
  recent.push(now);
  rateBuckets.set(ip, recent);
  return false;
}

function extractTurnstileToken(payload) {
  const token = payload.turnstile_token || payload['cf-turnstile-response'];
  delete payload.turnstile_token;
  delete payload['cf-turnstile-response'];
  return token;
}

function validPayload(payload) {
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
    return 'invalid_payload';
  }

  for (const [key, value] of Object.entries(payload)) {
    if (!ALLOWED_FIELDS.has(key)) return 'unexpected_field';
    if (typeof value !== 'string') return 'invalid_field_type';
    if (value.length > MAX_FIELD_LENGTH) return 'field_too_long';
  }

  if (payload._gotcha && payload._gotcha.trim()) return 'spam_detected';

  const source = (payload.source || '').trim();
  const required = SOURCES[source];
  if (!required) return 'invalid_source';

  for (const key of required) {
    if (typeof payload[key] !== 'string' || !payload[key].trim()) {
      return 'missing_required_fields';
    }
  }

  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(payload.email.trim())) {
    return 'invalid_email';
  }

  if (!/^PSQ-\d{8}-[A-Za-z0-9_-]+$/.test(payload.client_reference.trim())) {
    return 'invalid_reference';
  }

  if (source === 'contact_pathway') {
    if (!AGE_BANDS.has(payload.age_band.trim())) return 'invalid_age_band';
    if (!GOALS.has(payload.goal.trim())) return 'invalid_goal';
    if (!PURCHASE_PATHS.has(payload.purchase_path.trim())) return 'invalid_purchase_path';
  }

  if (source === 'school_quote' && !/^[1-9]\d{0,5}$/.test(payload.learner_count.trim())) {
    return 'invalid_learner_count';
  }

  const submittedAt = Date.parse(payload.submitted_at);
  if (!Number.isFinite(submittedAt)) {
    return 'invalid_submission_timing';
  }

  const ageMs = Date.now() - submittedAt;
  if (ageMs < MIN_FORM_AGE_MS) {
    return 'invalid_submission_timing';
  }

  if (ageMs > MAX_FORM_AGE_MS) {
    return 'stale_submission';
  }

  return null;
}

function turnstileHostnames(env) {
  return new Set(
    String(env.TURNSTILE_HOSTNAMES || '')
      .split(',')
      .map((hostname) => hostname.trim().toLowerCase())
      .filter(Boolean)
  );
}

async function verifyTurnstile(token, action, request, env, fetchImpl) {
  if (typeof token !== 'string' || token.length === 0 || token.length > 2048) {
    return 'verification_failed';
  }

  const hostnames = turnstileHostnames(env);
  if (hostnames.size === 0) return 'missing_env_turnstile_hostnames';

  let result;
  try {
    const response = await fetchImpl(SITEVERIFY_URL, {
      method: 'POST',
      headers: { 'content-type': 'application/x-www-form-urlencoded' },
      signal: AbortSignal.timeout(10_000),
      body: new URLSearchParams({
        secret: env.TURNSTILE_SECRET_KEY.trim(),
        response: token,
        remoteip: clientIp(request)
      }).toString()
    });
    if (!response.ok) return 'verification_failed';
    result = await response.json();
  } catch {
    return 'verification_failed';
  }

  if (
    !result ||
    result.success !== true ||
    result.action !== action ||
    !hostnames.has(String(result.hostname || '').toLowerCase())
  ) {
    return 'verification_failed';
  }

  return null;
}

function buildNotification(payload, env) {
  const lines = [
    `Reference: ${payload.client_reference.trim()}`,
    `Source: ${payload.source.trim()}`,
    `Adult: ${payload.adult_name.trim()}`,
    `Email: ${payload.email.trim()}`
  ];

  if (payload.source === 'contact_pathway') {
    lines.push(
      `Age band: ${payload.age_band.trim()}`,
      `Goal: ${payload.goal.trim()}`,
      `Purchase path: ${payload.purchase_path.trim()}`,
      `Organization: ${(payload.organization || '').trim()}`
    );
  } else {
    lines.push(
      `Organization: ${payload.organization.trim()}`,
      `Grade band: ${payload.grade_band.trim()}`,
      `Interest: ${payload.interest.trim()}`,
      `Learner count: ${payload.learner_count.trim()}`,
      `Timeline: ${payload.timeline.trim()}`
    );
  }

  lines.push(`Message: ${payload.message.trim()}`);

  return {
    from: env.RESEND_FROM_EMAIL.trim(),
    to: [env.OPERATIONS_EMAIL.trim()],
    subject: `Preparation Station request ${payload.client_reference.trim()}`,
    reply_to: payload.email.trim(),
    text: lines.join('\n')
  };
}

async function notify(payload, env, fetchImpl) {
  const response = await fetchImpl(RESEND_URL, {
    method: 'POST',
    headers: {
      authorization: `Bearer ${env.RESEND_API_KEY.trim()}`,
      'content-type': 'application/json'
    },
    body: JSON.stringify(buildNotification(payload, env))
  });

  if (!response.ok) {
    throw new Error(`notification_delivery_failed:${response.status}`);
  }
}

async function handleRequest(request, env, deps = {}) {
  const fetchImpl = deps.fetchImpl || fetch;
  const envError = validateEnv(env);
  if (envError) {
    return reject(500, envError);
  }

  if (request.method === 'OPTIONS') {
    if (!validOrigin(request, env.ALLOWED_ORIGIN)) {
      return reject(403, 'origin_not_allowed');
    }
    return new Response(null, {
      status: 204,
      headers: corsHeaders(env.ALLOWED_ORIGIN)
    });
  }

  if (request.method !== 'POST') {
    return reject(405, 'method_not_allowed');
  }

  const extra = originHeaders(env.ALLOWED_ORIGIN);

  if (!validOrigin(request, env.ALLOWED_ORIGIN)) {
    return reject(403, 'origin_not_allowed', extra);
  }

  if (rateLimited(clientIp(request))) {
    return reject(429, 'rate_limit', extra);
  }

  if (!request.headers.get('content-type')?.toLowerCase().startsWith('application/json')) {
    return reject(415, 'json_required', extra);
  }

  const claimedLength = Number(request.headers.get('content-length') || 0);
  if (Number.isFinite(claimedLength) && claimedLength > MAX_BODY_BYTES) {
    return reject(413, 'body_too_large', extra);
  }

  let raw;
  try {
    raw = await request.text();
  } catch {
    return reject(400, 'body_unreadable', extra);
  }

  if (new TextEncoder().encode(raw).byteLength > MAX_BODY_BYTES) {
    return reject(413, 'body_too_large', extra);
  }

  let payload;
  try {
    payload = JSON.parse(raw);
  } catch {
    return reject(400, 'invalid_json', extra);
  }

  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
    return reject(400, 'invalid_payload', extra);
  }

  const token = extractTurnstileToken(payload);
  const action = typeof payload.source === 'string' ? payload.source.trim() : '';
  const turnstileError = await verifyTurnstile(token, action, request, env, fetchImpl);
  if (turnstileError) {
    return reject(403, turnstileError, extra);
  }

  const payloadError = validPayload(payload);
  if (payloadError) {
    return reject(400, payloadError, extra);
  }

  try {
    await notify(payload, env, fetchImpl);
  } catch (error) {
    console.error(JSON.stringify({ event: 'notify_failed', status: 'intake_unavailable' }));
    return reject(503, 'intake_unavailable', extra);
  }

  return json({ ok: true, reference: payload.client_reference.trim() }, 202, extra);
}

export default {
  async fetch(request, env) {
    return handleRequest(request, env);
  }
};

export {
  handleRequest,
  resetRateLimitForTests,
  validOrigin,
  validPayload,
  validateEnv,
  extractTurnstileToken
};
