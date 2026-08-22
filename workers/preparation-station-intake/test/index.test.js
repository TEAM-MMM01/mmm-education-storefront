import assert from 'node:assert/strict';
import test from 'node:test';
import { constantTimeEqual, validPayload, validOrigin } from '../src/index.js';

test('constantTimeEqual accepts equal values and rejects unequal values', () => {
  assert.equal(constantTimeEqual('same', 'same'), true);
  assert.equal(constantTimeEqual('same', 'different'), false);
  assert.equal(constantTimeEqual('same', ''), false);
});

test('validOrigin requires exact configured origin', () => {
  const request = new Request('https://worker.example', {
    headers: { origin: 'https://preparationstation.example' }
  });
  assert.equal(validOrigin(request, 'https://preparationstation.example'), true);
  assert.equal(validOrigin(request, 'https://evil.example'), false);
});

test('validPayload accepts a valid minimal inquiry', () => {
  const result = validPayload({
    adult_name: 'Adult Example',
    email: 'adult@example.com',
    client_reference: 'PSQ-20260821-demo1',
    submitted_at: new Date(Date.now() - 2000).toISOString(),
    _gotcha: ''
  });
  assert.equal(result, null);
});

test('validPayload rejects unexpected fields, honeypot, and invalid references', () => {
  const base = {
    adult_name: 'Adult Example',
    email: 'adult@example.com',
    client_reference: 'PSQ-20260821-demo1',
    submitted_at: new Date(Date.now() - 2000).toISOString(),
    _gotcha: ''
  };

  assert.equal(validPayload({ ...base, card_number: '1234' }), 'unexpected_field');
  assert.equal(validPayload({ ...base, _gotcha: 'bot' }), 'spam_detected');
  assert.equal(validPayload({ ...base, client_reference: 'not-valid' }), 'invalid_reference');
  assert.equal(validPayload({ ...base, email: 'not-an-email' }), 'invalid_email');
});
