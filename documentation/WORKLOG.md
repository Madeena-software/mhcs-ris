# Worklog

## 2026-10-31 UTC — Indonesian language support

- Model: Not available.
- Request: Clone `Madeena-software/mhcs-ris` into `repos` and add Indonesian support on a new branch.
- Change: Created `feature/indonesian-language` from `origin/develop`; added both `id.json` dictionaries using existing loaders. Included the existing CKEditor Indonesian asset in build/test scripts so `ui: "id"` can translate its toolbar.
- Verification: Existing i18n validator passes for both dictionaries. Additional checks passed for all 2,144 strings: nonempty values, matching placeholders, HTML tags, and boundary whitespace.
- Runtime evidence: Frontend initializer normalizes `id-ID` and loads Indonesian labels. Backend resolves `id`/`ID`, preserves English fallback, and interpolates report signature placeholders. The CKEditor asset registers its Indonesian dictionary. Duplicate-key and documentation-link checks pass.
- Build setup: `npm ci --legacy-peer-deps --no-audit --no-fund` installed 1,055 frontend packages. The initial build could not start without dependencies. After installation, `npm run build` reached bundle generation but made no further progress for several minutes and was interrupted (exit 130); production build remains unverified.
- Type checking: `./node_modules/.bin/tsc --noEmit -p tsconfig.app.json` inside `frontend` passed (exit 0). `git diff --check` passed.
- Documentation: Added configuration/verification instructions, supported-language README entry, backend example comment, and current state.
- Limits: No browser verification. Native clinical terminology review remains pending. No configured Git author identity; no commit or push.

## 2026-10-31 UTC — Contextual translation review

- Model: Not available.
- Request: Ensure translations reflect application context rather than literal word substitution.
- Evidence: Inspected sign-in and identity fields, equipment slot forms, doctor/report workload lists, report overview/conclusion sections, report email construction, mail resend actions, patient-call displays, procedure reporting deadlines, and PET-CT MBq/mCi fields/calculation. Compared clinical wording with SATUSEHAT and BAPETEN sources linked in the setup guide.
- Changes: Corrected 120 frontend and five backend entries. Kept overview `Ringkasan` distinct from clinical conclusion `Kesimpulan`, identity numbers distinct from attachments, urgent scheduling distinct from emergency inpatient care, and radiological activity distinct from absorbed dose. Corrected the report email subject and replaced two hard-coded Spanish unit labels with existing i18n keys.
- Verification: Both existing dictionary validators pass. All 2,144 entries retain key structure/order, string types, placeholders, HTML tags, and boundary whitespace. Focused assertions pass for the context distinctions above.
- Template verification: `./node_modules/.bin/ngc -p tsconfig.app.json --noEmit` inside `frontend` passed (exit 0). Height/weight translation keys exist in all ten locale dictionaries. `git diff --check` passes.
- Documentation: Added a terminology table with implementation evidence and reasons to the Indonesian setup guide; updated current state.
- Limits: Native clinical-user and rendered browser reviews remain pending. Production build previously timed out; no new successful production build is claimed. Changes remain uncommitted because Git author identity is absent.

## 2026-10-31 UTC — Coolify deployment preparation

- Model: Not available.
- Request: Deploy the Indonesian-language branch to the Madeena project in Coolify.
- Preparation: Verified the configured Git identity and GitHub account. Inspected Docker entrypoints and templates: `SIRIUS_LANGUAJE=id` enables Indonesian for the frontend, calendar, editor, and backend. Added Docker/Coolify instructions and the language code to the environment example's supported-language comment.
- Verification: Both dictionary validators and `git diff --check` pass. Angular template compilation passed earlier. A production build retry outside the sandbox is in progress; its outcome is not yet known.
- Deployment status: No Coolify changes made. A saved token exists, but the dashboard URL is not configured; requested it from the user to identify the Madeena project and preserve its existing resources.
- Final local verification: The production build passed outside the sandbox using `NG_BUILD_MAX_WORKERS=2 timeout 240 npm run build -- --progress=false` (exit 0, build hash `c75a252ed5dbb4f7`, about 170 seconds). Existing report form CSS produced a 413-byte warning-budget overrun; no build errors occurred.
- Git delivery: Source commit `4f709855` authored by Ariftia was pushed to `origin/feature/indonesian-language`. Coolify rollout remains pending the dashboard URL; no deployment success is claimed.
