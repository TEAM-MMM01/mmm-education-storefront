# Security Policy

## Supported Versions
This repository tracks a single production branch (`main`). Security fixes are applied there and released via the standard build pipeline.

## Reporting a Vulnerability
Please do not open a public GitHub issue for security vulnerabilities.
Instead, report privately via GitHub's "Report a vulnerability" button on the Security tab, or contact the maintainer directly.

We aim to acknowledge reports within 5 business days and provide a remediation timeline within 10 business days.

## Scope
- Storefront frontend (HTML/CSS/JS)
- Order/tracking request-intake logic (`store/cart.js`, `store/track.js`)
- Orchestration/notification tooling (`tools/orchestration/`, `tools/notifications/`)

## Known Hardening Areas
Path and request-input handling in `tools/orchestration/queue.py` and `tools/notifications/__init__.py` are under active CodeQL review — see the Code Scanning tab for current status.
