# EHTERAF Public Website

The public EHTERAF website is served by the existing FastAPI application. It does not introduce a second backend, authentication system, or database.

## Routes
- / — public homepage
- /about — about EHTERAF
- /academic-services — academic service catalogue
- /technical-services — technical service catalogue
- /portfolio — verified-project placeholder
- /team — verified-team placeholder
- /why-ehteraf — value proposition
- /testimonials — verified-feedback placeholder
- /faq — frequently asked questions
- /contact — contact and request entry point
- /login — existing account sign-in
- /profile — separate account profile page
- /miniapp — existing authenticated Mini App (visual design preserved)

No public navigation or footer link exposes the admin route.

## Authentication handoff
1. Public request CTAs open /login?next=%2Fminiapp.
2. The login page calls the existing POST /api/v1/auth/login endpoint.
3. It verifies the returned token through GET /api/v1/auth/me.
4. The access token is held in tab-scoped sessionStorage under ehteraf_access_token.
5. The browser navigates to /miniapp.
6. The Mini App bootstrap assigns the token to its existing window.__ACADEMIC_BEARER_TOKEN__ integration seam. Its existing API client continues to use the established Bearer flow.
7. /profile independently reads the same session token and requests /api/v1/auth/me.

The login page always redirects successful authentication to /miniapp, as requested. The profile page is a separate URL and does not replace the Mini App destination.

## PWA
- Manifest: /website/static/manifest.webmanifest
- Root-scoped service worker: /service-worker.js
- Offline fallback: /offline
- Cache includes the public shell and static assets only.
- API, admin, and Mini App requests are excluded from service-worker caching.
- iOS installation is explained through Safari's Share → Add to Home Screen flow.
- Native install UI is shown only when the browser exposes beforeinstallprompt; the iOS guide is shown for iPhone/iPad.

## Content governance
Portfolio projects, team biographies, testimonials, contact channels, client counts, and achievements are not fabricated. Empty states explain that verified information will be added when supplied. Academic service messaging explicitly rejects cheating, plagiarism, and misrepresented authorship.

## Configuration still needed
- Official domain (for canonical URLs and production SEO verification).
- Approved logo and final brand assets (current E mark is a replaceable temporary symbol).
- Verified portfolio entries, team profiles, and testimonials.
- Official email, Telegram, WhatsApp, and other contact channels.
- Final copy approval for service scope, turnaround commitments, and any commercial terms.

## Verification and release
Before production release:
1. Run uv sync --locked --all-groups --all-extras.
2. Run uv run --no-sync pytest -q --tb=short.
3. Smoke-test /, all public page routes, /login, /profile, /miniapp, /robots.txt, and /sitemap.xml.
4. Verify login with a non-production account and confirm the Mini App can fetch authenticated endpoints.
5. Test PWA installation on Android/desktop browsers and manual installation on iOS Safari.
6. Test offline fallback and confirm no API responses or user-submitted data enter the cache.
7. Review the site on mobile, tablet, and desktop in both languages and themes.

This branch is not deployed. Merge and production deployment remain separate release decisions.