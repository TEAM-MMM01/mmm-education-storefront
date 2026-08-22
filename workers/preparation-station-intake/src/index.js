const MAX_BODY_BYTES = 16384;
const MIN_FORM_AGE_MS = 1500;
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

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      'content-type': 'application/json; charset=utf-8',
      'cache-control': 'no-store',
      'x-content-type-options': 'nosniff'
    }
  });
}

function reject(status, code) {
  return json({ ok: false, code }, status);
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
  if (!expectedOrigin) return false;
  return request.headers.get('origin') === expectedOrigin;
}

function validPayload(payload) {
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
    return 'invalid_payload';
  }

  for (const [key, value] of Object.entries(payload)) {
    if (!ALLOWED_FIELDS.has(key)) return 'unexpected_field';
    if (typeof value === 'string' && value.length > MAX_FIELD_LENGTH) return 'field_too_long';
  }

  if (payload._gotcha) return 'spam_detected';
  if (!payload.adult_name || !payload.email || !payload.client_reference) return 'missing_required_fields';
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(payload.email)) return 'invalid_email';
  if (!/^PSQ-\d{8}-[A-Za-z0-9_-]+$/.test(payload.client_reference)) return 'invalid_reference';

  const submittedAt = Date.parse(payload.submitted_at || '');
  if (!Number.isFinite(submittedAt) || Date.now() - submittedAt < MIN_FORM_AGE_MS) {
    return 'invalid_submission_timing';
  }

  return null;
}

async function notify(payload, env) {
  if (!env.RESEND_API_KEY || !env.OPERATIONS_EMAIL || !env.RESEND_FROM_EMAIL) {
    throw new Error('notification_not_configured');
  }

  const message = {
    from: env.RESEND_FROM_EMAIL,
    to: [env.OPERATIONS_EMAIL],
    subject: `Preparation Station request ${payload.client_reference}`,
    text: [
      `Reference: ${payload.client_reference}`,
      `Adult: ${payload.adult_name}`,
      `Email: ${payload.email}`,
      `Program: ${payload.program || ''}`,
      `Cart: ${payload.cart_items || ''}`,
      `Notes: ${payload.notes || ''}`
    ].join('\n')
  };

  const response = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: {
      authorization: `Bearer ${env.RESEND_API_KEY}`,
      'content-type': 'application/json'
    },
    body: JSON.stringify(message)
  });

  if (!response.ok) {
    throw new Error('notification_delivery_failed');
  }
}

export default {
  async fetch(request, env) {
    if (request.method === 'OPTIONS') {
      if (!validOrigin(request, env.ALLOWED_ORIGIN)) return reject(403, 'origin_not_allowed');
      return new Response(null, {
        status: 204,
        headers: {
          'access-control-allow-origin': env.ALLOWED_ORIGIN,
          'access-control-allow-methods': 'POST, OPTIONS',
          'access-control-allow-headers': 'content-type, x-intake-secret',
          'access-control-max-age': '600',
          vary: 'Origin'
        }
      });
    }

    if (request.method !== 'POST') return reject(405, 'method_not_allowed');
    if (!validOrigin(request, env.ALLOWED_ORIGIN)) return reject(403, 'origin_not_allowed');

    if (!request.headers.get('content-type')?.toLowerCase().startsWith('application/json')) {
      return reject(415, 'json_required');
    }

    const claimedLength = Number(request.headers.get('content-length') || 0);
    if (claimedLength > MAX_BODY_BYTES) return reject(413, 'body_too_large');

    if (!constantTimeEqual(request.headers.get('x-intake-secret'), env.INTAKE_SHARED_SECRET)) {
      return reject(401, 'unauthorized');
    }

    let raw;
    try {
      raw = await request.text();
    } catch {
      return reject(400, 'body_unreadable');
    }

    if (new TextEncoder().encode(raw).byteLength > MAX_BODY_BYTES) {
      return reject(413, 'body_too_large');
    }

    let payload;
    try {
      payload = JSON.parse(raw);
    } catch {
      return reject(400, 'invalid_json');
    }

    const payloadError = validPayload(payload);
    if (payloadError) return reject(400, payloadError);

    try {
      await notify(payload, env);
    } catch {
      return reject(503, 'intake_unavailable');
    }

    return new Response(JSON.stringify({ ok: true, reference: payload.client_reference }), {
      status: 202,
      headers: {
        'content-type': 'application/json; charset=utf-8',
        'cache-control': 'no-store',
        'access-control-allow-origin': env.ALLOWED_ORIGIN,
        vary: 'Origin'
      }
    });
  }
};

export {
  constantTimeEqual,
  validPayload,
  validOrigin
};
