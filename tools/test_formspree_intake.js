'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const intake = require(path.join(root, 'store', 'formspree-intake.js'));
const config = JSON.parse(fs.readFileSync(path.join(root, 'config', 'formspree-intake.json'), 'utf8'));
const contact = fs.readFileSync(path.join(root, 'contact.html'), 'utf8');
const source = fs.readFileSync(path.join(root, 'src', 'info', 'contact.html'), 'utf8');
const docs = fs.readFileSync(path.join(root, 'docs', 'workflow', 'FORMSPREE_INTAKE_SETUP.md'), 'utf8');

assert.equal(config.enabled, false);
assert.equal(config.PATHWAY_RECOMMENDATION_FORMSPREE_ID, '');
assert.equal(config.SCHOOL_DISTRICT_QUOTE_FORMSPREE_ID, '');
assert.equal(config.TURNSTILE_SITE_KEY, '');
assert.equal(config.restricted_domain, 'preparationstation.org');
assert.equal(intake.isReady(config), false);
assert.equal(intake.endpoint(''), '');
assert.equal(intake.endpoint('abcdEFGH'), 'https://formspree.io/f/abcdEFGH');
assert.equal(intake.isFormId('bad id'), false);
assert.equal(intake.isFormId('[public form ID]'), false);
assert.equal(intake.isSitekey('secret-key-value'), false);
assert.equal(intake.isSitekey('[public site key]'), false);

assert.equal(
  intake.isReady({
    ...config,
    enabled: true,
    PATHWAY_RECOMMENDATION_FORMSPREE_ID: '',
    SCHOOL_DISTRICT_QUOTE_FORMSPREE_ID: 'moqjwvab',
    TURNSTILE_SITE_KEY: '0x4AAAAAAAABCDEFGH',
  }),
  false,
  'empty pathway ID must keep forms disabled',
);

const ready = {
  ...config,
  enabled: true,
  PATHWAY_RECOMMENDATION_FORMSPREE_ID: 'xpzgkqyz',
  SCHOOL_DISTRICT_QUOTE_FORMSPREE_ID: 'moqjwvab',
  TURNSTILE_SITE_KEY: '0x4AAAAAAAABCDEFGH',
};
assert.equal(intake.isReady(ready), true);

assert.match(intake.SUCCESS, /Request received/);
assert.match(intake.FAILURE, /could not send your request/);
assert.match(source, /Please do not include student records, health information, payment details, or program-account credentials\./);
assert.match(source, /__FORMSPREE_READY__/);
assert.match(source, /name="_gotcha"/);
assert.match(docs, /Restrict to Domain.*preparationstation\.org/s);
assert.doesNotMatch(source, /TURNSTILE_SECRET/);
assert.doesNotMatch(contact, /TURNSTILE_SECRET/);
assert.match(contact, /data-formspree-ready="false"/);
assert.doesNotMatch(contact, /https:\/\/formspree\.io\/f\/[A-Za-z0-9]+/);
assert.doesNotMatch(contact, /action="mailto:/);
assert.match(contact, /store\/formspree-intake\.js/);
assert.match(contact, /id="contact-name"/);
assert.match(contact, /id="quote-organization"/);
assert.match(contact, /data-turnstile-slot/);
for (const forbidden of ['ssn', 'student_record', 'payment', 'password', 'account_number', 'odyssey_password']) {
  assert.doesNotMatch(contact, new RegExp('name="' + forbidden + '"'));
}

console.log('Formspree intake tests passed.');
