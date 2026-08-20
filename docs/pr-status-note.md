Updated the branch so the Pages release artifact now passes boundary and link smoke checks.

Completed:
- Fixed the track page contact link for Pages-safe relative navigation.
- Included printable resource pages in the release allowlist.
- Cleaned up the release builder so the artifact shape matches policy.

Current status:
- Pages release artifact boundary and link smoke checks pass.
- Remaining messages are expected release-governance blockers in config/pages-release.json and related state, not storefront artifact or link failures.

Deployment is still intentionally blocked until the verified TEFA SKU, request intake, Formspree endpoint, and request backend verification fields are completed.
