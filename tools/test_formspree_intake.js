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

assert.equal(config.enabled, true);
assert.equal(config.PATHWAY_RECOMMENDATION_FORMSPREE_ID, 'xbgjyqzw');
assert.equal(config.SCHOOL_DISTRICT_QUOTE_FORMSPREE_ID, 'xoeqwykd');
assert.equal(config.TURNSTILE_SITE_KEY, '');
assert.equal(config.restricted_domain, 'preparationstation.org');
assert.equal(intake.isReady(config), true);
assert.equal(intake.endpoint('xbgjyqzw'), 'https://formspree.io/f/xbgjyqzw');
assert.equal(intake.isFormId('bad id'), false);
assert.equal(intake.isFormId('[public form ID]'), false);
assert.equal(
  intake.isReady({
    ...config,
    enabled: true,
    PATHWAY_RECOMMENDATION_FORMSPREE_ID: '',
  }),
  false,
  'empty pathway ID must keep forms disabled',
);

assert.match(intake.SUCCESS, /Request received/);
assert.match(intake.FAILURE, /could not send your request/);
assert.match(source, /Please do not include student records, health information, payment details, or program-account credentials\./);
assert.match(source, /name="form_type"/);
assert.match(source, /name="_subject"/);
assert.match(source, /name="_gotcha"/);
assert.match(source, />Submit request</);
assert.match(source, />Request quote</);
assert.match(source, /aria-live="assertive"/);
assert.match(source, /aria-live="polite"/);
assert.match(docs, /Restrict to Domain.*preparationstation\.org/s);
assert.doesNotMatch(source, /TURNSTILE_SECRET/);
assert.doesNotMatch(contact, /TURNSTILE_SECRET/);
assert.match(contact, /data-formspree-ready="true"/);
assert.match(contact, /https:\/\/formspree\.io\/f\/xbgjyqzw/);
assert.match(contact, /https:\/\/formspree\.io\/f\/xoeqwykd/);
assert.doesNotMatch(contact, /action="mailto:/);
assert.match(contact, /method="POST"/i);
assert.match(contact, /store\/formspree-intake\.js/);
assert.match(contact, /id="contact-topic"/);
assert.match(contact, /id="quote-role"/);
assert.match(contact, /name="products_skus"/);
for (const forbidden of ['ssn', 'student_record', 'payment', 'password', 'account_number', 'odyssey_password']) {
  assert.doesNotMatch(contact, new RegExp('name="' + forbidden + '"'));
}

console.log('Formspree intake tests passed.');
