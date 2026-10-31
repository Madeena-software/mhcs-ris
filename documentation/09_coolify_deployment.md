# Local Coolify deployment

The deployment target is the `Madeena` project on local Coolify
(`http://localhost:8000`). Its source is the `feature/indonesian-language` branch, using the
Docker Compose build pack and `/docker-compose.coolify.yml`.

The configuration builds the frontend, backend, and database from repository
source. It enables Indonesian with `SIRIUS_LANGUAJE=id`, publishes the frontend
only at `http://localhost:4000`, and keeps database/backend ports internal. Named
volumes preserve MongoDB data, backup files, and backend uploads across rebuilds.
No existing project's containers or volumes are reused.

Set these required runtime variables in Coolify before deployment:

- `MONGO_INITDB_ROOT_PASSWORD`
- `AUTH_JWT_SECRET`
- `SIRIUS_BACKEND_DELETE_CODE`
- `SIRIUS_BACKEND_RABC_EXCLUDE_CODE`

Use independently generated values; do not commit them. `MONGO_INITDB_ROOT_USERNAME`
defaults to `sirius_user`. The database name stays `sirius_db`, matching the bundled
initial archive. The archive is restored only during initialization of an empty
MongoDB data volume. Retain the volume when redeploying.

The local host is ARM64. The OHIF stage explicitly reads static assets from the
upstream amd64 image; it executes no amd64 binaries. Runtime and builder images
use the host architecture. Angular build workers are limited to two.

Verification after a deployment:

1. Confirm all three containers are healthy in Coolify.
2. Check `/assets/main-settings.json` for `id` in app, calendar, and editor settings.
3. Check `/assets/i18n/id.json` and `/sirius-api/` through the frontend URL.
4. Sign in and confirm an authenticated API request succeeds.

For rollback, deploy the previous working source revision in Coolify while
retaining the named volumes. This deployment changes no schema. Stop the new
application through Coolify if initial deployment fails; do not delete data
volumes to retry. Database backups require separate scheduling; the included
backup volume alone does not establish a working backup job.

PACS/Wezen are external integrations and are not provisioned by this Compose file.
Image retrieval and modality worklist delivery require those services to be
configured separately. The repository seed is for initial setup; rotate its
bootstrap application credentials before granting access.
