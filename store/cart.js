/* Client-side quote cart and disabled-by-default request intake. The funded
   path creates a request record only; it never collects payment. A validated
   request intake endpoint in config/request-intake.json is required before the
   online request button can be enabled. */
(function () {
  const KEY = 'preparation_station_cart_v1';
  const LEGACY_KEY = 'mmm_cart_v1';
  const REQUEST_CONFIG_URL = '../config/request-intake.json';
  const WORKER_ENDPOINT = /^https:\/\/worker\.example\/intake$/;
  const REQUEST_FIELDS = [
    '_gotcha',
    'adult_name',
    'cart_items',
    'client_reference',
    'email',
    'internal_owner',
    'notes',
    'program',
    'source',
    'submitted_at',
  ];
  const ALLOWED_PROGRAMS = ['TEFA', 'PDSES/ClassWallet', 'Self-pay', 'Other / not sure'];

  const PRODUCTS = {
    'PS-PR-101': { name: 'Home & Repair Tool Roll', price: null, dept: 'Practical & Trade' },
    'PS-PR-102': { name: 'Money & First Job Kit', price: null, dept: 'Practical & Trade' },
    'PS-PR-103': { name: 'Kitchen & Provision Kit', price: null, dept: 'Practical & Trade' },
    'PS-SC-201': { name: 'Situation Handling Deck', price: null, dept: 'Situation Handling & Self-Command' },
    'PS-SC-202': { name: 'Focus & Energy System', price: null, dept: 'Situation Handling & Self-Command' },
    'PS-SC-203': { name: 'Self-Advocacy Workbook', price: null, dept: 'Situation Handling & Self-Command' },
    'PS-SC-204': { name: 'Interview & First Job Prep Kit', price: null, dept: 'Situation Handling & Self-Command' },
    'PS-SC-205': { name: 'Adulting Launch Kit', price: null, dept: 'Situation Handling & Self-Command' },
    'PS-CS-301': { name: 'Graphic Design Bench', price: null, dept: 'Design & Motion Studio' },
    'PS-CS-302': { name: 'Motion & Video Kit', price: null, dept: 'Design & Motion Studio' },
    'PS-CS-303': { name: 'Skill-to-Income Pack', price: null, dept: 'Design & Motion Studio' },
    'PS-AT-401': { name: 'AI Literacy Bench Kit', price: null, dept: 'AI & Emerging Tech Bench' },
    'PS-AT-402': { name: 'Electronics & Robotics Starter', price: null, dept: 'AI & Emerging Tech Bench' },
    'PS-AT-403': { name: '3D Design & Fabrication Intro', price: null, dept: 'AI & Emerging Tech Bench' },
    'PS-HS-501': { name: 'Weekly Evidence Binder', price: null, dept: 'Homeschool Essentials' },
    'PS-HS-502': { name: 'Homeschool Assessment & Portfolio Kit', price: null, dept: 'Homeschool Essentials' },
    'PS-HS-503': { name: 'Daily Supply Restock Box', price: null, dept: 'Homeschool Essentials' },
    'PS-HS-504': { name: 'Art & Craft Foundations Kit', price: null, dept: 'Homeschool Essentials' },
  };

  const requestState = {
    config: null,
    configStatus: 'loading',
    inFlight: false,
    needsRetry: false,
    receipt: null,
    completed: false,
  };
