# Worklog

## 2026-10-31 UTC — Existing production Compose updates and rollback

- Model: Not available.
- Request: Update GitHub deployment automation on the other production server to
  reuse its existing deployment and recover from unsuccessful updates. Coolify is
  excluded. The human authorized implementation and local commits.
- Governing task: `.agents/tasks/update-existing-deployment-with-rollback.md` at
  `27132c55822842c71da9da304d4a5353403c709a`, based on
  `24ff711b145228492bffddaab37ca1081640978b` plus the task publication commit.
- Change: Separate non-cleaning checkout; discover existing Compose identity and
  verify host mounts; preserve implicit volumes and protect unmounted uploads;
  retain exact local images, effective environment, and configuration outside the
  checkout. Add health probes, automatic recovery with failed job status, manual
  rollback, pending recovery records, GitHub concurrency, and a host file lock.
  Remove host Docker daemon reconfiguration from application deployment.
- Compatibility: Keep manual dispatch and the existing runner labels/service
  names. `up -d --build` updates published images because this Compose file has no
  builds. `down` now stops without removing the containers/network/storage.
- Verification: `python3 -B -m unittest discover -s tests -p test_deploy_compose.py`
  passes 20 tests, including real Compose config parsing with literal-dollar
  credentials and mount-path round trips. Failure/recovery, missing snapshots,
  interrupted jobs, service-specific updates, stopped-stack resume, and unsafe
  storage changes use isolated fixtures/fake Docker; no live Docker mutation.
  actionlint 1.7.12 passes with the existing `production` runner label supplied
  through a temporary configuration. Python syntax compilation and diff checks
  pass. Real parser checks found and corrected Compose's escaped-dollar output.
- Intelligence: Fast graph indexing completed, but the new helper was excluded
  and new tests were untracked; coverage checks and direct source review were
  used. No claim of complete graph coverage.
- Limits: No push, deployment, production dispatch, or live rollback drill. Image
  and state retention require disk housekeeping; database restoration/migrations
  are separate operations. Operator instructions are in
  `10_runner_updates_and_rollback.md`.

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

## 2026-10-31 UTC — Local Coolify rollout

- Model: Not available.
- Target: Discovered local Coolify 4.5.3 on port 8000. The token exposes only Root Team, with no Madeena project. Created Madeena and selected its production environment on the existing localhost ARM64 server. Other applications remain untouched.
- Configuration: Added `docker-compose.coolify.yml` to build the branch's frontend, backend, and database with persistent volumes, health checks, internal-only database/backend ports, and a loopback-only frontend on port 4000. Required secrets are supplied through Coolify. Added Docker context exclusions, included the seed archive in the database image, and made the static-only OHIF copy stage explicitly amd64 for ARM64 builds.
- Checks: Compose configuration validation passes with placeholder secrets; `git diff --check` passes. Existing production frontend build passed earlier. Full container build and live verification remain pending.
- Operations and rollback: See `09_coolify_deployment.md`. Retain data volumes for rollback/redeploy. PACS/Wezen are external integrations and are not created by this deployment.
- First attempt `qpismqh3ciqhyzrva2xcqyjq` stopped at Compose interpolation before starting containers. The initial source import created empty variable placeholders. Reapplied/verified the generated values with runtime and build-time availability, and explicitly disabled Dockerfile build-argument injection.
- Deployment `07jnpbsod2hylaeneoh5gf8y` finished successfully from `d8611f017141b64fcaa3474cf16154eb977084b5`. All three ARM64 containers report healthy. Only the frontend is published, on `127.0.0.1:4000`; database/backend have no host port bindings. Persistent database/backups/uploads mounts are present.
- Live checks: `/`, `/assets/main-settings.json`, `/assets/i18n/id.json`, and `/sirius-api/` return HTTP 200. App/calendar/editor language is `id`; contextual labels match the reviewed dictionary. An empty sign-in request returns Indonesian validation text. Seed superuser password initialization, successful Indonesian sign-in, and an authenticated `/users/find` database read passed. Login details were saved in `/home/ubuntu/.config/coolify/mhcs-ris-access.json` with mode 0600; no credential values are recorded here.
- Final checks: Generated secrets are absent from all three image metadata/history records. All previously existing applications still report healthy. Cleaned up only verified orphan processes from the earlier canceled local build.
- Limits: No rendered browser checks, native clinical review, PACS/Wezen provisioning, public domain, or scheduled backup job. Automatic Git-push deployments are disabled. Recovery instructions and resource identifiers are in the deployment guide.
