# Local Coolify deployment

The deployment target is the `Madeena` project on local Coolify
(`http://localhost:8000`). Its source is the `feature/indonesian-language` branch, using the
Docker Compose build pack and `/docker-compose.coolify.yml`.

The configuration builds the frontend, backend, and database from repository
source. It enables Indonesian with `SIRIUS_LANGUAJE=id`, publishes the frontend
only at `http://localhost:4000`, and keeps database/backend ports internal. Named
volumes preserve MongoDB data, backup files, and backend uploads across rebuilds.
No existing project's containers or volumes are reused.

## Current deployment

Verified on 2026-10-31 UTC:

- Project `Madeena`: `ebdcvbqhd10zdvaied8ktjio`
- Environment `production`: `butjjziurtzvt3ti08vkirzp`
- Application `MHCS RIS Indonesia`: `1oskipsfmfp7obpchg5nlsfu`
- Server `localhost`: `agwgoid4spuvyg6gixzofnxs`
- Deployed source: `d8611f017141b64fcaa3474cf16154eb977084b5`
- Successful deployment: `07jnpbsod2hylaeneoh5gf8y`
- App URL: `http://localhost:4000`; Coolify reports `running:healthy`.

All three containers report healthy and use ARM64 runtime images. HTTP checks,
Indonesian configuration, validation messages, sign-in, and an authenticated
database read passed. The seed superuser password was replaced with a generated
password; login details are saved only in
`/home/ubuntu/.config/coolify/mhcs-ris-access.json` with mode 0600. The original
applications remained healthy. Browser-rendered flows were not checked.

Automatic deployment on Git pushes is disabled. Documentation-only commits after
the deployed revision do not trigger a rebuild.

## Configuration and operation

Set these required variables in Coolify after it parses the Compose file:

- `MONGO_INITDB_ROOT_PASSWORD`
- `AUTH_JWT_SECRET`
- `SIRIUS_BACKEND_DELETE_CODE`
- `SIRIUS_BACKEND_RABC_EXCLUDE_CODE`

Use independently generated values; do not commit them. `MONGO_INITDB_ROOT_USERNAME`
defaults to `sirius_user`. The database name stays `sirius_db`, matching the bundled
initial archive. The archive is restored only during initialization of an empty
MongoDB data volume. Retain the volume when redeploying.

Make the variables available for both build-time Compose interpolation and runtime.
Keep **Inject build arguments to Dockerfile** disabled. No Dockerfile `ARG` or
build argument consumes these values, and Coolify writes its build `.env` outside
the Docker contexts. Verify that the first Compose import has not left empty
placeholder values before starting a deployment.

The local host is ARM64. The OHIF stage explicitly reads static assets from the
upstream amd64 image; it executes no amd64 binaries. Runtime and builder images
use the host architecture. Angular build workers are limited to two.

Verification after a deployment:

1. Confirm all three containers are healthy in Coolify.
2. Check `/assets/main-settings.json` for `id` in app, calendar, and editor settings.
3. Check `/assets/i18n/id.json` and `/sirius-api/` through the frontend URL.
4. Sign in and confirm an authenticated API request succeeds.

For future rollback, deploy the previous working source revision in Coolify while
retaining the named volumes. `d8611f01` is the first verified local deployment;
there was no prior RIS deployment on this instance. This deployment changes no
schema. Stop the application through Coolify if recovery requires diagnosis;
do not delete data volumes to retry. Database backups require separate scheduling; the included
backup volume alone does not establish a working backup job.

PACS/Wezen are external integrations and are not provisioned by this Compose file.
Image retrieval and modality worklist delivery require those services to be
configured separately. The repository seed is for initial setup; bootstrap
application credentials were rotated during this deployment.
