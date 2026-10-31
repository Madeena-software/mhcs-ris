# Project state

Updated: 2026-10-31 UTC
Latest workflow remediation: run `41194024495` passed helper tests but stopped
before deployment at the unmounted-upload guard. The guard counted the tracked
zero-byte `.gitkeep` placeholder as uploaded data. The helper now ignores only
empty regular `.gitkeep` files; real files and symlinks remain protected.
All 25 local tests pass, including actual Node probe fixtures. No production
rerun of this correction has been dispatched; start a new run from `main` after
the fix is pushed rather than retrying the old commit.

Current maintenance: production-runner deployment updates and rollback are
implemented locally in `.github/workflows/deploy-docker-compose.yml` and
`scripts/deploy_compose.py`. The workflow reuses the existing Compose project and
mounts, records exact recovery images/configuration, checks readiness, and supports
automatic/manual recovery. It uses a separate checkout and private recovery state.
See [Runner operations](10_runner_updates_and_rollback.md). Isolated transaction
tests and real Compose configuration parsing pass; actionlint passes with the
existing custom `production` runner label configured. No production workflow
dispatch or live rollback drill has been performed. Changes are not pushed.

Current task: Indonesian language support on `feature/indonesian-language`, based on `origin/develop`.

Implemented: complete Indonesian frontend/backend dictionaries and registration of
the existing Indonesian CKEditor asset in Angular build/test scripts. Configuration
and verification instructions are in [Indonesian language setup](08_indonesian_language.md).
Context review corrected 120 frontend and five backend entries after examining
their screens and data fields. Decisions and terminology references are recorded
in the setup document. The report overview's height/weight units now use existing
translation keys.

Verification: both dictionaries pass the existing structural validator. Placeholder,
HTML-tag, nonempty-string, and boundary-whitespace checks pass for 2,023 frontend
strings and 121 backend strings.

Runtime smoke checks pass for frontend initialization with `id-ID`, backend `id`/`ID`
loading, English fallback, report interpolation, and CKEditor Indonesian registration.
Frontend dependencies were installed with `npm ci --legacy-peer-deps --no-audit --no-fund`.
TypeScript checking passed with `./node_modules/.bin/tsc --noEmit -p tsconfig.app.json`
inside `frontend`. `git diff --check` passed.
After the context corrections, Angular template compilation also passed with
`./node_modules/.bin/ngc -p tsconfig.app.json --noEmit` inside `frontend`. All 2,144
dictionary entries still pass structural/placeholder checks; assertions confirm
that overview/conclusion, identity/attachment, and urgency/emergency wording stay distinct.

Production verification: `NG_BUILD_MAX_WORKERS=2 timeout 240 npm run build -- --progress=false`
passed outside the sandbox (exit 0, about 170 seconds). The existing report form CSS
exceeds its warning budget by 413 bytes; the build completed successfully.

Delivery: source commit `4f709855` is pushed to `origin/feature/indonesian-language`.
Git author identity is configured as Ariftia. Local Coolify 4.5.3 is on port 8000.
`Madeena` → `production` → `MHCS RIS Indonesia` is deployed from `d8611f01` on the
local ARM64 server, using [Local Coolify deployment](09_coolify_deployment.md).
Application URL: `http://localhost:4000`, bound only to `127.0.0.1`.

Live verification: all three containers are healthy. Frontend, contextual
dictionary, and proxied API return HTTP 200. App/calendar/editor settings are `id`;
backend validation messages are Indonesian. The seeded superuser password was
initialized, sign-in succeeded, and an authenticated database read passed.
Login details are in `/home/ubuntu/.config/coolify/mhcs-ris-access.json` (mode 0600).
Generated secrets are absent from the image metadata/history. Database and upload
volumes are mounted; all previously existing applications remain healthy.

Remaining: rendered browser verification and native clinical terminology review.
PACS/Wezen integrations and a scheduled backup job are not configured by this
deployment. No public domain was added.
