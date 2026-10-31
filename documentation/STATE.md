# Project state

Updated: 2026-10-31 UTC
Production runner: the upload guard remediation at `44dfaf2b` passed production
run `41205935652`. All 25 baseline local tests also pass; that bounded correction
is accepted. The successor task is `.agents/tasks/deploy-indonesian-source.md`
at `dd26a76cd97e110ad256c10c1307be260ebcd139`.

The updated workflow sets `RIS_BUILD_SOURCE=true` and `SIRIUS_LANGUAJE=id`.
Updates build the repository frontend/backend before changing containers, verify
runtime language settings/dictionaries, and preserve the existing project,
storage and exact-image rollback. All 32 isolated/local parser tests, Actions
syntax and both Indonesian dictionary validators pass. Implementation `0dfdf9faa57f78204504f7a329c87a05222fcd93` is accepted after
source review and those checks. It was pushed to `origin/main`; production run
`41220372005` failed during frontend build after backend build succeeded. No
running-container mutation occurred. Build-only diagnostics now retain the last
60 lines; Compose/runtime diagnostics remain private. Remediation task revision:
`cf03dbbe7802e27746320e50f48b6b152c9c39ab`. All 33 local tests pass; retry pending.
See [Runner operations](10_runner_updates_and_rollback.md).

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
