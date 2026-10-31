# Project state

Updated: 2026-10-31 UTC
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
Git author identity is configured as Ariftia. Coolify deployment preparation is in
progress; the dashboard origin is needed to locate the Madeena project. A saved
deployment token is available through the local credential file; its value is not
recorded here. No Coolify resources have been changed.

Remaining: Coolify target identification/deployment, browser verification, and
native clinical terminology review.
