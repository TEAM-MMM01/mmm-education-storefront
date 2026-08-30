const MAX_BODY_BYTES = 16384;
const MIN_FORM_AGE_MS = 1500;
const MAX_FORM_AGE_MS = 1000 * 60 * 60 * 24;
const MAX_FIELD_LENGTH = 2000;

const ALLOWED_FIELDS = new Set([
  '_gotcha',
  'adult_name',
  'cart_items',
  'client_reference',
  'email',
  'internal_owner',
  'notes',
  'program',
  'source',
  'submitted_at'
]);

const REQUIRED_FIELDS = ['adult_name', 'email', 'client_reference', 'submitted_at'];

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

function constantTimeEqual(left, right) {
  if (typeof left !== 'string' || typeof right !== 'string' || left.length !== right.length) {
    return false;
  }

  let diff = 0;
  for (let i = 0; i < left.length; i += 1) {
    diff |= left.charCodeAt(i) ^ right.charCodeAt(i);
  }
  return diff === 0;
}

function validOrigin(request, expectedOrigin) {
  if (typeof expectedOrigin !== 'string' || !expectedOrigin) return false;
  return request.headers.get('origin') === expectedOrigin;
}

function corsHeaders(origin) {
  return {
    'access-control-allow-origin': origin,
    'access-control-allow-methods': 'POST, OPTIONS',
    'access-control-allow-headers': 'content-type, x-intake-secret',
    'access-control-max-age': '600',
    vary: 'Origin'
  };
}

function validateEnv(env) {
  const required = [
    'ALLOWED_ORIGIN',
    'INTAKE_SHARED_SECRET',
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

function validPayload(payload) {
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
    return 'invalid_payload';
  }

  for (const key of REQUIRED_FIELDS) {
    if (typeof payload[key] !== 'string' || !payload[key].trim()) {
      return 'missing_required_fields';
    }
  }

  for (const [key, value] of Object.entries(payload)) {
    if (!ALLOWED_FIELDS.has(key)) return 'unexpected_field';
    if (typeof value !== 'string') return 'invalid_field_type';
    if (value.length > MAX_FIELD_LENGTH) return 'field_too_long';
  }

  if (payload._gotcha && payload._gotcha.trim()) return 'spam_detected';

  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(payload.email.trim())) {
    return 'invalid_email';
  }

  if (!/^PSQ-\d{8}-[A-Za-z0-9_-]+$/.test(payload.client_reference.trim())) {
    return 'invalid_reference';
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

function buildNotification(payload, env) {
  return {
    from: env.RESEND_FROM_EMAIL.trim(),
    to: [env.OPERATIONS_EMAIL.trim()],
    subject: `Preparation Station request ${payload.client_reference.trim()}`,
    reply_to: payload.email.trim(),
    text: [
      `Reference: ${payload.client_reference.trim()}`,
      `Adult: ${payload.adult_name.trim()}`,
      `Email: ${payload.email.trim()}`,
      `Program: ${(payload.program || '').trim()}`,
      `Cart: ${(payload.cart_items || '').trim()}`,
      `Owner: ${(payload.internal_owner || '').trim()}`,
      `Source: ${(payload.source || '').trim()}`,
      `Notes: ${(payload.notes || '').trim()}`
    ].join('\n')
  };
}

async function notify(payload, env) {
  const response = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: {
      authorization: `Bearer ${env.RESEND_API_KEY.trim()}`,
      'content-type': 'application/json'
    },
    body: JSON.stringify(buildNotification(payload, env))
  });

  if (!response.ok) {
    const details = await response.text().catch(() => '');
    throw new Error(`notification_delivery_failed:${response.status}:${details.slice(0, 500)}`);
  }
}

export default {
  async fetch(request, env) {
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

    if (!validOrigin(request, env.ALLOWED_ORIGIN)) {
      return reject(403, 'origin_not_allowed', {
        'access-control-allow-origin': env.ALLOWED_ORIGIN,
        vary: 'Origin'
      });
    }

    if (!request.headers.get('content-type')?.toLowerCase().startsWith('application/json')) {
      return reject(415, 'json_required', {
        'access-control-allow-origin': env.ALLOWED_ORIGIN,
        vary: 'Origin'
      });
    }

    const claimedLength = Number(request.headers.get('content-length') || 0);
    if (Number.isFinite(claimedLength) && claimedLength > MAX_BODY_BYTES) {
      return reject(413, 'body_too_large', {
        'access-control-allow-origin': env.ALLOWED_ORIGIN,
        vary: 'Origin'
      });
    }

    let raw;
    try {
      raw = await request.text();
    } catch {
      return reject(400, 'body_unreadable', {
        'access-control-allow-origin': env.ALLOWED_ORIGIN,
        vary: 'Origin'
      });
    }

    if (new TextEncoder().encode(raw).byteLength > MAX_BODY_BYTES) {
      return reject(413, 'body_too_large', {
        'access-control-allow-origin': env.ALLOWED_ORIGIN,
        vary: 'Origin'
      });
    }

    if (!constantTimeEqual(request.headers.get('x-intake-secret') || '', env.INTAKE_SHARED_SECRET.trim())) {
      return reject(401, 'unauthorized', {
        'access-control-allow-origin': env.ALLOWED_ORIGIN,
        vary: 'Origin'
      });
    }

    let payload;
    try {
      payload = JSON.parse(raw);
    } catch {
      return reject(400, 'invalid_json', {
        'access-control-allow-origin': env.ALLOWED_ORIGIN,
        vary: 'Origin'
      });
    }

    const payloadError = validPayload(payload);
    if (payloadError) {
      return reject(400, payloadError, {
        'access-control-allow-origin': env.ALLOWED_ORIGIN,
        vary: 'Origin'
      });
    }

    try {
      await notify(payload, env);
    } catch (error) {
      console.error('notify_failed', String(error?.message || error));
      return reject(503, 'intake_unavailable', {
        'access-control-allow-origin': env.ALLOWED_ORIGIN,
        vary: 'Origin'
      });
    }

    return json(
      { ok: true, reference: payload.client_reference.trim() },
      202,
      {
        'access-control-allow-origin': env.ALLOWED_ORIGIN,
        vary: 'Origin'
      }
    );
  }
};

export {
  constantTimeEqual,
  validOrigin,
  validPayload,
  validateEnv
};
