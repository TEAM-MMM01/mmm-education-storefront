'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const intake = require(path.join(root, 'store', 'formspree-intake.js'));
const config = JSON.parse(fs.readFileSync(path.join(root, 'config', 'formspree-intake.json'), 'utf8'));
const contact = fs.readFileSync(path.join(root, 'contact.html'), 'utf8');
const source = fs.readFileSync(path.join(root, 'src', 'info', 'contact.html'), 'utf8');

assert.equal(config.enabled, false);
assert.equal(config.pathway_form_id, '');
assert.equal(config.quote_form_id, '');
assert.equal(config.turnstile_sitekey, '');
assert.equal(intake.isReady(config), false);
assert.equal(intake.endpoint(''), '');
assert.equal(intake.endpoint('abcdEFGH'), 'https://formspree.io/f/abcdEFGH');
assert.equal(intake.isFormId('bad id'), false);
assert.equal(intake.isSitekey('secret-key-value'), false);

const ready = {
  ...config,
  enabled: true,
  pathway_form_id: 'xpzgkqyz',
  quote_form_id: 'moqjwvab',
  turnstile_sitekey: '0x4AAAAAAAABCDEFGH',
};
assert.equal(intake.isReady(ready), true);

assert.match(intake.SUCCESS, /Request received/);
assert.match(intake.FAILURE, /could not send your request/);
assert.match(source, /Please do not include student records, health information, payment details, or program-account credentials\./);
assert.match(source, /__FORMSPREE_READY__/);
assert.doesNotMatch(source, /TURNSTILE_SECRET/);
assert.doesNotMatch(contact, /TURNSTILE_SECRET/);
assert.match(contact, /data-formspree-ready="false"/);
assert.doesNotMatch(contact, /https:\/\/formspree\.io\/f\/[A-Za-z0-9]+/);
assert.doesNotMatch(contact, /mailto:.*form/);
assert.match(contact, /store\/formspree-intake\.js/);
assert.match(contact, /id="contact-name"/);
assert.match(contact, /id="quote-organization"/);
for (const forbidden of ['ssn', 'student_record', 'payment', 'password', 'account_number', 'odyssey_password']) {
  assert.doesNotMatch(contact, new RegExp('name="' + forbidden + '"'));
}

console.log('Formspree intake tests passed.');
